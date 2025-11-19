"""Le!‹!W"""
from services.embedder.base import BaseEmbedder
from services.embedder.local_bge_embedder import BGEEmbedder
from api.config import settings


def get_embedder() -> BaseEmbedder:
    """·ÖLe!‹ž‹"""
    if settings.EMBEDDING_MODEL_TYPE == "bge":
        return BGEEmbedder()
    else:
        raise ValueError(f"/„Le!‹{‹: {settings.EMBEDDING_MODEL_TYPE}")
