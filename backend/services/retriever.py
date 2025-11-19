"""‡cÀ"¡"""
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from services.embedder import get_embedder
from api.config import settings
from loguru import logger


class DocumentRetriever:
    """‡cÀ"h"""

    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.QDRANT_COLLECTION
        self.embedder = get_embedder()
        self._ensure_collection()

    def _ensure_collection(self):
        """nÝÆX("""
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
            logger.info(f" ú Qdrant Æ: {self.collection_name}")

    def add_chunks(self, chunks: List[Dict]):
        """û ‡,W0Ï“"""
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)

        points = [
            PointStruct(
                id=chunk["vector_id"],
                vector=emb.tolist(),
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "text": chunk["text"],
                }
            )
            for chunk, emb in zip(chunks, embeddings)
        ]

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f" û  {len(chunks)} *‡,W0Ï“")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """À"øs‡c"""
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
