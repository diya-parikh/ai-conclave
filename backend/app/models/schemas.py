"""
Pydantic Schemas

Request/Response validation models for all API endpoints.
Separated from ORM models to maintain clean architecture.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


# ============================================================
# Auth Schemas
# ============================================================

class UserRegisterRequest(BaseModel):
    """Registration request payload."""
    name: str = Field(..., min_length=2, max_length=255, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(..., pattern="^(teacher|student)$", examples=["teacher"])


class UserLoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """User info response."""
    id: uuid.UUID
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Document Schemas
# ============================================================

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    id: uuid.UUID
    filename: str
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    subject: Optional[str] = None
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Full document details response."""
    id: uuid.UUID
    filename: str
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    subject: Optional[str] = None
    exam_name: Optional[str] = None
    file_type: str
    file_size_bytes: Optional[int] = None
    status: str
    extracted_text: Optional[dict] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# Processing Schemas
# ============================================================

class ProcessRequest(BaseModel):
    """Request to trigger OCR + NLP processing."""
    document_id: uuid.UUID


class ProcessResponse(BaseModel):
    """Response after triggering processing."""
    document_id: uuid.UUID
    status: str
    message: str


# ============================================================
# Evaluation Schemas
# ============================================================

class EvaluateRequest(BaseModel):
    """Request to trigger evaluation."""
    document_id: uuid.UUID
    max_marks_per_question: Decimal = Field(default=10, ge=1, le=100)


class QuestionResultResponse(BaseModel):
    """Per-question evaluation result."""
    question_id: str
    extracted_answer: Optional[str] = None
    marks_awarded: Optional[Decimal] = None
    max_marks: Optional[Decimal] = None
    feedback: Optional[str] = None
    contradictions: Optional[list] = None
    confidence_score: Optional[Decimal] = None

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    """Full evaluation result response."""
    id: uuid.UUID
    document_id: uuid.UUID
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    subject: Optional[str] = None
    total_marks: Optional[Decimal] = None
    max_marks: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    grade: Optional[str] = None
    status: str
    evaluated_at: Optional[datetime] = None
    questions: List[QuestionResultResponse] = []

    class Config:
        from_attributes = True


class EvaluationSummaryResponse(BaseModel):
    """Summary evaluation for list views."""
    id: uuid.UUID
    document_id: uuid.UUID
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    subject: Optional[str] = None
    total_marks: Optional[Decimal] = None
    max_marks: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    grade: Optional[str] = None
    status: str
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# Knowledge Base Schemas
# ============================================================

class KnowledgeIngestResponse(BaseModel):
    """Response after ingesting a knowledge document."""
    id: uuid.UUID
    filename: str
    subject: Optional[str] = None
    document_type: str
    chunks_created: int
    ingested_at: datetime

    class Config:
        from_attributes = True


class KnowledgeDocumentListResponse(BaseModel):
    """Knowledge document summary for list views."""
    id: uuid.UUID
    filename: str
    subject: Optional[str] = None
    document_type: str
    total_chunks: int
    ingested_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Dashboard Schemas
# ============================================================

class DashboardStatsResponse(BaseModel):
    """Aggregated dashboard statistics for teachers."""
    total_evaluations: int = 0
    total_students: int = 0
    average_score: Optional[float] = None
    subjects: List[str] = []
    grade_distribution: dict = {}
    recent_evaluations: List[EvaluationSummaryResponse] = []


# ============================================================
# Generic Response Wrapper
# ============================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    status: str = "success"
    message: Optional[str] = None
    data: Optional[dict] = None
