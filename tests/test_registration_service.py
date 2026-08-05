"""Tests for account registration services."""

import pytest
from sqlalchemy.orm import Session

from worldwake.auth import (
    ACCOUNT_CONFLICT_MESSAGE,
    AccountConflictError,
    RegisterRequest,
    register_user,
    verify_password,
)
from worldwake.models import User


def make_registration(
    *,
    username: str = "DevTheMapper",
    email: str = "dev@example.com",
    password: str = "RiverStone42",
) -> RegisterRequest:
    """Create validated registration input for a test."""

    return RegisterRequest.model_validate(
        {
            "username": username,
            "email": email,
            "password": password,
        }
    )


def test_register_user_stores_safe_account_data(
    database_session: Session,
) -> None:
    """Registration should persist normalized, hashed account data."""

    registration = make_registration()

    user = register_user(
        database_session,
        registration,
    )

    assert user.id is not None

    assert user.username == "DevTheMapper"
    assert user.username_normalized == "devthemapper"

    assert user.email == "dev@example.com"
    assert user.email_normalized == "dev@example.com"

    assert user.password_hash != "RiverStone42"
    assert user.password_hash.startswith("$argon2id$")

    assert verify_password(
        user.password_hash,
        "RiverStone42",
    ) is True

    stored_user = database_session.get(
        User,
        user.id,
    )

    assert stored_user is not None
    assert stored_user.username == "DevTheMapper"


def test_register_user_rejects_duplicate_username(
    database_session: Session,
) -> None:
    """Username uniqueness should be case-insensitive."""

    register_user(
        database_session,
        make_registration(
            username="WorldWaker",
            email="first@example.com",
        ),
    )

    with pytest.raises(
        AccountConflictError,
        match=ACCOUNT_CONFLICT_MESSAGE,
    ):
        register_user(
            database_session,
            make_registration(
                username="WORLDWAKER",
                email="second@example.com",
            ),
        )


def test_register_user_rejects_duplicate_email(
    database_session: Session,
) -> None:
    """Email uniqueness should be case-insensitive."""

    register_user(
        database_session,
        make_registration(
            username="FirstMapper",
            email="Dev@Example.com",
        ),
    )

    with pytest.raises(
        AccountConflictError,
        match=ACCOUNT_CONFLICT_MESSAGE,
    ):
        register_user(
            database_session,
            make_registration(
                username="SecondMapper",
                email="DEV@EXAMPLE.COM",
            ),
        )


def test_register_user_does_not_commit_transaction(
    database_session: Session,
) -> None:
    """The request lifecycle, not the service, should commit."""

    user = register_user(
        database_session,
        make_registration(),
    )
    user_id = user.id

    database_session.rollback()

    stored_user = database_session.get(
        User,
        user_id,
    )

    assert stored_user is None