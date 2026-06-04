from pydantic import BaseModel


class Document(BaseModel):
    filename: str
    chunks: int


class DocumentIngestResult(BaseModel):
    filename: str
    chunks_created: int
    total_chunks: int


class DocumentRemoveResult(BaseModel):
    filename: str
    chunks_removed: int
