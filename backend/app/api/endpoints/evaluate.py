"""
Evaluate Endpoint

Triggers RAG retrieval + LLM evaluation on a processed document.
Teacher only — generates marks and explainable feedback.
"""

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.evaluation import Evaluation, QuestionResult
from app.models.schemas import EvaluateRequest, EvaluationResponse, QuestionResultResponse
from app.api.dependencies import require_teacher
from app.services.pipeline_service import PipelineService

router = APIRouter()


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def evaluate_document(
    request: EvaluateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger evaluation on a processed document.

    Pipeline:
    1. RAG: Retrieve relevant knowledge chunks for each question
    2. LLM: Evaluate answers against retrieved context
    3. Score: Generate marks, feedback, and contradiction detection

    - **Teacher only**
    - Document must have status 'processed'
    - Creates evaluation and question_result records
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

    if document.status != "processed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document must be 'processed' before evaluation. Current: '{document.status}'",
        )

    # Create evaluation record
    evaluation = Evaluation(
        document_id=document.id,
        status="evaluating",
    )
    db.add(evaluation)
    await db.flush()

    try:
        # Run evaluation pipeline
        pipeline = PipelineService()
        eval_results = await pipeline.evaluate(
            extracted_text=document.extracted_text,
            processed_data=document.processed_data,
            subject=document.subject,
            max_marks_per_question=float(request.max_marks_per_question),
        )

        # Store per-question results
        total_marks = Decimal(0)
        max_marks = Decimal(0)
        question_responses = []

        for q_result in eval_results["questions"]:
            qr = QuestionResult(
                evaluation_id=evaluation.id,
                question_id=q_result["question_id"],
                extracted_answer=q_result.get("extracted_answer"),
                marks_awarded=q_result.get("marks_awarded", 0),
                max_marks=request.max_marks_per_question,
                feedback=q_result.get("feedback"),
                contradictions=q_result.get("contradictions", []),
                confidence_score=q_result.get("confidence_score"),
            )
            db.add(qr)
            total_marks += Decimal(str(q_result.get("marks_awarded", 0)))
            max_marks += Decimal(str(request.max_marks_per_question))

            question_responses.append(QuestionResultResponse(
                question_id=q_result["question_id"],
                extracted_answer=q_result.get("extracted_answer"),
                marks_awarded=q_result.get("marks_awarded"),
                max_marks=request.max_marks_per_question,
                feedback=q_result.get("feedback"),
                contradictions=q_result.get("contradictions", []),
                confidence_score=q_result.get("confidence_score"),
            ))

        # Calculate final scores
        percentage: Decimal = (total_marks / max_marks * Decimal(100)) if max_marks > 0 else Decimal(0)
        grade = _calculate_grade(float(percentage))

        # Update evaluation record
        evaluation.total_marks = total_marks
        evaluation.max_marks = max_marks
        evaluation.percentage = percentage  # Keep as Decimal for database
        evaluation.grade = grade
        evaluation.status = "completed"
        evaluation.evaluated_at = datetime.now(timezone.utc)
        await db.flush()

        return EvaluationResponse(
            id=evaluation.id,
            document_id=document.id,
            student_name=document.student_name,
            student_email=document.student_email,
            subject=document.subject,
            total_marks=total_marks,
            max_marks=max_marks,
            percentage=percentage,
            grade=grade,
            status="completed",
            evaluated_at=evaluation.evaluated_at,
            questions=question_responses,
        )

    except Exception as e:
        evaluation.status = "failed"
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


def _calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"
