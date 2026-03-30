"""
Feedback Generator

Generates explainable feedback for student answers using Ollama LLM.
Includes what's correct, what's missing, and contradiction detection.
"""

from typing import Dict, Any, List

from app.core.config import settings


class FeedbackGenerator:
    """
    Generates detailed, explainable feedback for evaluated answers.

    Uses Ollama LLM to produce human-readable feedback that explains:
    - What the student got right
    - What's missing or incomplete
    - Any contradictions with the reference material
    """

    def __init__(self):
        self._llm = None

    def _load_llm(self):
        """Lazy-load the Ollama LLM via LangChain."""
        if self._llm is None:
            from langchain_ollama import OllamaLLM
            self._llm = OllamaLLM(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3,
            )

    async def generate(
        self,
        answer: str,
        context: str,
        score: float,
        max_marks: float,
    ) -> Dict[str, Any]:
        """
        Generate explainable feedback for a student answer.

        Args:
            answer: Student's answer text.
            context: Reference context from knowledge base.
            score: Marks awarded.
            max_marks: Maximum marks.

        Returns:
            Dict with 'feedback' (string) and 'contradictions' (list).
        """
        self._load_llm()

        prompt = self._build_feedback_prompt(answer, context, score, max_marks)

        try:
            response = self._llm.invoke(prompt)
            return self._parse_feedback_response(response)
        except Exception as e:
            return {
                "feedback": f"Score: {score}/{max_marks}. Automated feedback unavailable.",
                "contradictions": [],
                "error": str(e),
            }

    def _build_feedback_prompt(
        self, answer: str, context: str, score: float, max_marks: float
    ) -> str:
        """Build the feedback generation prompt."""
        return f"""You are an expert academic evaluator providing detailed feedback to a student.

REFERENCE CONTEXT (correct information):
{context}

STUDENT ANSWER:
{answer}

SCORE: {score}/{max_marks}

Provide detailed, constructive feedback in the following format:

FEEDBACK:
[Write 2-4 sentences explaining what the student got right, what was missing, 
and suggestions for improvement. Be encouraging but specific.]

CONTRADICTIONS:
[List any factual contradictions between the student answer and reference context. 
Write "None" if there are no contradictions. Format each as a single line.]

Be concise, specific, and helpful."""

    def _parse_feedback_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract feedback and contradictions."""
        feedback = ""
        contradictions = []

        # Split response into sections
        parts = response.split("CONTRADICTIONS:")

        if len(parts) >= 2:
            # Extract feedback
            feedback_section = parts[0]
            if "FEEDBACK:" in feedback_section:
                feedback = feedback_section.split("FEEDBACK:", 1)[1].strip()
            else:
                feedback = feedback_section.strip()

            # Extract contradictions
            contradiction_text = parts[1].strip()
            if contradiction_text.lower() != "none":
                contradictions = [
                    line.strip().lstrip("- •")
                    for line in contradiction_text.split("\n")
                    if line.strip() and line.strip().lower() != "none"
                ]
        else:
            feedback = response.strip()

        return {
            "feedback": feedback,
            "contradictions": contradictions,
        }
