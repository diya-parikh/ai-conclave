"""
Text Chunker

Splits text into meaningful semantic chunks suitable for embeddings.
"""

from typing import List
from app.modules.nlp.tokenizer import TextTokenizer


class TextChunker:
    """
    Intelligently chunks text by grouping sentences up to a target 
    word limit. Maintains semantic coherence by keeping sentences intact.
    """

    def __init__(self, min_words: int = 50, max_words: int = 120):
        self.min_words = min_words
        self.max_words = max_words
        self.tokenizer = TextTokenizer()

    def chunk(self, text: str) -> List[str]:
        """
        Group sentences into semantically cohesive chunks.

        Args:
            text: Cleaned input text.

        Returns:
            List of chunk strings.
        """
        if not text:
            return []

        sentences = self.tokenizer.tokenize_sentences(text)

        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            word_count = len(sentence.split())

            # If adding this sentence exceeds the max word count, 
            # and our current chunk has reached the minimum threshold, save the chunk.
            # If the single sentence is massive, we append it directly to avoid breaking meaning.
            if current_word_count + word_count > self.max_words and current_word_count >= self.min_words:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_word_count = word_count
            else:
                current_chunk.append(sentence)
                current_word_count += word_count

        # Append any remaining text
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
