"""
Shared API Dependencies

Provides dependency injection for database sessions, current user,
and role-based access control.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.database import get_db
from app.models.user import User

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Extract and validate the current user from JWT token.

    Raises:
        HTTPException 401: If token is invalid or user not found.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def require_teacher(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency: Ensure the current user has the 'teacher' role.

    Raises:
        HTTPException 403: If user is not a teacher.
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires 'teacher' role",
        )
    return current_user


async def require_student(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency: Ensure the current user has the 'student' role.

    Raises:
        HTTPException 403: If user is not a student.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires 'student' role",
        )
    return current_user
