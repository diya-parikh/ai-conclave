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
        extracted_text: Any,
        processed_data: Dict[str, Any],
        subject: Optional[str] = None,
        max_marks_per_question: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Run the full evaluation pipeline natively linking the chunked matrix mappings.
        """
        question_results = []

        # Process each question sequentially based on the new RAG-optimized chunk hierarchy
        for question_id, q_data in processed_data.items():
            original_answer = q_data.get("original_answer", "")
            chunks = q_data.get("chunks", [])

            aggregated_chunks_context = {}

            # Step 1: Query the vector DB iteratively per high-density mathematical chunk
            for chunk_data in chunks:
                chunk_embed = chunk_data.get("embedding")
                chunk_text = chunk_data.get("chunk")
                
                # Natively bypass expensive textual inference since float vectors already exist 
                retrieved_context = await self.query_service.retrieve(
                    query_text=chunk_text,
                    query_embedding=chunk_embed,
                    subject=subject,
                    top_k=3 # Optimized micro-scan to maintain distinct contextual ranges
                )
                
                # Consolidate and deduplicate references across all chunks dynamically
                for r in retrieved_context:
                    rc = r.get("content")
                    if rc:
                        # Append highest similarity score for duplicate contexts
                        aggregated_chunks_context[rc] = max(
                             aggregated_chunks_context.get(rc, 0),
                             r.get("similarity_score", 0)
                        )

            # Sort context logically by similarity value taking top 5 matches
            sorted_context = sorted(aggregated_chunks_context.items(), key=lambda x: x[1], reverse=True)
            top_contexts = [{"content": item[0]} for item in sorted_context[:5]]

            # Step 2: Pipe robust contextualized arrays into the LLM scoring block
            eval_result = await self.evaluation_service.evaluate(
                question_id=question_id,
                answer=original_answer,
                context=top_contexts,
                max_marks=max_marks_per_question,
            )

            question_results.append(eval_result)

        # Step 3: Process and normalize matrix results
        final_results = self.result_service.process_results(
            question_results=question_results,
            max_marks_per_question=max_marks_per_question,
        )

        return final_results
