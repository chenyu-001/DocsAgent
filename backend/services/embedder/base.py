"""Base class for text embedding models"""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbedder(ABC):
    """Abstract base class for text embedding implementations"""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string into a vector representation"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Embed a batch of text strings into vector representations"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors"""
        pass
