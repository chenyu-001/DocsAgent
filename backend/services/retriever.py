"""Document Retrieval Service"""
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from services.embedder import get_embedder
from api.config import settings
from loguru import logger


class DocumentRetriever:
    """Document retrieval class"""

    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.QDRANT_COLLECTION
        self.embedder = get_embedder()
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure collection exists"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedder.dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def add_chunks(self, chunks: List[Dict]):
        """Add text chunks and generate embeddings"""
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)

        points = [
            PointStruct(
                id=chunk["chunk_id"],  # Use integer chunk_id as Qdrant point ID
                vector=emb.tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "text": chunk["text"],
                    "vector_id": chunk["vector_id"],  # Keep vector_id in payload for reference
                }
            )
            for chunk, emb in zip(chunks, embeddings)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Added {len(chunks)} text chunks to vector database")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search for documents"""
        query_vector = self.embedder.embed_text(query)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
        )

        return [
            {
                "chunk_id": hit.payload["chunk_id"],
                "document_id": hit.payload["document_id"],
                "text": hit.payload["text"],
                "score": hit.score,
            }
            for hit in results
        ]


# Global singleton instance
_retriever_instance = None


def get_retriever() -> DocumentRetriever:
    """Get global retriever instance"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = DocumentRetriever()
    return _retriever_instance
