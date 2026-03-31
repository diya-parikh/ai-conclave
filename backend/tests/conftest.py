"""
Test Configuration & Fixtures

Provides shared test fixtures including:
- Test database setup
- Test client
- Authentication helpers
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app
from app.models.database import Base, engine, async_session_factory
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean database session for each test."""
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Provide an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def teacher_token():
    """Generate a JWT token for a teacher user."""
    return create_access_token(data={"sub": "test-teacher-id", "role": "teacher"})


@pytest.fixture
def student_token():
    """Generate a JWT token for a student user."""
    return create_access_token(data={"sub": "test-student-id", "role": "student"})


@pytest.fixture
def teacher_headers(teacher_token):
    """Auth headers for teacher requests."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def student_headers(student_token):
    """Auth headers for student requests."""
    return {"Authorization": f"Bearer {student_token}"}
