"""
RAG Indexing Service

Handles the indexing phase of the RAG pipeline:
1. Parse and preprocess academic documents
2. Chunk documents into overlapping segments
3. Generate embeddings for each chunk
4. Store chunks + embeddings in pgvector
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rag.chunker import DocumentChunker
from app.modules.nlp.embeddings import EmbeddingGenerator
from app.modules.rag.vector_store import VectorStore
from app.core.config import settings


class IndexingService:
    """
    Indexes academic documents into the vector store for RAG retrieval.

    Takes parsed document text, chunks it, generates embeddings,
    and stores everything in PostgreSQL with pgvector.
    """

    def __init__(self):
        self.chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()

    async def index_document(
        self,
        document_text: str,
        knowledge_document_id: str,
        db: AsyncSession,
    ) -> int:
        """
        Index a document into the vector store.

        Args:
            document_text: Full text of the academic document.
            knowledge_document_id: ID of the KnowledgeDocument record.
            db: Database session.

        Returns:
            Number of chunks created and indexed.
        """
        # Step 1: Chunk the document
        chunks = self.chunker.chunk(document_text)

        if not chunks:
            return 0

        # Step 2: Generate embeddings for all chunks
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await self.embedding_generator.generate_batch(chunk_texts)

        # Step 3: Store in vector database
        await self.vector_store.store_chunks(
            chunks=chunks,
            embeddings=embeddings,
            knowledge_document_id=knowledge_document_id,
            db=db,
        )

        return len(chunks)
