import os
import shutil
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.api.deps import get_pipeline, get_vector_store
from src.core.config import settings
from src.api.schemas import (
    DocumentClearResponse,
    DocumentIngestResponse,
    DocumentItem,
    DocumentRemoveResponse,
)
from src.core.logging import get_logger
from src.services.rag_service import RagService
from src.repositories.vector_store import VectorRepository

router = APIRouter(tags=["documents"])
logger = get_logger(__name__)

PDFS_DIR = settings.data_dir / "pdfs"


def _ensure_pdfs_dir():
    PDFS_DIR.mkdir(parents=True, exist_ok=True)


def _save_pdf(source_path: str, filename: str) -> str:
    _ensure_pdfs_dir()
    dest = PDFS_DIR / filename
    shutil.copy2(source_path, str(dest))
    logger.info("Saved PDF: %s", dest)
    return str(dest)


def _delete_pdf(filename: str):
    path = PDFS_DIR / filename
    if path.exists():
        path.unlink()
        logger.info("Deleted PDF: %s", path)


@router.post("/documents", response_model=DocumentIngestResponse)
async def ingest_from_url(
    body: dict,
    pipeline: RagService = Depends(get_pipeline),
    store: VectorRepository = Depends(get_vector_store),
):
    url = body.get("url")
    path = body.get("path")
    if not url and not path:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Provide 'url' or 'path' in JSON body")
    if url and path:
        raise HTTPException(HTTP_400_BAD_REQUEST, "Provide only one of 'url' or 'path'")

    return _ingest(pipeline, store, url=url, pdf_path_raw=path)


@router.post("/documents/upload", response_model=DocumentIngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    pipeline: RagService = Depends(get_pipeline),
    store: VectorRepository = Depends(get_vector_store),
):
    return _ingest(pipeline, store, upload_file=file)


def _ingest(pipeline, store, upload_file=None, url=None, pdf_path_raw=None):
    pdf_path = None
    filename = "unknown"
    cleanup = False

    try:
        if upload_file:
            filename = upload_file.filename or "upload.pdf"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf_path = tmp.name
            content = upload_file.file.read()
            tmp.write(content)
            tmp.close()
            cleanup = True

        elif url:
            filename = Path(url).name or "remote.pdf"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf_path = tmp.name
            with httpx.Client(timeout=60, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                tmp.write(resp.content)
            tmp.close()
            cleanup = True

        elif pdf_path_raw:
            p = Path(pdf_path_raw)
            if not p.exists():
                raise HTTPException(HTTP_404_NOT_FOUND, f"File not found: {pdf_path_raw}")
            pdf_path = str(p.resolve())
            filename = p.name

        _save_pdf(pdf_path, filename)
        chunk_count = pipeline.ingest(pdf_path, settings.chunk_size, settings.chunk_overlap, source_name=filename)
        total = store.count()

        return DocumentIngestResponse(
            filename=filename,
            chunks_created=chunk_count,
            total_chunks=total,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(exc))
    finally:
        if cleanup and pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)


@router.get("/documents/{filename:path}/pdf")
async def get_pdf(filename: str):
    pdf_path = PDFS_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(HTTP_404_NOT_FOUND, f"PDF not found: {filename}")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{filename}\""},
    )


@router.get("/documents", response_model=list[DocumentItem])
async def list_documents(store: VectorRepository = Depends(get_vector_store)):
    sources = store.list_sources()
    return [DocumentItem(filename=fn, chunks=n) for fn, n in sorted(sources.items())]


@router.delete("/documents/{filename:path}", response_model=DocumentRemoveResponse)
async def remove_document(
    filename: str,
    store: VectorRepository = Depends(get_vector_store),
):
    removed = store.delete_by_source(filename)
    if removed == 0:
        raise HTTPException(HTTP_404_NOT_FOUND, f"No chunks found for '{filename}'")
    _delete_pdf(filename)
    return DocumentRemoveResponse(filename=filename, chunks_removed=removed)


@router.delete("/documents", response_model=DocumentClearResponse)
async def clear_documents(store: VectorRepository = Depends(get_vector_store)):
    store.clear()
    if PDFS_DIR.is_dir():
        shutil.rmtree(str(PDFS_DIR))
        PDFS_DIR.mkdir(parents=True, exist_ok=True)
    return DocumentClearResponse(message="Vector store cleared")
