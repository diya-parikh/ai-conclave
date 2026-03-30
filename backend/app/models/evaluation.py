"""
Evaluation Models

Stores evaluation results at both the document level and per-question level.
Includes marks, feedback, contradictions, and confidence scores.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Evaluation(Base):
    """
    Document-level evaluation result.

    Aggregates per-question results into totals, percentage, and grade.

    Attributes:
        id: Unique identifier.
        document_id: Reference to the evaluated document.
        total_marks: Sum of marks awarded.
        max_marks: Maximum possible marks.
        percentage: Score percentage.
        grade: Letter grade (A+, A, B+, B, C, D, F).
        status: Evaluation status (pending → evaluating → completed → failed).
    """

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    total_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    grade: Mapped[str] = mapped_column(String(10), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    document = relationship("Document", back_populates="evaluations", lazy="selectin")
    question_results = relationship(
        "QuestionResult", back_populates="evaluation", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Evaluation(id={self.id}, total={self.total_marks}/{self.max_marks}, grade='{self.grade}')>"


class QuestionResult(Base):
    """
    Per-question evaluation detail.

    Contains the extracted answer, marks, feedback, and confidence
    for a single question within an evaluation.

    Attributes:
        id: Unique identifier.
        evaluation_id: Parent evaluation.
        question_id: Question label (e.g., 'Q1', 'Q2').
        extracted_answer: The text extracted from the answer sheet.
        marks_awarded: Marks given for this question.
        max_marks: Maximum marks for this question.
        feedback: Explainable feedback text.
        contradictions: JSON array of detected contradictions.
        confidence_score: Model confidence (0.0 to 1.0).
    """

    __tablename__ = "question_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[str] = mapped_column(String(50), nullable=False)
    extracted_answer: Mapped[str] = mapped_column(Text, nullable=True)
    marks_awarded: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    contradictions: Mapped[dict] = mapped_column(JSONB, nullable=True, default=list)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    evaluation = relationship("Evaluation", back_populates="question_results")

    def __repr__(self) -> str:
        return f"<QuestionResult(q='{self.question_id}', marks={self.marks_awarded}/{self.max_marks})>"
