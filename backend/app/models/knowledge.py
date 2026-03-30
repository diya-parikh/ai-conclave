"""
Knowledge Base Models

Stores ingested academic documents and their vector-embedded chunks
for RAG retrieval.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.config import settings
from app.models.database import Base


class KnowledgeDocument(Base):
    """
    Ingested academic document metadata.

    Represents a model answer, textbook, or notes document that has been
    ingested into the knowledge base for RAG retrieval.

    Attributes:
        id: Unique identifier.
        teacher_id: Teacher who uploaded this knowledge document.
        filename: Original filename.
        subject: Academic subject.
        document_type: Type (model_answer, textbook, notes).
        total_chunks: Number of chunks generated.
        ingested_at: Ingestion timestamp.
    """

    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="model_answer"
    )
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="knowledge_document", lazy="selectin")

    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, subject='{self.subject}', chunks={self.total_chunks})>"


class KnowledgeChunk(Base):
    """
    Vector-embedded chunk from an academic document.

    Each chunk stores the text content and its sentence-BERT embedding
    for similarity search during RAG retrieval.

    Attributes:
        id: Unique identifier.
        knowledge_document_id: Parent document.
        chunk_index: Sequential index within the document.
        content: Text content of the chunk.
        embedding: Sentence-BERT vector embedding.
        metadata: Additional metadata (page, section, etc.).
    """

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    knowledge_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    knowledge_document = relationship("KnowledgeDocument", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<KnowledgeChunk(doc={self.knowledge_document_id}, index={self.chunk_index})>"
