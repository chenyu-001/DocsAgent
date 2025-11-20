"""BGE ,0Le!‹"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from services.embedder.base import BaseEmbedder
from api.config import settings
from loguru import logger


class BGEEmbedder(BaseEmbedder):
    """BGE Le!‹"""

    def __init__(self):
        logger.info(f" } BGE !‹: {settings.EMBEDDING_MODEL_NAME}")
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            device=settings.EMBEDDING_DEVICE
        )
        logger.info(f" BGE !‹ }Œô¦: {self.dimension}")

    def embed_text(self, text: str) -> np.ndarray:
        """LeU*‡,"""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """yÏLe‡,"""
        embeddings = self.model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return [emb for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Ïô¦"""
        return self.model.get_sentence_embedding_dimension()


# h@U‹
_embedder_instance = None


def get_bge_embedder() -> BGEEmbedder:
    """·Ö BGE Lehž‹U‹	"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = BGEEmbedder()
    return _embedder_instance
