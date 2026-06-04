from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class SourceRef(BaseModel):
    source: str
    chunk_index: int


class QueryResult(BaseModel):
    answer: str
    sources: list[SourceRef]
    session_id: str | None = None
