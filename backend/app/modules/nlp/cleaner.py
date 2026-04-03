import re

class TextCleaner:
    """
    Cleans and normalizes raw OCR-extracted text for RAG.
    Maintains semantic integrity without aggressive token dropping.
    """

    def clean(self, text: str) -> str:
        """
        Clean and normalize text.

        Preserves formulas, arrows, steps, and punctuation.
        Removes excessive noise and normalizes whitespaces.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace and newlines
        text = re.sub(r"\s+", " ", text)

        # Remove control characters that might interfere with embeddings
        text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)

        return text.strip()
