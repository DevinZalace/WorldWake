"""Tests for password-change services."""

import pytest
from sqlalchemy.orm import Session

from worldwake.auth import (
    INCORRECT_CURRENT_PASSWORD_MESSAGE,
    IncorrectCurrentPasswordError,
    RegisterRequest,
    change_user_password,
    register_user,
    verify_password,
)
from worldwake.models import User


OLD_PASSWORD = "RiverStone42"
NEW_PASSWORD = "MountainRiver84"


def create_test_user(
    database_session: Session,
) -> User:
    """Create an account for password-change tests."""

    registration = RegisterRequest.model_validate(
        {
            "username": "DevTheMapper",
            "email": "dev@example.com",
            "password": OLD_PASSWORD,
        }
    )

    return register_user(
        database_session,
        registration,
    )


def test_change_user_password_replaces_hash(
    database_session: Session,
) -> None:
    """A correct current password should install a new hash."""

    user = create_test_user(database_session)
    original_hash = user.password_hash

    change_user_password(
        database_session,
        user,
        OLD_PASSWORD,
        NEW_PASSWORD,
    )

    assert user.password_hash != original_hash

    assert verify_password(
        user.password_hash,
        OLD_PASSWORD,
    ) is False

    assert verify_password(
        user.password_hash,
        NEW_PASSWORD,
    ) is True


def test_change_user_password_rejects_wrong_current_password(
    database_session: Session,
) -> None:
    """An incorrect current password must preserve the old hash."""

    user = create_test_user(database_session)
    original_hash = user.password_hash

    with pytest.raises(
        IncorrectCurrentPasswordError,
        match=INCORRECT_CURRENT_PASSWORD_MESSAGE,
    ):
        change_user_password(
            database_session,
            user,
            "CompletelyWrong42",
            NEW_PASSWORD,
        )

    assert user.password_hash == original_hash

    assert verify_password(
        user.password_hash,
        OLD_PASSWORD,
    ) is True