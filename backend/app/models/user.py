"""
User Model

Supports two roles: 'teacher' and 'student'.
Teachers upload and evaluate; students view their own results.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class User(Base):
    """
    User account model.

    Attributes:
        id: Unique identifier (UUID).
        name: Full name.
        email: Unique email address.
        hashed_password: Bcrypt-hashed password.
        role: Either 'teacher' or 'student'.
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("teacher", "student", name="user_role"),
        nullable=False,
        default="student",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    documents = relationship("Document", back_populates="teacher", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"
