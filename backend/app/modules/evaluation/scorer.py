"""
Answer Scorer

Uses Ollama LLM to score student answers against reference context.
Combines semantic similarity with LLM-based assessment.
"""

from typing import Dict, Any, Optional

from app.core.config import settings


class AnswerScorer:
    """
    Scores student answers using a combination of:
    - Semantic similarity score (from comparator)
    - LLM-based evaluation (via Ollama)

    Uses Ollama for local LLM inference.
    """

    def __init__(self):
        self._llm: Optional[Any] = None

    def _load_llm(self) -> None:
        """Lazy-load the Ollama LLM via LangChain."""
        if self._llm is None:
            from langchain_ollama import OllamaLLM
            self._llm = OllamaLLM(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.1,  # Low temperature for consistent scoring
            )

    async def score(
        self,
        answer: str,
        context: str,
        max_marks: float,
        similarity_score: float,
    ) -> Dict[str, Any]:
        """
        Score a student answer using LLM evaluation.

        Args:
            answer: Student's answer text.
            context: Reference context from knowledge base.
            max_marks: Maximum marks for this question.
            similarity_score: Pre-computed semantic similarity.

        Returns:
            Dict with 'marks' (float) and 'confidence' (float).
        """
        self._load_llm()
        assert self._llm is not None, "LLM failed to load"

        prompt = self._build_scoring_prompt(answer, context, max_marks)

        try:
            response = await self._llm.ainvoke(prompt)
            result = self._parse_score_response(response, max_marks)
            return result
        except Exception as e:
            # Fallback: use similarity score for basic scoring
            fallback_marks = round(similarity_score * max_marks, 1)
            return {
                "marks": fallback_marks,
                "confidence": 0.3,
                "error": str(e),
            }

    def _build_scoring_prompt(self, answer: str, context: str, max_marks: float) -> str:
        """Build the scoring prompt for the LLM."""
        return f"""You are an expert academic evaluator. Score the following student answer 
based on the reference context provided.

REFERENCE CONTEXT:
{context}

STUDENT ANSWER:
{answer}

SCORING CRITERIA:
- Maximum marks: {max_marks}
- Evaluate content accuracy, completeness, and relevance
- Partial marks are allowed (e.g., 7.5 out of 10)
- Consider both factual correctness and depth of explanation

RESPOND WITH EXACTLY THIS FORMAT:
MARKS: [number]
CONFIDENCE: [number between 0 and 1]

Only output the marks and confidence, nothing else."""

    def _parse_score_response(self, response: str, max_marks: float) -> Dict[str, Any]:
        """Parse the LLM response to extract marks and confidence."""
        import re

        marks = 0.0
        confidence = 0.5

        # Extract MARKS
        marks_match = re.search(r"MARKS:\s*([\d.]+)", response, re.IGNORECASE)
        if marks_match:
            marks = min(float(marks_match.group(1)), max_marks)

        # Extract CONFIDENCE
        confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", response, re.IGNORECASE)
        if confidence_match:
            confidence = min(float(confidence_match.group(1)), 1.0)

        return {
            "marks": round(marks, 1),
            "confidence": round(confidence, 2),
        }
