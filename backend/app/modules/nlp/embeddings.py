"""
Embedding Generator

Generates sequence embeddings from text chunks using Sentence-BERT.
Specifically designed to process semantic chunks rather than full answers.
"""

from typing import List, Optional, Any

from app.core.config import settings


class EmbeddingGenerator:
    """
    Generates embeddings from semantic chunks using Sentence-BERT.

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

    async def generate(self, chunk: str) -> List[float]:
        """
        Generate embedding for a single text chunk.

        Args:
            chunk: Input text chunk.

        Returns:
            List of float values representing the embedding vector.
        """
        if not chunk:
            return [0.0] * settings.EMBEDDING_DIMENSION

        self._load_model()
        assert self._model is not None, "Model failed to load"
        embedding = self._model.encode(chunk, convert_to_numpy=True)
        return embedding.tolist()

    async def generate_batch(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple chunks in batch.

        Highly optimized for RAG since it vectorizes semantic chunks efficiently.

        Args:
            chunks: List of input chunk texts.

        Returns:
            List of embedding vectors.
        """
        if not chunks:
            return []

        self._load_model()
        assert self._model is not None, "Model failed to load"
        embeddings = self._model.encode(chunks, convert_to_numpy=True, batch_size=32)
        return [emb.tolist() for emb in embeddings]
