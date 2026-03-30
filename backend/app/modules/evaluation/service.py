"""
Evaluation Service

Orchestrates the LLM-based evaluation pipeline:
1. Semantic similarity comparison
2. Contradiction detection
3. Context-aware LLM scoring
4. Explainable feedback generation
"""

from typing import Dict, Any, List

from app.modules.evaluation.comparator import SemanticComparator
from app.modules.evaluation.scorer import AnswerScorer
from app.modules.evaluation.feedback import FeedbackGenerator


class EvaluationService:
    """
    Orchestrates answer evaluation using RAG context and LLM.

    Takes a student answer and relevant knowledge context,
    then produces marks, feedback, and contradiction analysis.

    Usage:
        service = EvaluationService()
        result = await service.evaluate(
            answer="Student's answer",
            context=["relevant chunk 1", "relevant chunk 2"],
            max_marks=10,
        )
    """

    def __init__(self):
        self.comparator = SemanticComparator()
        self.scorer = AnswerScorer()
        self.feedback_generator = FeedbackGenerator()

    async def evaluate(
        self,
        question_id: str,
        answer: str,
        context: List[Dict[str, Any]],
        max_marks: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Evaluate a single answer against retrieved context.

        Args:
            question_id: Question identifier (e.g., "Q1").
            answer: Student's answer text.
            context: List of relevant knowledge chunks from RAG.
            max_marks: Maximum marks for this question.

        Returns:
            Dict with evaluation results:
            {
                "question_id": "Q1",
                "extracted_answer": "...",
                "marks_awarded": 8.0,
                "feedback": "Good explanation...",
                "contradictions": [],
                "confidence_score": 0.87,
            }
        """
        if not answer or not answer.strip():
            return {
                "question_id": question_id,
                "extracted_answer": answer,
                "marks_awarded": 0,
                "feedback": "No answer provided.",
                "contradictions": [],
                "confidence_score": 1.0,
            }

        # Combine context chunks for evaluation
        context_text = "\n".join([c.get("content", "") for c in context])

        # Step 1: Semantic similarity comparison
        similarity_result = await self.comparator.compare(answer, context_text)

        # Step 2: Score the answer using LLM
        score_result = await self.scorer.score(
            answer=answer,
            context=context_text,
            max_marks=max_marks,
            similarity_score=similarity_result.get("similarity_score", 0),
        )

        # Step 3: Generate explainable feedback
        feedback_result = await self.feedback_generator.generate(
            answer=answer,
            context=context_text,
            score=score_result.get("marks", 0),
            max_marks=max_marks,
        )

        return {
            "question_id": question_id,
            "extracted_answer": answer,
            "marks_awarded": score_result.get("marks", 0),
            "feedback": feedback_result.get("feedback", ""),
            "contradictions": feedback_result.get("contradictions", []),
            "confidence_score": score_result.get("confidence", 0.5),
        }
