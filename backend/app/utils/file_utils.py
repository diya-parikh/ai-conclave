"""
File Utilities

Helper functions for file handling operations.
"""

import os
import mimetypes
from typing import Optional


ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}
ALLOWED_KNOWLEDGE_EXTENSIONS = {".pdf", ".docx", ".txt", ".doc"}


def get_file_extension(filename: str) -> str:
    """Extract file extension in lowercase."""
    return os.path.splitext(filename)[1].lower()


def is_allowed_upload(filename: str) -> bool:
    """Check if file extension is allowed for answer sheet uploads."""
    return get_file_extension(filename) in ALLOWED_UPLOAD_EXTENSIONS


def is_allowed_knowledge(filename: str) -> bool:
    """Check if file extension is allowed for knowledge base uploads."""
    return get_file_extension(filename) in ALLOWED_KNOWLEDGE_EXTENSIONS


def get_mime_type(filename: str) -> Optional[str]:
    """Guess MIME type from filename."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
