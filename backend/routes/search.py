"""Document Search Route"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import get_current_active_user
from models.user_models import User
from services.retriever import get_retriever
from loguru import logger

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    top_k: int = 5


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Semantic search in documents

    Args:
        request: Search request containing query and top_k parameter
        current_user: Current authenticated user

    Returns:
        Search results
    """
    logger.info(f"User {current_user.username} searching: {request.query}")

    retriever = get_retriever()
    results = retriever.search(request.query, top_k=request.top_k)

    return {
        "query": request.query,
        "results": results,
        "count": len(results),
    }
