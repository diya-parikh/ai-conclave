"""
Text Tokenizer

Handles tokenization using NLTK:
- Sentence tokenization ONLY
"""

from typing import List

class TextTokenizer:
    """
    Tokenizes text into sentences using NLTK.
    Used for intelligent chunking.
    """

    def __init__(self):
        self._sent_tokenizer_loaded = False

    def _ensure_nltk_data(self):
        """Download NLTK sentence tokenizer data if not available."""
        if not self._sent_tokenizer_loaded:
            import nltk
            try:
                nltk.data.find("tokenizers/punkt")
                nltk.data.find("tokenizers/punkt_tab")
            except LookupError:
                nltk.download("punkt", quiet=True)
                nltk.download("punkt_tab", quiet=True)
            self._sent_tokenizer_loaded = True

    def tokenize_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        """
        if not text:
            return []

        self._ensure_nltk_data()
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)
