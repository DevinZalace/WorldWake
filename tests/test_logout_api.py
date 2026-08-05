"""Tests for CSRF-protected account logout."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from worldwake.auth import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    hash_token,
)
from worldwake.models import AuthSession


VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": "RiverStone42",
}


def register_signed_in_account(
    api_client: TestClient,
) -> tuple[str, str]:
    """Register a user and return the issued browser tokens."""

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert response.status_code == 201

    session_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )
    csrf_token = api_client.cookies.get(
        CSRF_COOKIE_NAME
    )

    assert session_token is not None
    assert csrf_token is not None

    return session_token, csrf_token


def test_logout_requires_csrf_header(
    api_client: TestClient,
) -> None:
    """A session cookie alone must not authorize logout."""

    register_signed_in_account(api_client)

    response = api_client.post(
        "/api/auth/logout"
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "CSRF validation failed."
    }

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 200


def test_logout_rejects_incorrect_csrf_header(
    api_client: TestClient,
) -> None:
    """A fabricated CSRF header must not revoke the session."""

    register_signed_in_account(api_client)

    response = api_client.post(
        "/api/auth/logout",
        headers={
            CSRF_HEADER_NAME: (
                "fabricated-csrf-token"
            ),
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "CSRF validation failed."
    }

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 200


def test_logout_rejects_mismatched_csrf_cookie_and_header(
    api_client: TestClient,
) -> None:
    """The browser cookie and submitted header must agree."""

    _, csrf_token = register_signed_in_account(
        api_client
    )

    api_client.cookies.set(
        CSRF_COOKIE_NAME,
        f"{csrf_token}-changed",
    )

    response = api_client.post(
        "/api/auth/logout",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
    )

    assert response.status_code == 403


def test_logout_revokes_session_and_clears_cookies(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """Valid logout should revoke the record and forget credentials."""

    session_token, csrf_token = (
        register_signed_in_account(api_client)
    )

    response = api_client.post(
        "/api/auth/logout",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
    )

    assert response.status_code == 204
    assert response.content == b""

    assert api_client.cookies.get(
        SESSION_COOKIE_NAME
    ) is None

    assert api_client.cookies.get(
        CSRF_COOKIE_NAME
    ) is None

    with test_session_factory() as session:
        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(session_token)
            )
        )

        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_logged_out_browser_loses_protected_access(
    api_client: TestClient,
) -> None:
    """The revoked session must no longer authenticate `/me`."""

    _, csrf_token = register_signed_in_account(
        api_client
    )

    logout_response = api_client.post(
        "/api/auth/logout",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
    )

    assert logout_response.status_code == 204

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 401
    assert me_response.json() == {
        "detail": "Authentication required."
    }