import os
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src import config
from src.api.dependencies import get_pipeline, get_vector_store
from src.api.schemas import (
    DocumentClearResponse,
    DocumentIngestResponse,
    DocumentItem,
    DocumentRemoveResponse,
)
from src.qa.pipeline import RAGPipeline
from src.vector_store.store import VectorStore

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentIngestResponse)
async def ingest_from_url(
    body: dict,
    pipeline: RAGPipeline = Depends(get_pipeline),
    store: VectorStore = Depends(get_vector_store),
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
    pipeline: RAGPipeline = Depends(get_pipeline),
    store: VectorStore = Depends(get_vector_store),
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

        chunk_count = pipeline.ingest(pdf_path, config.CHUNK_SIZE, config.CHUNK_OVERLAP, source_name=filename)
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


@router.get("/documents", response_model=list[DocumentItem])
async def list_documents(store: VectorStore = Depends(get_vector_store)):
    sources = store.list_sources()
    return [DocumentItem(filename=fn, chunks=n) for fn, n in sorted(sources.items())]


@router.delete("/documents/{filename:path}", response_model=DocumentRemoveResponse)
async def remove_document(
    filename: str,
    store: VectorStore = Depends(get_vector_store),
):
    removed = store.delete_by_source(filename)
    if removed == 0:
        raise HTTPException(HTTP_404_NOT_FOUND, f"No chunks found for '{filename}'")
    return DocumentRemoveResponse(filename=filename, chunks_removed=removed)


@router.delete("/documents", response_model=DocumentClearResponse)
async def clear_documents(store: VectorStore = Depends(get_vector_store)):
    store.clear()
    return DocumentClearResponse(message="Vector store cleared")
