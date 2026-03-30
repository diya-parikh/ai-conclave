"""
Text Utilities

Helper functions for text processing operations.
"""

import re
from typing import List


def count_words(text: str) -> int:
    """Count the number of words in text."""
    if not text:
        return 0
    return len(text.split())


def count_sentences(text: str) -> int:
    """Approximate sentence count using punctuation."""
    if not text:
        return 0
    sentences = re.split(r"[.!?]+", text)
    return len([s for s in sentences if s.strip()])


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """Truncate text to max_length characters."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """Replace multiple whitespace characters with a single space."""
    return re.sub(r"\s+", " ", text).strip()


def extract_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]
