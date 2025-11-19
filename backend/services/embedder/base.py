"""Le!‹ú{"""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbedder(ABC):
    """Le!‹½aú{"""

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """LeU*‡,"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[np.ndarray]:
        """yÏLe‡,"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Ïô¦"""
        pass
