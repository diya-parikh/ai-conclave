"""
Storage Service

Manages local file storage operations for uploaded documents.
"""

import os
import uuid
import shutil
from typing import Optional

from app.core.config import settings


class StorageService:
    """
    Handles file storage operations for uploaded documents.

    All files are stored locally in the configured UPLOAD_DIR.
    """

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, content: bytes, original_filename: str) -> str:
        """
        Save file content to disk.

        Args:
            content: File bytes.
            original_filename: Original filename for extension extraction.

        Returns:
            Path where the file was saved.
        """
        ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from disk.

        Args:
            file_path: Path to the file.

        Returns:
            True if deleted, False if not found.
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(file_path)
