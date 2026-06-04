from functools import lru_cache

from src import config
from src.embeddings.embedder import Embedder
from src.qa.llm_client import OllamaClient
from src.qa.pipeline import RAGPipeline
from src.vector_store.store import VectorStore


@lru_cache
def get_embedder() -> Embedder:
    return Embedder(config.EMBEDDING_MODEL)


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore(config.CHROMA_DIR, config.COLLECTION_NAME)


@lru_cache
def get_llm_client() -> OllamaClient:
    return OllamaClient(config.OLLAMA_BASE_URL, config.LLM_MODEL)


@lru_cache
def get_pipeline() -> RAGPipeline:
    return RAGPipeline(
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
        top_k=config.TOP_K,
    )
