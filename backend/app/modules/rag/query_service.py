"""
RAG Query Service

Handles the query phase of the RAG pipeline:
1. Convert student answer into embedding
2. Perform cosine similarity search in pgvector
3. Return top-K relevant knowledge chunks
"""

from typing import List, Dict, Any, Optional

from app.modules.nlp.embeddings import EmbeddingGenerator
from app.modules.rag.vector_store import VectorStore
from app.core.config import settings


class QueryService:
    """
    Retrieves relevant knowledge chunks for a student answer.

    Uses cosine similarity search against the pgvector-indexed
    academic knowledge base.
    """

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()

    async def retrieve(
        self,
        query_text: str = "",
        query_embedding: Optional[List[float]] = None,
        subject: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks for a query using cosine similarity.
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # Generate embedding only if pre-computed array is missing
        if not query_embedding:
            query_embedding = await self.embedding_generator.generate(query_text)

        # Perform similarity search natively using vector float blocks
        results = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            subject=subject,
            top_k=top_k,
        )

        return results
