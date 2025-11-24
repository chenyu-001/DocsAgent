"""Question answering route."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_active_user
from models.user_models import User
from services.qa_service import get_qa_service
from loguru import logger

router = APIRouter()


class QARequest(BaseModel):
    """QA request body."""

    question: str
    top_k: int = 5


@router.post("/qa")
async def ask_question(request: QARequest, current_user: User = Depends(get_current_active_user)):
    """Answer a user question using retrieved document context."""
    logger.info(f"User {current_user.username} asking: {request.question}")

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        qa_service = get_qa_service()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    result = qa_service.answer_question(request.question, top_k=request.top_k)

    return result
