"""Tests for authenticated current-user access."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from worldwake.auth import (
    SESSION_COOKIE_NAME,
    hash_token,
)
from worldwake.models import AuthSession


VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": "RiverStone42",
}


def register_test_account(
    api_client: TestClient,
) -> None:
    """Register and retain a signed-in test account."""

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert response.status_code == 201


def test_me_returns_current_signed_in_user(
    api_client: TestClient,
) -> None:
    """A registered browser should retrieve its safe profile."""

    register_test_account(api_client)

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["username"] == "DevTheMapper"
    assert response_data["email"] == "dev@example.com"

    assert "password_hash" not in response_data
    assert "username_normalized" not in response_data
    assert "sessions" not in response_data


def test_me_rejects_anonymous_request(
    api_client: TestClient,
) -> None:
    """A browser without a session cookie should receive 401."""

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required."
    }


def test_me_rejects_unknown_session_token(
    api_client: TestClient,
) -> None:
    """An invented session token should not authenticate."""

    api_client.cookies.set(
        SESSION_COOKIE_NAME,
        "not-a-real-session-token",
    )

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required."
    }


def test_me_rejects_expired_session(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """An expired database session should receive 401."""

    register_test_account(api_client)

    session_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )

    assert session_token is not None

    with test_session_factory() as session:
        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(session_token)
            )
        )

        assert auth_session is not None

        auth_session.expires_at = (
            datetime.now(UTC)
            - timedelta(seconds=1)
        )

        session.commit()

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required."
    }


def test_me_rejects_revoked_session(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """A revoked database session should receive 401."""

    register_test_account(api_client)

    session_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )

    assert session_token is not None

    with test_session_factory() as session:
        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(session_token)
            )
        )

        assert auth_session is not None

        auth_session.revoked_at = datetime.now(UTC)

        session.commit()

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required."
    }


def test_me_updates_session_last_used_time(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """Accepting a session should refresh its last-use time."""

    register_test_account(api_client)

    session_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )

    assert session_token is not None

    old_time = datetime(
        2020,
        1,
        1,
        tzinfo=UTC,
    )

    with test_session_factory() as session:
        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(session_token)
            )
        )

        assert auth_session is not None

        auth_session.last_used_at = old_time
        session.commit()

    response = api_client.get(
        "/api/auth/me"
    )

    assert response.status_code == 200

    with test_session_factory() as session:
        refreshed_session = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(session_token)
            )
        )

        assert refreshed_session is not None
        assert refreshed_session.last_used_at != old_time