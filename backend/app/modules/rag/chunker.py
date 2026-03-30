"""
Document Chunker

Splits documents into overlapping chunks for RAG indexing.
Supports configurable chunk size and overlap.
"""

from typing import List, Dict


class DocumentChunker:
    """
    Chunks documents into overlapping text segments.

    Uses character-based splitting with configurable size and overlap.
    Attempts to split at sentence boundaries when possible.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> List[Dict]:
        """
        Split text into overlapping chunks.

        Args:
            text: Full document text.

        Returns:
            List of chunk dicts with 'content', 'chunk_index', 'start_char', 'end_char'.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to find a sentence boundary near the end
            if end < len(text):
                # Look for sentence-ending punctuation within the last 20% of chunk
                search_start = max(start, end - int(self.chunk_size * 0.2))
                last_period = text.rfind(".", search_start, end)
                last_newline = text.rfind("\n", search_start, end)
                boundary = max(last_period, last_newline)

                if boundary > search_start:
                    end = boundary + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                })
                chunk_index += 1

            # Move start forward, accounting for overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start >= len(text) or end >= len(text):
                break

        return chunks
