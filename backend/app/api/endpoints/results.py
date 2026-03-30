"""
Results Endpoints

Provides evaluation results with role-based access:
- Teachers: view all results and student lists
- Students: view only their own results
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.evaluation import Evaluation, QuestionResult
from app.models.schemas import (
    EvaluationResponse,
    EvaluationSummaryResponse,
    QuestionResultResponse,
    DashboardStatsResponse,
)
from app.api.dependencies import get_current_user, require_teacher

router = APIRouter()


@router.get("/", response_model=List[EvaluationSummaryResponse])
async def list_evaluations(
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    List all evaluations (teacher only).

    Returns a summary list of all student evaluations
    with scores and grades — for the teacher dashboard.
    """
    result = await db.execute(
        select(Evaluation)
        .join(Document)
        .where(Document.teacher_id == teacher.id)
        .order_by(Evaluation.created_at.desc())
    )
    evaluations = result.scalars().all()

    summaries = []
    for ev in evaluations:
        doc = ev.document
        summaries.append(EvaluationSummaryResponse(
            id=ev.id,
            document_id=ev.document_id,
            student_name=doc.student_name if doc else None,
            student_email=doc.student_email if doc else None,
            subject=doc.subject if doc else None,
            total_marks=ev.total_marks,
            max_marks=ev.max_marks,
            percentage=ev.percentage,
            grade=ev.grade,
            status=ev.status,
            evaluated_at=ev.evaluated_at,
        ))

    return summaries


@router.get("/my-results", response_model=List[EvaluationSummaryResponse])
async def get_my_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get results for the currently logged-in student.

    Matches evaluations by student_email on the document.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for students only",
        )

    result = await db.execute(
        select(Evaluation)
        .join(Document)
        .where(Document.student_email == current_user.email)
        .order_by(Evaluation.created_at.desc())
    )
    evaluations = result.scalars().all()

    summaries = []
    for ev in evaluations:
        doc = ev.document
        summaries.append(EvaluationSummaryResponse(
            id=ev.id,
            document_id=ev.document_id,
            student_name=doc.student_name if doc else None,
            student_email=doc.student_email if doc else None,
            subject=doc.subject if doc else None,
            total_marks=ev.total_marks,
            max_marks=ev.max_marks,
            percentage=ev.percentage,
            grade=ev.grade,
            status=ev.status,
            evaluated_at=ev.evaluated_at,
        ))

    return summaries


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated dashboard statistics (teacher only).

    Includes total evaluations, average scores, grade distribution, etc.
    """
    # Total evaluations
    total_result = await db.execute(
        select(func.count(Evaluation.id))
        .join(Document)
        .where(Document.teacher_id == teacher.id, Evaluation.status == "completed")
    )
    total_evaluations = total_result.scalar() or 0

    # Unique students
    students_result = await db.execute(
        select(func.count(distinct(Document.student_email)))
        .join(Evaluation)
        .where(Document.teacher_id == teacher.id)
    )
    total_students = students_result.scalar() or 0

    # Average score
    avg_result = await db.execute(
        select(func.avg(Evaluation.percentage))
        .join(Document)
        .where(Document.teacher_id == teacher.id, Evaluation.status == "completed")
    )
    average_score = float(avg_result.scalar() or 0)

    # Subjects
    subjects_result = await db.execute(
        select(distinct(Document.subject))
        .join(Evaluation)
        .where(Document.teacher_id == teacher.id, Document.subject.isnot(None))
    )
    subjects = [s for s in subjects_result.scalars().all() if s]

    # Grade distribution
    grade_result = await db.execute(
        select(Evaluation.grade, func.count(Evaluation.id))
        .join(Document)
        .where(Document.teacher_id == teacher.id, Evaluation.status == "completed")
        .group_by(Evaluation.grade)
    )
    grade_distribution = {row[0]: row[1] for row in grade_result.all() if row[0]}

    # Recent evaluations
    recent_result = await db.execute(
        select(Evaluation)
        .join(Document)
        .where(Document.teacher_id == teacher.id)
        .order_by(Evaluation.created_at.desc())
        .limit(10)
    )
    recent_evaluations = []
    for ev in recent_result.scalars().all():
        doc = ev.document
        recent_evaluations.append(EvaluationSummaryResponse(
            id=ev.id,
            document_id=ev.document_id,
            student_name=doc.student_name if doc else None,
            student_email=doc.student_email if doc else None,
            subject=doc.subject if doc else None,
            total_marks=ev.total_marks,
            max_marks=ev.max_marks,
            percentage=ev.percentage,
            grade=ev.grade,
            status=ev.status,
            evaluated_at=ev.evaluated_at,
        ))

    return DashboardStatsResponse(
        total_evaluations=total_evaluations,
        total_students=total_students,
        average_score=average_score,
        subjects=subjects,
        grade_distribution=grade_distribution,
        recent_evaluations=recent_evaluations,
    )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation_detail(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed evaluation results.

    - Teachers can view any evaluation they created
    - Students can only view their own results (matched by email)
    """
    result = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.question_results))
        .where(Evaluation.id == evaluation_id)
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        )

    # Access control
    doc = evaluation.document
    if current_user.role == "teacher":
        if doc.teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif current_user.role == "student":
        if doc.student_email != current_user.email:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Build response
    question_responses = [
        QuestionResultResponse.model_validate(qr) for qr in evaluation.question_results
    ]

    return EvaluationResponse(
        id=evaluation.id,
        document_id=evaluation.document_id,
        student_name=doc.student_name,
        student_email=doc.student_email,
        subject=doc.subject,
        total_marks=evaluation.total_marks,
        max_marks=evaluation.max_marks,
        percentage=evaluation.percentage,
        grade=evaluation.grade,
        status=evaluation.status,
        evaluated_at=evaluation.evaluated_at,
        questions=question_responses,
    )
