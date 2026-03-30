"""
Result Service

Processes and normalizes evaluation results:
- Normalize marks
- Aggregate totals
- Calculate grades
"""

from typing import Dict, Any, List


class ResultService:
    """
    Processes raw evaluation results into final structured output.

    Handles mark normalization, total aggregation, and grade calculation.
    """

    def process_results(
        self,
        question_results: List[Dict[str, Any]],
        max_marks_per_question: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Process and format evaluation results.

        Args:
            question_results: List of per-question evaluation results.
            max_marks_per_question: Max marks per question.

        Returns:
            Dict with normalized and aggregated results.
        """
        processed_questions = []
        total_marks = 0
        max_marks = 0

        for result in question_results:
            # Normalize marks (ensure within bounds)
            marks = min(
                float(result.get("marks_awarded", 0)),
                max_marks_per_question,
            )
            marks = max(0, marks)

            processed = {
                "question_id": result.get("question_id"),
                "extracted_answer": result.get("extracted_answer"),
                "marks_awarded": round(marks, 1),
                "max_marks": max_marks_per_question,
                "feedback": result.get("feedback", ""),
                "contradictions": result.get("contradictions", []),
                "confidence_score": result.get("confidence_score", 0.5),
            }

            processed_questions.append(processed)
            total_marks += marks
            max_marks += max_marks_per_question

        return {
            "questions": processed_questions,
            "total_marks": round(total_marks, 1),
            "max_marks": round(max_marks, 1),
            "percentage": round(total_marks / max_marks * 100, 1) if max_marks > 0 else 0,
        }
