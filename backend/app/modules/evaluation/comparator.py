"""
Semantic Comparator

Compares student answers against reference context using
semantic similarity measures.
"""

from typing import Dict, Any, List

from app.modules.nlp.embeddings import EmbeddingGenerator


class SemanticComparator:
    """
    Compares student answers with reference context using
    semantic similarity (cosine similarity on embeddings).
    """

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()

    async def compare(self, answer: str, context: str) -> Dict[str, Any]:
        """
        Compute semantic similarity between answer and context.

        Args:
            answer: Student's answer text.
            context: Reference context from knowledge base.

        Returns:
            Dict with similarity_score (0.0 to 1.0).
        """
        if not answer or not context:
            return {"similarity_score": 0.0}

        # Generate embeddings
        answer_embedding = await self.embedding_generator.generate(answer)
        context_embedding = await self.embedding_generator.generate(context)

        # Compute cosine similarity
        similarity = self._cosine_similarity(answer_embedding, context_embedding)

        return {"similarity_score": max(0.0, min(1.0, similarity))}

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec_a: First vector.
            vec_b: Second vector.

        Returns:
            Cosine similarity score (0 to 1).
        """
        import math

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
