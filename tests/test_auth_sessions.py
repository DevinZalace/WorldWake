"""Tests for secure authentication-session creation."""

from worldwake.models import AuthSession, User

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from worldwake.auth import (
    SESSION_LIFETIME,
    RegisterRequest,
    create_auth_session,
    hash_token,
    register_user,
    revoke_auth_session,
)
from worldwake.models import AuthSession


def create_test_user(
    database_session: Session,
) -> User:
    """Create a user for authentication-session tests."""

    registration = RegisterRequest.model_validate(
        {
            "username": "DevTheMapper",
            "email": "dev@example.com",
            "password": "RiverStone42",
        }
    )

    return register_user(
        database_session,
        registration,
    )


def test_create_auth_session_stores_only_token_hashes(
    database_session: Session,
) -> None:
    """Raw browser credentials should not be stored in the database."""

    user = create_test_user(database_session)

    issued_session = create_auth_session(
        database_session,
        user,
    )

    stored_session = issued_session.record

    assert stored_session.id is not None
    assert stored_session.user_id == user.id

    assert (
        stored_session.token_hash
        == hash_token(issued_session.session_token)
    )
    assert (
        stored_session.csrf_token_hash
        == hash_token(issued_session.csrf_token)
    )

    assert stored_session.token_hash != issued_session.session_token
    assert (
        stored_session.csrf_token_hash
        != issued_session.csrf_token
    )

    assert len(stored_session.token_hash) == 64
    assert len(stored_session.csrf_token_hash) == 64


def test_create_auth_session_sets_absolute_expiration(
    database_session: Session,
) -> None:
    """A new session should expire exactly 30 days after creation."""

    user = create_test_user(database_session)

    creation_time = datetime(
        2026,
        8,
        5,
        20,
        0,
        tzinfo=UTC,
    )

    issued_session = create_auth_session(
        database_session,
        user,
        now=creation_time,
    )

    stored_session = issued_session.record

    assert stored_session.created_at == creation_time
    assert stored_session.last_used_at == creation_time
    assert (
        stored_session.expires_at
        == creation_time + SESSION_LIFETIME
    )
    assert stored_session.revoked_at is None


def test_each_auth_session_receives_unique_tokens(
    database_session: Session,
) -> None:
    """Separate browser sessions should not share credentials."""

    user = create_test_user(database_session)

    first_session = create_auth_session(
        database_session,
        user,
    )
    second_session = create_auth_session(
        database_session,
        user,
    )

    assert (
        first_session.session_token
        != second_session.session_token
    )
    assert first_session.csrf_token != second_session.csrf_token

    assert (
        first_session.record.token_hash
        != second_session.record.token_hash
    )
    assert (
        first_session.record.csrf_token_hash
        != second_session.record.csrf_token_hash
    )


def test_create_auth_session_does_not_commit(
    database_session: Session,
) -> None:
    """The request lifecycle should own the final commit."""

    user = create_test_user(database_session)

    issued_session = create_auth_session(
        database_session,
        user,
    )
    session_id = issued_session.record.id

    database_session.rollback()

    stored_session = database_session.get(
        AuthSession,
        session_id,
    )

    assert stored_session is None

def test_revoke_auth_session_records_revocation_time(
    database_session: Session,
) -> None:
    """Revoking a session should permanently mark its record."""

    user = create_test_user(database_session)

    issued_session = create_auth_session(
        database_session,
        user,
    )

    revocation_time = datetime(
        2026,
        8,
        5,
        21,
        30,
        tzinfo=UTC,
    )

    revoke_auth_session(
        issued_session.record,
        now=revocation_time,
    )

    assert (
        issued_session.record.revoked_at
        == revocation_time
    )