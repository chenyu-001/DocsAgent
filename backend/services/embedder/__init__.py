"""Embedder Module"""
from services.embedder.base import BaseEmbedder
from services.embedder.local_bge_embedder import BGEEmbedder
from api.config import settings


def get_embedder() -> BaseEmbedder:
    """Get configured embedder instance"""
    if settings.EMBEDDING_MODEL_TYPE == "bge":
        return BGEEmbedder()
    else:
        raise ValueError(f"Unsupported embedding model type: {settings.EMBEDDING_MODEL_TYPE}")
