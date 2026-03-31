"""
Embedding Generator

Generates sentence embeddings using Sentence-BERT (sentence-transformers).
Uses the model specified in configuration.
"""

from typing import List, Optional, Any

from app.core.config import settings


class EmbeddingGenerator:
    """
    Generates sentence embeddings using Sentence-BERT.

    Lazy-loads the model on first use. Uses the model specified
    in settings.EMBEDDING_MODEL (default: all-MiniLM-L6-v2).
    """

    _instance = None  # Singleton pattern for model reuse

    def __init__(self):
        self._model: Optional[Any] = None

    def _load_model(self) -> None:
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)

    async def generate(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text string.

        Returns:
            List of float values representing the embedding vector.
        """
        if not text:
            return [0.0] * settings.EMBEDDING_DIMENSION

        self._load_model()
        assert self._model is not None, "Model failed to load"
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        More efficient than generating one at a time.

        Args:
            texts: List of input text strings.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        self._load_model()
        assert self._model is not None, "Model failed to load"
        embeddings = self._model.encode(texts, convert_to_numpy=True, batch_size=32)
        return [emb.tolist() for emb in embeddings]
