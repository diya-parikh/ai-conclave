"""
Text Tokenizer

Handles tokenization using NLTK:
- Sentence tokenization
- Word tokenization
"""

from typing import List


class TextTokenizer:
    """
    Tokenizes text into sentences and words using NLTK.
    """

    def __init__(self):
        self._sent_tokenizer_loaded = False
        self._word_tokenizer_loaded = False

    def _ensure_nltk_data(self):
        """Download NLTK data if not available."""
        if not self._sent_tokenizer_loaded:
            import nltk
            try:
                nltk.data.find("tokenizers/punkt_tab")
            except LookupError:
                nltk.download("punkt_tab", quiet=True)
            self._sent_tokenizer_loaded = True
            self._word_tokenizer_loaded = True

    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text.

        Returns:
            List of sentence strings.
        """
        if not text:
            return []

        self._ensure_nltk_data()
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)

    def tokenize_words(self, text: str) -> List[str]:
        """
        Split text into words.

        Args:
            text: Input text.

        Returns:
            List of word tokens.
        """
        if not text:
            return []

        self._ensure_nltk_data()
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)
