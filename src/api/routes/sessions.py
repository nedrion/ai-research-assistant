from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from src.api.deps import get_session_store
from src.repositories.session_repository import SessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}")
async def get_session(session_id: str, sessions: SessionRepository = Depends(get_session_store)):
    if not sessions.session_exists(session_id):
        raise HTTPException(HTTP_404_NOT_FOUND, "Session not found")
    history = sessions.get_history(session_id)
    return {"session_id": session_id, "messages": history}
