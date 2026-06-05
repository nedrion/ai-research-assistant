import asyncio

from sentence_transformers import SentenceTransformer

from src.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def load(self):
        if self._model is not None:
            return
        logger.info("Loading embedding model '%s'...", self.model_name)
        self._model = SentenceTransformer(self.model_name)
        logger.info("Embedding model loaded (dim=%d)", self.dimension)

    async def async_load(self):
        if self._model is not None:
            return
        logger.info("Loading embedding model '%s' (async)...", self.model_name)
        loop = asyncio.get_running_loop()
        self._model = await loop.run_in_executor(
            None, lambda: SentenceTransformer(self.model_name)
        )
        logger.info("Embedding model loaded (dim=%d)", self.dimension)

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
