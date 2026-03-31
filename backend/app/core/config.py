"""
Application Configuration

Loads all settings from environment variables / .env file using Pydantic Settings.
Single source of truth for all configurable values.
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All values can be overridden via .env file.
    """

    # ---- Application ----
    APP_NAME: str = "Evaluate AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ---- Database ----
    DATABASE_URL: str = "postgresql+asyncpg://postgres:aastha@localhost:5432/evaluate_ai"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://postgres:aastha@localhost:5432/evaluate_ai"

    # ---- JWT Authentication ----
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ---- Ollama LLM ----
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # ---- Sentence-BERT Embeddings ----
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ---- QWEN V3 OCR ----
    QWEN_MODEL: str = "Qwen/Qwen2-VL-7B-Instruct"

    # ---- File Storage ----
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # ---- RAG Configuration ----
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5

    # ---- CORS ----
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
