"""
Content Preprocessor

Preprocesses academic document content before indexing:
- Remove headers/footers
- Normalize whitespace
- Remove page numbers
- Clean formatting artifacts
"""

import re


class ContentPreprocessor:
    """
    Preprocesses academic document text for knowledge base indexing.

    Cleans up formatting artifacts, page numbers, and other
    non-content elements from parsed documents.
    """

    def preprocess(self, text: str) -> str:
        """
        Preprocess document text for indexing.

        Args:
            text: Raw parsed document text.

        Returns:
            Cleaned text ready for chunking.
        """
        if not text:
            return ""

        # Remove page numbers (standalone numbers on a line)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

        # Remove excessive newlines (more than 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove excessive whitespace within lines
        text = re.sub(r"[ \t]+", " ", text)

        # Remove common header/footer patterns
        text = re.sub(r"(?i)page\s+\d+\s*(of\s+\d+)?", "", text)

        # Strip each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text
