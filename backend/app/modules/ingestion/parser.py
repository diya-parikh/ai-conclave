"""
Document Parser

Parses various document formats (PDF, DOCX, TXT) to extract text content.
"""


class DocumentParser:
    """
    Parses academic documents in various formats.

    Supports:
    - PDF (via PyPDF2)
    - DOCX (via python-docx)
    - TXT (plain text)
    """

    async def parse(self, file_path: str, file_type: str) -> str:
        """
        Parse a document and extract text.

        Args:
            file_path: Path to the file.
            file_type: MIME type of the file.

        Returns:
            Extracted text string.
        """
        if "pdf" in file_type:
            return self._parse_pdf(file_path)
        elif "docx" in file_type or "word" in file_type:
            return self._parse_docx(file_path)
        elif "text" in file_type:
            return self._parse_txt(file_path)
        else:
            # Try as plain text
            return self._parse_txt(file_path)

    def _parse_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        pages_text = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        return "\n\n".join(pages_text)

    def _parse_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx."""
        from docx import Document

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)

    def _parse_txt(self, file_path: str) -> str:
        """Read plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
