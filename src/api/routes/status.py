from fastapi import APIRouter, Depends

from src.api.deps import get_llm_client, get_vector_store
from src.api.schemas import DocumentItem, ModelItem, ModelsResponse, StatusResponse
from src.core.config import settings
from src.services.llm_service import LlmService
from src.repositories.vector_store import VectorRepository

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def status(store: VectorRepository = Depends(get_vector_store)):
    total = store.count()
    sources = store.list_sources()
    docs = [DocumentItem(filename=fn, chunks=n) for fn, n in sorted(sources.items())]
    return StatusResponse(total_chunks=total, documents=docs)


@router.get("/models", response_model=ModelsResponse)
async def models(llm: LlmService = Depends(get_llm_client)):
    available = llm.list_models()
    items = [
        ModelItem(name=m, current=(m == settings.llm_model or m.split(":")[0] == settings.llm_model.split(":")[0]))
        for m in available
    ]
    return ModelsResponse(models=items, current=settings.llm_model)
