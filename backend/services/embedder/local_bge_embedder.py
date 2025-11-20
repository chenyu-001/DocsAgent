"""BGE-based local text embedding implementation"""
from typing import List
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from services.embedder.base import BaseEmbedder
from api.config import settings
from loguru import logger


class BGEEmbedder(BaseEmbedder):
    """BGE (BAAI General Embedding) text embedder implementation"""

    def __init__(self):
        # Configure Hugging Face mirror for China (speeds up model download)
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        logger.info(f"Loading BGE model: {settings.EMBEDDING_MODEL_NAME}")
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            device=settings.EMBEDDING_DEVICE
        )
        logger.info(f"BGE model loaded successfully. Embedding dimension: {self.dimension}")

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string into a vector representation"""
        return self.model.encode(text, convert_to_numpy=True)

    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings into vector representations"""
        embeddings = self.model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return [emb for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors"""
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedder_instance = None


def get_bge_embedder() -> BGEEmbedder:
    """Get or create the singleton BGE embedder instance"""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = BGEEmbedder()
    return _embedder_instance
