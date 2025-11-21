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
        self._configure_hf_endpoint()

        logger.info(f"Loading BGE model: {settings.EMBEDDING_MODEL_NAME}")
        try:
            self.model = self._load_model()
        except Exception as exc:
            if settings.HF_ENDPOINT:
                logger.warning(
                    "Failed to load model from configured HF endpoint %s, retrying default endpoint",
                    settings.HF_ENDPOINT,
                    exc_info=exc,
                )
                self._restore_original_hf_endpoint()
                self.model = self._load_model()
            else:
                raise

        logger.info(f"BGE model loaded successfully. Embedding dimension: {self.dimension}")

    def _configure_hf_endpoint(self):
        self._original_hf_endpoint = os.environ.get('HF_ENDPOINT')
        # Only set HF_ENDPOINT if it has a valid non-empty value
        if settings.HF_ENDPOINT and settings.HF_ENDPOINT.strip():
            os.environ['HF_ENDPOINT'] = settings.HF_ENDPOINT
        else:
            # Remove HF_ENDPOINT if it's empty to avoid URL construction issues
            os.environ.pop('HF_ENDPOINT', None)

    def _restore_original_hf_endpoint(self):
        if self._original_hf_endpoint is None:
            os.environ.pop('HF_ENDPOINT', None)
        else:
            os.environ['HF_ENDPOINT'] = self._original_hf_endpoint

    def _load_model(self) -> SentenceTransformer:
        return SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            device=settings.EMBEDDING_DEVICE
        )

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
