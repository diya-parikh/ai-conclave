"""
Pipeline Service

End-to-end pipeline orchestrator that chains together:
RAG Query → Evaluation Engine → Result Processing

This is invoked after OCR + NLP processing is complete.
"""

from typing import Dict, Any, List, Optional

from app.modules.rag.query_service import QueryService
from app.modules.evaluation.service import EvaluationService
from app.services.result_service import ResultService


class PipelineService:
    """
    Orchestrates the evaluation pipeline for a processed document.

    Takes extracted and NLP-processed text, retrieves relevant
    knowledge via RAG, evaluates each answer, and produces results.
    """

    def __init__(self):
        self.query_service = QueryService()
        self.evaluation_service = EvaluationService()
        self.result_service = ResultService()

    async def evaluate(
        self,
        extracted_text: Dict[str, str],
        processed_data: Dict[str, Any],
        subject: Optional[str] = None,
        max_marks_per_question: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Run the full evaluation pipeline on processed text.

        Args:
            extracted_text: Dict of question IDs to answer text.
            processed_data: Dict of NLP-processed data per question.
            subject: Subject for RAG filtering.
            max_marks_per_question: Max marks per question.

        Returns:
            Dict with 'questions' list containing per-question results.
        """
        question_results = []

        # Process each question sequentially
        for question_id, answer_text in extracted_text.items():
            # Step 1: Retrieve relevant context via RAG
            context = await self.query_service.retrieve(
                query_text=answer_text,
                subject=subject,
            )

            # Step 2: Evaluate answer against context
            eval_result = await self.evaluation_service.evaluate(
                question_id=question_id,
                answer=answer_text,
                context=context,
                max_marks=max_marks_per_question,
            )

            question_results.append(eval_result)

        # Step 3: Process and normalize results
        final_results = self.result_service.process_results(
            question_results=question_results,
            max_marks_per_question=max_marks_per_question,
        )

        return final_results
