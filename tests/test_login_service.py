"""Tests for account login services."""

from argon2 import PasswordHasher
import pytest
from sqlalchemy.orm import Session

from worldwake.auth import (
    INVALID_CREDENTIALS_MESSAGE,
    InvalidCredentialsError,
    LoginRequest,
    RegisterRequest,
    authenticate_user,
    password_hash_needs_rehash,
    register_user,
    verify_password,
)
from worldwake.models import User


PASSWORD = "RiverStone42"


def create_registered_user(
    database_session: Session,
) -> User:
    """Create a user available for login tests."""

    registration = RegisterRequest.model_validate(
        {
            "username": "DevTheMapper",
            "email": "Dev@Example.com",
            "password": PASSWORD,
        }
    )

    return register_user(
        database_session,
        registration,
    )


def make_login(
    identifier: str,
    password: str = PASSWORD,
) -> LoginRequest:
    """Create validated login input."""

    return LoginRequest.model_validate(
        {
            "identifier": identifier,
            "password": password,
        }
    )


def test_authenticate_user_by_username_case_insensitively(
    database_session: Session,
) -> None:
    """Username login should ignore letter casing."""

    user = create_registered_user(
        database_session
    )

    authenticated_user = authenticate_user(
        database_session,
        make_login("DEVTHeMAPPER"),
    )

    assert authenticated_user.id == user.id


def test_authenticate_user_by_email_case_insensitively(
    database_session: Session,
) -> None:
    """Email login should ignore letter casing."""

    user = create_registered_user(
        database_session
    )

    authenticated_user = authenticate_user(
        database_session,
        make_login("DEV@EXAMPLE.COM"),
    )

    assert authenticated_user.id == user.id


@pytest.mark.parametrize(
    ("identifier", "password"),
    [
        (
            "DevTheMapper",
            "CompletelyWrong42",
        ),
        (
            "NobodyLivesHere",
            PASSWORD,
        ),
    ],
)
def test_authentication_failures_use_generic_message(
    database_session: Session,
    identifier: str,
    password: str,
) -> None:
    """Wrong and unknown credentials should appear identical."""

    create_registered_user(database_session)

    with pytest.raises(
        InvalidCredentialsError,
        match=INVALID_CREDENTIALS_MESSAGE,
    ):
        authenticate_user(
            database_session,
            make_login(
                identifier,
                password,
            ),
        )


def test_authenticate_user_upgrades_legacy_hash(
    database_session: Session,
) -> None:
    """Successful login should replace outdated Argon2 settings."""

    user = create_registered_user(
        database_session
    )

    legacy_hasher = PasswordHasher(
        time_cost=1,
        memory_cost=8192,
        parallelism=1,
    )

    legacy_hash = legacy_hasher.hash(PASSWORD)
    user.password_hash = legacy_hash

    database_session.flush()

    assert password_hash_needs_rehash(
        legacy_hash
    ) is True

    authenticated_user = authenticate_user(
        database_session,
        make_login("DevTheMapper"),
    )

    assert authenticated_user.id == user.id
    assert authenticated_user.password_hash != legacy_hash

    assert verify_password(
        authenticated_user.password_hash,
        PASSWORD,
    ) is True

    assert password_hash_needs_rehash(
        authenticated_user.password_hash
    ) is False