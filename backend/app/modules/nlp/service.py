"""
NLP Service

Orchestrates the complete NLP processing pipeline:
1. Text cleaning and normalization
2. Tokenization (NLTK / spaCy)
3. Feature extraction (POS, NER)
4. Sentence embedding generation (Sentence-BERT)
"""

from typing import Dict, Any

from app.modules.nlp.cleaner import TextCleaner
from app.modules.nlp.tokenizer import TextTokenizer
from app.modules.nlp.features import FeatureExtractor
from app.modules.nlp.embeddings import EmbeddingGenerator


class NLPService:
    """
    Orchestrates the NLP processing pipeline for student answers.

    Takes structured question-answer text from OCR and produces
    cleaned text, linguistic features, and embeddings.

    Usage:
        service = NLPService()
        result = await service.process({"Q1": "answer text", ...})
    """

    def __init__(self):
        self.cleaner = TextCleaner()
        self.tokenizer = TextTokenizer()
        self.feature_extractor = FeatureExtractor()
        self.embedding_generator = EmbeddingGenerator()

    async def process(self, extracted_text: Dict[str, str]) -> Dict[str, Any]:
        """
        Process extracted text through the NLP pipeline.

        Args:
            extracted_text: Dict mapping question IDs to raw answer text.
                Example: {"Q1": "The CPU processes...", "Q2": "..."}

        Returns:
            Dict with processed data for each question:
            {
                "Q1": {
                    "original_text": "...",
                    "cleaned_text": "...",
                    "tokens": [...],
                    "sentences": [...],
                    "pos_tags": [...],
                    "entities": [...],
                    "embedding": [0.1, 0.2, ...],
                },
                ...
            }
        """
        processed = {}

        for question_id, text in extracted_text.items():
            # Step 1: Clean and normalize text
            cleaned_text = self.cleaner.clean(text)

            # Step 2: Tokenize
            tokens = self.tokenizer.tokenize_words(cleaned_text)
            sentences = self.tokenizer.tokenize_sentences(cleaned_text)

            # Step 3: Extract linguistic features
            features = self.feature_extractor.extract(cleaned_text)

            # Step 4: Generate sentence embedding
            embedding = await self.embedding_generator.generate(cleaned_text)

            processed[question_id] = {
                "original_text": text,
                "cleaned_text": cleaned_text,
                "tokens": tokens,
                "sentences": sentences,
                "pos_tags": features.get("pos_tags", []),
                "entities": features.get("entities", []),
                "embedding": embedding,
            }

        return processed
