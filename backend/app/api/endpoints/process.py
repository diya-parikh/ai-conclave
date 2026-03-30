"""
Process Endpoint

Triggers OCR + NLP processing pipeline on an uploaded document.
Teacher only — sequential processing.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.schemas import ProcessRequest, ProcessResponse
from app.api.dependencies import require_teacher
from app.modules.ocr.service import OCRService
from app.modules.nlp.service import NLPService

router = APIRouter()


@router.post("/", response_model=ProcessResponse)
async def process_document(
    request: ProcessRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger OCR + NLP processing on an uploaded document.

    Pipeline:
    1. OCR: Image preprocessing → text extraction → question segmentation
    2. NLP: Text cleaning → tokenization → feature extraction → embeddings

    - **Teacher only**
    - Document must have status 'uploaded'
    - Processing is sequential (blocks until complete)
    """
    # Fetch document
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id,
            Document.teacher_id == teacher.id,
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.status not in ("uploaded", "failed"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is already in '{document.status}' state",
        )

    # Update status to processing
    document.status = "processing"
    await db.flush()

    try:
        # Step 1: OCR — Extract text from document
        ocr_service = OCRService()
        extracted_text = await ocr_service.process(document.file_path, document.file_type)

        # Step 2: NLP — Process extracted text
        nlp_service = NLPService()
        processed_data = await nlp_service.process(extracted_text)

        # Update document with results
        document.extracted_text = extracted_text
        document.processed_data = processed_data
        document.status = "processed"
        document.processed_at = datetime.now(timezone.utc)
        await db.flush()

        return ProcessResponse(
            document_id=document.id,
            status="processed",
            message=f"Successfully extracted {len(extracted_text)} questions",
        )

    except Exception as e:
        document.status = "failed"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}",
        )
