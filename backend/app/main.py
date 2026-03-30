"""
Evaluate AI Capstone — Main Application Entry Point

FastAPI application factory with CORS, router mounts, and lifespan events.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Startup: Initialize database tables, create upload directory.
    Shutdown: Cleanup resources.
    """
    # ---- Startup ----
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize database tables
    await init_db()

    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started successfully")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"🤖 Ollama model: {settings.OLLAMA_MODEL}")

    yield

    # ---- Shutdown ----
    print(f"👋 {settings.APP_NAME} shutting down...")


def create_app() -> FastAPI:
    """
    Application factory.
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Automated Evaluation of Handwritten Student Answer Sheets. "
            "Uses OCR, NLP, RAG, and LLM to evaluate answers and generate feedback."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ---- CORS Middleware ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Mount API Router ----
    app.include_router(api_router, prefix="/api/v1")

    # ---- Health Check ----
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }

    return app


# Create the application instance
app = create_app()
