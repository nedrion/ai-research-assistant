from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    session_id: Optional[str] = None
    top_k: Optional[int] = None


class Source(BaseModel):
    source: str
    chunk_index: int


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    session_id: str


class DocumentIngestResponse(BaseModel):
    filename: str
    chunks_created: int
    total_chunks: int


class DocumentItem(BaseModel):
    filename: str
    chunks: int


class StatusResponse(BaseModel):
    total_chunks: int
    documents: list[DocumentItem]


class ModelItem(BaseModel):
    name: str
    current: bool


class ModelsResponse(BaseModel):
    models: list[ModelItem]
    current: str


class DocumentRemoveResponse(BaseModel):
    filename: str
    chunks_removed: int


class DocumentClearResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
