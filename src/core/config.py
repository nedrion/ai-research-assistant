from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path(__file__).resolve().parent.parent.parent / "data"

    embedding_model: str = Field("all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(50, alias="CHUNK_OVERLAP")
    collection_name: str = Field("documents", alias="COLLECTION_NAME")
    top_k: int = Field(5, alias="TOP_K")
    ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")
    llm_model: str = Field("llama3.2", alias="LLM_MODEL")
    api_host: str = Field("127.0.0.1", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")

    @property
    def chroma_dir(self) -> str:
        return str(self.data_dir / "chroma")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
    }


settings = Settings()
