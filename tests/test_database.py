"""Tests for isolated database configuration."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from worldwake.models import AuthSession, User


def test_temporary_database_starts_empty(
    database_session: Session,
) -> None:
    """Each database fixture should begin without account records."""

    user_count = database_session.scalar(
        select(func.count(User.id))
    )
    session_count = database_session.scalar(
        select(func.count(AuthSession.id))
    )

    assert user_count == 0
    assert session_count == 0


def test_temporary_database_can_store_user(
    database_session: Session,
) -> None:
    """A valid user should persist inside the temporary database."""

    user = User(
        username="DevTheMapper",
        username_normalized="devthemapper",
        email="dev@example.com",
        email_normalized="dev@example.com",
        password_hash="$argon2id$temporary-test-hash",
    )

    database_session.add(user)
    database_session.commit()

    stored_user = database_session.scalar(
        select(User).where(
            User.username_normalized == "devthemapper"
        )
    )

    assert stored_user is not None
    assert stored_user.id == user.id
    assert stored_user.username == "DevTheMapper"


def test_database_rejects_duplicate_normalized_username(
    database_session: Session,
) -> None:
    """The database should enforce case-insensitive uniqueness."""

    first_user = User(
        username="WorldWaker",
        username_normalized="worldwaker",
        email="first@example.com",
        email_normalized="first@example.com",
        password_hash="$argon2id$first-test-hash",
    )
    second_user = User(
        username="WORLDWAKER",
        username_normalized="worldwaker",
        email="second@example.com",
        email_normalized="second@example.com",
        password_hash="$argon2id$second-test-hash",
    )

    database_session.add(first_user)
    database_session.commit()

    database_session.add(second_user)

    with pytest.raises(IntegrityError):
        database_session.commit()

    database_session.rollback()


def test_database_enforces_session_user_foreign_key(
    database_session: Session,
) -> None:
    """A login session cannot belong to a nonexistent user."""

    now = datetime.now(UTC)

    orphaned_session = AuthSession(
        user_id=uuid4(),
        token_hash="a" * 64,
        csrf_token_hash="b" * 64,
        created_at=now,
        last_used_at=now,
        expires_at=now + timedelta(days=30),
    )

    database_session.add(orphaned_session)

    with pytest.raises(IntegrityError):
        database_session.commit()

    database_session.rollback()