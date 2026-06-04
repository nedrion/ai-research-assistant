from fastapi import APIRouter, Depends

from src import config
from src.api.dependencies import get_llm_client, get_vector_store
from src.api.schemas import DocumentItem, ModelItem, ModelsResponse, StatusResponse
from src.qa.llm_client import OllamaClient
from src.vector_store.store import VectorStore

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def status(store: VectorStore = Depends(get_vector_store)):
    total = store.count()
    sources = store.list_sources()
    docs = [DocumentItem(filename=fn, chunks=n) for fn, n in sorted(sources.items())]
    return StatusResponse(total_chunks=total, documents=docs)


@router.get("/models", response_model=ModelsResponse)
async def models(llm: OllamaClient = Depends(get_llm_client)):
    available = llm.list_models()
    items = [
        ModelItem(name=m, current=(m == config.LLM_MODEL or m.split(":")[0] == config.LLM_MODEL.split(":")[0]))
        for m in available
    ]
    return ModelsResponse(models=items, current=config.LLM_MODEL)
