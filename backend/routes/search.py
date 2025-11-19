"""‡cÀ"ï1"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import get_current_active_user
from models.user_models import User
from services.retriever import get_retriever
from loguru import logger

router = APIRouter()


class SearchRequest(BaseModel):
    """"÷B!‹"""
    query: str
    top_k: int = 5


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    À"øs‡c

    Args:
        request: "÷B+åâŒÔÞpÏ	
        current_user: SM(7

    Returns:
        À"Óœh
    """
    logger.info(f"(7 {current_user.username} ": {request.query}")

    retriever = get_retriever()
    results = retriever.search(request.query, top_k=request.top_k)

    return {
        "query": request.query,
        "results": results,
        "count": len(results),
    }
