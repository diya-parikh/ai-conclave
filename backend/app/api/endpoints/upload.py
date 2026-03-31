"""
Upload Endpoint

Handles file upload for answer sheets (teacher only).
Validates file type and size, stores locally, creates document record.
"""

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.schemas import DocumentUploadResponse
from app.api.dependencies import require_teacher
from app.core.config import settings

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
}


@router.post("/", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_answer_sheet(
    file: UploadFile = File(..., description="Answer sheet image or PDF"),
    student_name: str = Form(..., description="Student name"),
    student_email: str = Form(..., description="Student email"),
    subject: str = Form(..., description="Subject name"),
    exam_name: str = Form(None, description="Exam name (optional)"),
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an answer sheet file.

    - **Teacher only**
    - Accepts PDF, PNG, JPG, TIFF files
    - Validates file size (max from config)
    - Stores file locally in uploads directory
    - Creates a document record in database
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a content type",
        )

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, PNG, JPG, TIFF.",
        )

    # Read file content
    content = await file.read()

    # Validate file size (convert MB to bytes)
    max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Generate unique filename and save
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    document = Document(
        teacher_id=teacher.id,
        student_name=student_name,
        student_email=student_email,
        subject=subject,
        exam_name=exam_name,
        filename=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size_bytes=len(content),
        status="uploaded",
    )
    db.add(document)
    await db.flush()

    return DocumentUploadResponse.model_validate(document)
