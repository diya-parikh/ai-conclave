"""
Vector Store

Low-level operations for storing and querying vectors in PostgreSQL
with the pgvector extension.
"""

from typing import List, Dict, Any, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.database import async_session_factory


class VectorStore:
    """
    Manages vector storage and retrieval operations using pgvector.

    Handles:
    - Storing document chunks with their embeddings
    - Cosine similarity search
    - Filtering by subject
    """

    async def store_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        knowledge_document_id: str,
        db: AsyncSession,
    ) -> None:
        """
        Store document chunks with their embeddings in the vector store.

        Args:
            chunks: List of chunk dicts from DocumentChunker.
            embeddings: Corresponding embedding vectors.
            knowledge_document_id: Parent knowledge document ID.
            db: Database session.
        """
        for chunk, embedding in zip(chunks, embeddings):
            chunk_record = KnowledgeChunk(
                knowledge_document_id=knowledge_document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=embedding,
                metadata_json={
                    "start_char": chunk.get("start_char"),
                    "end_char": chunk.get("end_char"),
                },
            )
            db.add(chunk_record)

        await db.flush()

    async def similarity_search(
        self,
        query_embedding: List[float],
        subject: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform cosine similarity search against stored embeddings.

        Args:
            query_embedding: The query vector.
            subject: Optional subject filter.
            top_k: Number of results to return.

        Returns:
            List of dicts with 'content', 'similarity_score', 'metadata'.
        """
        async with async_session_factory() as session:
            # Build query with cosine distance operator
            # pgvector uses <=> for cosine distance (1 - similarity)
            query = (
                select(
                    KnowledgeChunk.content,
                    KnowledgeChunk.metadata_json,
                    KnowledgeChunk.knowledge_document_id,
                    KnowledgeChunk.chunk_index,
                    # Cosine distance => similarity = 1 - distance
                    (1 - KnowledgeChunk.embedding.cosine_distance(query_embedding)).label(
                        "similarity_score"
                    ),
                )
                .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )

            # Filter by subject if provided
            if subject:
                query = query.join(KnowledgeDocument).where(
                    KnowledgeDocument.subject == subject
                )

            result = await session.execute(query)
            rows = result.all()

            return [
                {
                    "content": row.content,
                    "similarity_score": float(row.similarity_score) if row.similarity_score else 0,
                    "metadata": {
                        "document_id": str(row.knowledge_document_id),
                        "chunk_index": row.chunk_index,
                        **(row.metadata_json or {}),
                    },
                }
                for row in rows
            ]
