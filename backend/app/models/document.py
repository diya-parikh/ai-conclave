"""
Document Model

Represents uploaded answer sheet files with their processing status
and extracted text data.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Document(Base):
    """
    Uploaded document model.

    Tracks the lifecycle of an uploaded answer sheet from upload
    through OCR processing to evaluation.

    Attributes:
        id: Unique identifier (UUID).
        teacher_id: ID of the teacher who uploaded it.
        student_name: Name of the student whose paper this is.
        student_email: Email of the student (for linking to student account).
        subject: Academic subject.
        filename: Original filename.
        file_path: Server-side storage path.
        file_type: MIME type (e.g., 'application/pdf').
        file_size_bytes: File size in bytes.
        status: Processing status (uploaded → processing → processed → failed).
        extracted_text: JSON of question-wise extracted text.
        processed_data: JSON of NLP-processed features and metadata.
        uploaded_at: Upload timestamp.
        processed_at: Processing completion timestamp.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(255), nullable=True)
    student_email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=True)
    exam_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # File metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)

    # Processing state
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="uploaded", index=True
    )

    # Extracted & processed data (stored as JSONB)
    extracted_text: Mapped[dict] = mapped_column(JSONB, nullable=True)
    processed_data: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    teacher = relationship("User", back_populates="documents", lazy="selectin")
    evaluations = relationship("Evaluation", back_populates="document", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
