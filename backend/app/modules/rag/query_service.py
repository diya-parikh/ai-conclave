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
        query_text: str,
        subject: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge chunks for a query.

        Args:
            query_text: The student's answer text.
            subject: Optional subject filter.
            top_k: Number of results to return (default from config).

        Returns:
            List of dicts with 'content', 'similarity_score', and 'metadata'.
            [
                {
                    "content": "The CPU processes instructions...",
                    "similarity_score": 0.92,
                    "metadata": {"chunk_index": 3, "document_id": "..."}
                },
                ...
            ]
        """
        top_k = top_k or settings.TOP_K_RESULTS

        # Generate embedding for the query
        query_embedding = await self.embedding_generator.generate(query_text)

        # Perform similarity search
        results = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            subject=subject,
            top_k=top_k,
        )

        return results
