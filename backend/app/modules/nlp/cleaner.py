"""
Text Cleaner

Handles text cleaning and normalization:
- Lowercasing
- Special character removal
- Whitespace normalization
- Stopword removal
- Lemmatization
"""

import re
from typing import Optional, Set, Any


class TextCleaner:
    """
    Cleans and normalizes raw OCR-extracted text.

    Applies a series of text cleaning operations to prepare
    student answers for NLP processing.
    """

    def __init__(self):
        self._stopwords: Optional[Set[str]] = None
        self._lemmatizer: Optional[Any] = None

    def _load_nltk_resources(self) -> None:
        """Lazy-load NLTK resources."""
        if self._stopwords is None:
            import nltk
            try:
                from nltk.corpus import stopwords
                from nltk.stem import WordNetLemmatizer
                self._stopwords = set(stopwords.words("english"))
                self._lemmatizer = WordNetLemmatizer()
            except LookupError:
                nltk.download("stopwords", quiet=True)
                nltk.download("wordnet", quiet=True)
                from nltk.corpus import stopwords
                from nltk.stem import WordNetLemmatizer
                self._stopwords = set(stopwords.words("english"))
                self._lemmatizer = WordNetLemmatizer()

    def clean(self, text: str, remove_stopwords: bool = False) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw input text.
            remove_stopwords: Whether to remove stopwords. Default False
                because stopwords can be important for semantic meaning.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep periods, commas, and basic punctuation
        text = re.sub(r"[^\w\s.,;:!?'\-]", "", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Optionally remove stopwords
        if remove_stopwords:
            self._load_nltk_resources()
            assert self._stopwords is not None, "Stopwords failed to load"
            words = text.split()
            text = " ".join(w for w in words if w not in self._stopwords)

        return text

    def lemmatize(self, text: str) -> str:
        """
        Apply lemmatization to reduce words to their base form.

        Args:
            text: Input text.

        Returns:
            Lemmatized text.
        """
        self._load_nltk_resources()
        assert self._lemmatizer is not None, "Lemmatizer failed to load"
        words = text.split()
        lemmatized = [self._lemmatizer.lemmatize(word) for word in words]
        return " ".join(lemmatized)
