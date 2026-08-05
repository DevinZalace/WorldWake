"""Database model for a WorldWake user account."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from worldwake.models.base import Base, utc_now


if TYPE_CHECKING:
    from worldwake.models.auth_session import AuthSession


class User(Base):
    """A person with a private WorldWake account."""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "length(username) BETWEEN 3 AND 30",
            name="username_length",
        ),
        CheckConstraint(
            "length(username_normalized) BETWEEN 3 AND 30",
            name="username_normalized_length",
        ),
        CheckConstraint(
            "length(email) BETWEEN 3 AND 320",
            name="email_length",
        ),
        CheckConstraint(
            "length(email_normalized) BETWEEN 3 AND 320",
            name="email_normalized_length",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    username_normalized: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    email_normalized: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )