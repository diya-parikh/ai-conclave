"""
Database Engine & Session Management

Configures SQLAlchemy async engine, session factory, and Base class.
Provides init_db() for table creation and get_db() for dependency injection.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ---- Async Engine ----
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
)

# ---- Session Factory ----
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---- Base Class ----
class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def init_db():
    """
    Initialize database tables.
    Creates pgvector extension if needed, then creates all tables defined by Base subclasses.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Enable pgvector extension
        # await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Import all models to ensure they are registered with Base
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    Automatically commits on success, rolls back on error.

    Usage in FastAPI endpoints:
        async def endpoint(db: AsyncSession = Depends(get_db)):
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
