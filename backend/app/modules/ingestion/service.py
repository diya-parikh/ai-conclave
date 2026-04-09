"""
Ingestion Service

Orchestrates the document ingestion pipeline for the knowledge base:
1. Parse document (PDF, DOCX, TXT)
2. Preprocess content
3. Chunk and embed via RAG indexing service
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.parser import DocumentParser
from app.modules.ingestion.preprocessor import ContentPreprocessor
from app.modules.rag.indexing_service import IndexingService


class IngestionService:
    """
    Handles the full ingestion pipeline for academic documents.

    Takes a file, extracts text, preprocesses it, then passes
    it to the RAG indexing service for chunking + embedding.
    """

    def __init__(self):
        self.parser = DocumentParser()
        self.preprocessor = ContentPreprocessor()
        self.indexing_service = IndexingService()

    async def ingest(
        self,
        file_path: str,
        file_type: str,
        subject: str,
        knowledge_document_id: str,
        db: AsyncSession,
    ) -> int:
        """
        Ingest a document into the knowledge base.

        Args:
            file_path: Path to the uploaded file.
            file_type: MIME type of the file.
            subject: Academic subject.
            knowledge_document_id: ID of the parent KnowledgeDocument record.
            db: Database session.

        Returns:
            Number of chunks created.
        """
        # Step 1: Parse document to extract text
        raw_text = await self.parser.parse(file_path, file_type)

        if not raw_text or not raw_text.strip():
            return 0

        # Step 2: Preprocess content
        cleaned_text = self.preprocessor.preprocess(raw_text)

        # Step 3: Index into vector store
        chunks_created = await self.indexing_service.index_document(
            document_text=cleaned_text,
            knowledge_document_id=knowledge_document_id,
            db=db,
        )

        return chunks_created
