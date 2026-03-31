"""
Feature Extractor

Extracts linguistic features using spaCy:
- Part-of-Speech (POS) tagging
- Named Entity Recognition (NER)
"""

from typing import Dict, List, Any, Optional


class FeatureExtractor:
    """
    Extracts linguistic features from text using spaCy.

    Lazy-loads the spaCy model on first use to avoid
    heavy memory allocation at startup.
    """

    def __init__(self):
        self._nlp: Optional[Any] = None

    def _load_model(self) -> None:
        """Lazy-load spaCy model."""
        if self._nlp is None:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Model not installed — download it
                from spacy.cli.download import download
                download("en_core_web_sm")
                self._nlp = spacy.load("en_core_web_sm")

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract POS tags and named entities from text.

        Args:
            text: Input text.

        Returns:
            Dictionary with 'pos_tags' and 'entities' lists.
            {
                "pos_tags": [{"token": "CPU", "pos": "NOUN", "tag": "NN"}, ...],
                "entities": [{"text": "Python", "label": "ORG", "start": 0, "end": 6}, ...],
            }
        """
        if not text:
            return {"pos_tags": [], "entities": []}

        self._load_model()
        assert self._nlp is not None, "spaCy model failed to load"
        doc = self._nlp(text)

        # POS Tags
        pos_tags = [
            {
                "token": token.text,
                "pos": token.pos_,
                "tag": token.tag_,
            }
            for token in doc
        ]

        # Named Entities
        entities = [
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            for ent in doc.ents
        ]

        return {
            "pos_tags": pos_tags,
            "entities": entities,
        }
