"""Text Chunking Service"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from api.config import settings


class TextChunker:
    """Text chunking class"""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        )

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks

        Args:
            text: Input text

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        chunks = self.splitter.split_text(text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]


# Global singleton instance
_chunker_instance = None


def get_chunker() -> TextChunker:
    """Get global text chunker instance"""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = TextChunker()
    return _chunker_instance
