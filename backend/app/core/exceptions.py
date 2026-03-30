"""
Custom Exception Classes

Defines a hierarchy of application-specific exceptions
for consistent error handling across all modules.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


# ---- Authentication Exceptions ----
class InvalidCredentialsError(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self):
        super().__init__(
            detail="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenExpiredError(AppException):
    """Raised when JWT token has expired."""

    def __init__(self):
        super().__init__(
            detail="Token has expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class InsufficientPermissionsError(AppException):
    """Raised when user lacks required role permissions."""

    def __init__(self, required_role: str = "teacher"):
        super().__init__(
            detail=f"This action requires '{required_role}' role",
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ---- Document Exceptions ----
class DocumentNotFoundError(AppException):
    """Raised when a requested document is not found."""

    def __init__(self, document_id: str):
        super().__init__(
            detail=f"Document '{document_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class FileTooLargeError(AppException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size_mb: int):
        super().__init__(
            detail=f"File exceeds maximum size of {max_size_mb}MB",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class UnsupportedFileTypeError(AppException):
    """Raised when file type is not supported."""

    def __init__(self, file_type: str):
        super().__init__(
            detail=f"File type '{file_type}' is not supported. Use PDF, PNG, JPG, or JPEG.",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


# ---- Processing Exceptions ----
class OCRProcessingError(AppException):
    """Raised when OCR processing fails."""

    def __init__(self, detail: str = "OCR processing failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NLPProcessingError(AppException):
    """Raised when NLP processing fails."""

    def __init__(self, detail: str = "NLP processing failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EvaluationError(AppException):
    """Raised when LLM evaluation fails."""

    def __init__(self, detail: str = "Evaluation processing failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RAGQueryError(AppException):
    """Raised when RAG retrieval fails."""

    def __init__(self, detail: str = "Knowledge retrieval failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---- Evaluation Exceptions ----
class EvaluationNotFoundError(AppException):
    """Raised when evaluation results are not found."""

    def __init__(self, evaluation_id: str):
        super().__init__(
            detail=f"Evaluation '{evaluation_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
