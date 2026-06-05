import uuid

from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from src.api.deps import get_pipeline, get_llm_client, get_session_store
from src.api.schemas import QueryRequest, QueryResponse, Source
from src.core.config import settings
from src.core.logging import get_logger
from src.services.llm_service import LlmService
from src.services.rag_service import RagService
from src.repositories.session_repository import SessionRepository

router = APIRouter(tags=["query"])
logger = get_logger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    pipeline: RagService = Depends(get_pipeline),
    llm: LlmService = Depends(get_llm_client),
    sessions: SessionRepository = Depends(get_session_store),
):
    model = body.model or settings.llm_model

    if not llm.is_server_running():
        raise HTTPException(HTTP_400_BAD_REQUEST, "Ollama is not running")
    if model not in llm.list_models():
        raise HTTPException(HTTP_400_BAD_REQUEST, f"Model '{model}' not found in Ollama. Run: ollama pull {model}")

    session_id = body.session_id or str(uuid.uuid4())
    top_k = body.top_k or settings.top_k

    history = sessions.get_history(session_id)

    query_embedding = pipeline.embedder.embed([body.question])[0]
    results = pipeline.vector_store.search(query_embedding, top_k)

    if not results:
        sessions.add_message(session_id, "user", body.question)
        sessions.add_message(session_id, "assistant", "No relevant documents found.")
        return QueryResponse(
            answer="No relevant documents found.",
            sources=[],
            session_id=session_id,
        )

    context = "\n\n".join(
        f"[Source: {r['metadata']['source']}, Chunk {r['metadata']['chunk_index']}]\n{r['document']}"
        for r in results
    )

    history_block = ""
    if history:
        lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")
        history_block = "\n\n" + "\n".join(lines)

    system_prompt = (
        "You are a precise research assistant. Answer the question based solely on the provided context. "
        "If the context doesn't contain enough information, say so. "
        "Always reference the source documents in your answer."
    )

    user_prompt = (
        f"Context:\n{context}"
        f"{history_block}"
        f"\n\nQuestion: {body.question}\n\nAnswer:"
    )

    try:
        answer = llm.generate(user_prompt, system=system_prompt, model=model)
    except RuntimeError as exc:
        raise HTTPException(HTTP_400_BAD_REQUEST, str(exc))

    sessions.add_message(session_id, "user", body.question)
    sessions.add_message(session_id, "assistant", answer)

    sources = [
        Source(source=r["metadata"]["source"], chunk_index=r["metadata"]["chunk_index"], page=r["metadata"].get("page"))
        for r in results
    ]

    logger.info("Query answered (session=%s, sources=%d)", session_id, len(sources))
    return QueryResponse(answer=answer, sources=sources, session_id=session_id)
