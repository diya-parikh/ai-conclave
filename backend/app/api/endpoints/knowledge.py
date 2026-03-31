"""
Knowledge Base Endpoint

Handles ingestion of academic content (model answers, textbooks, notes)
into the vector store for RAG retrieval.
"""

import os
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.models.knowledge import KnowledgeDocument
from app.models.schemas import KnowledgeIngestResponse
from app.api.dependencies import require_teacher
from app.modules.ingestion.service import IngestionService
from app.core.config import settings

router = APIRouter()


@router.post("/ingest", response_model=KnowledgeIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_knowledge(
    file: UploadFile = File(..., description="Academic document (PDF, DOCX, TXT)"),
    subject: str = Form(..., description="Subject name"),
    document_type: str = Form(
        "model_answer",
        description="Document type: model_answer, textbook, or notes",
    ),
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest an academic document into the knowledge base.

    Pipeline:
    1. Parse document (PDF/DOCX/TXT)
    2. Chunk content into overlapping segments
    3. Generate sentence-BERT embeddings
    4. Store chunks + embeddings in pgvector

    - **Teacher only**
    """
    # Validate document type
    valid_types = {"model_answer", "textbook", "notes"}
    if document_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document_type. Must be one of: {valid_types}",
        )

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    # Save file locally
    knowledge_dir = os.path.join(settings.UPLOAD_DIR, "knowledge")
    os.makedirs(knowledge_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(knowledge_dir, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # Run ingestion pipeline
        ingestion_service = IngestionService()
        file_type = file.content_type or "application/octet-stream"
        chunks_created = await ingestion_service.ingest(
            file_path=file_path,
            file_type=file_type,
            subject=subject,
            teacher_id=str(teacher.id),
            db=db,
        )

        # Create knowledge document record
        knowledge_doc = KnowledgeDocument(
            teacher_id=teacher.id,
            filename=file.filename,
            file_path=file_path,
            subject=subject,
            document_type=document_type,
            total_chunks=chunks_created,
        )
        db.add(knowledge_doc)
        await db.flush()

        return KnowledgeIngestResponse(
            id=knowledge_doc.id,
            filename=file.filename,
            subject=subject,
            document_type=document_type,
            chunks_created=chunks_created,
            ingested_at=knowledge_doc.ingested_at,
        )

    except Exception as e:
        # Clean up file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )
