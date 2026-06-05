from functools import lru_cache

from src.core.config import settings
from src.services.embedding_service import EmbeddingService
from src.services.llm_service import LlmService
from src.services.rag_service import RagService
from src.repositories.vector_store import VectorRepository
from src.repositories.session_repository import SessionRepository


@lru_cache
def get_embedder() -> EmbeddingService:
    return EmbeddingService(settings.embedding_model)


@lru_cache
def get_vector_store() -> VectorRepository:
    return VectorRepository(settings.chroma_dir, settings.collection_name)


@lru_cache
def get_llm_client() -> LlmService:
    return LlmService(settings.ollama_base_url, settings.llm_model)


@lru_cache
def get_pipeline() -> RagService:
    return RagService(
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
        top_k=settings.top_k,
    )


@lru_cache
def get_session_store() -> SessionRepository:
    return SessionRepository()
