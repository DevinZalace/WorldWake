"""Tests for the account-registration API."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from fastapi.testclient import TestClient

from worldwake.auth import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    hash_token,
)
from worldwake.models import AuthSession, User


VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": "RiverStone42",
}


def test_register_creates_account_and_session(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """Registration should create and sign in a safe account."""

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["username"] == "DevTheMapper"
    assert response_data["email"] == "dev@example.com"

    assert "password" not in response_data
    assert "password_hash" not in response_data
    assert "token_hash" not in response_data
    assert "csrf_token_hash" not in response_data

    session_token = response.cookies.get(
        SESSION_COOKIE_NAME
    )
    csrf_token = response.cookies.get(
        CSRF_COOKIE_NAME
    )

    assert session_token is not None
    assert csrf_token is not None
    assert session_token != csrf_token

    with test_session_factory() as session:
        user = session.scalar(
            select(User).where(
                User.username_normalized
                == "devthemapper"
            )
        )

        assert user is not None

        auth_session = session.scalar(
            select(AuthSession).where(
                AuthSession.user_id == user.id
            )
        )

        assert auth_session is not None
        assert (
            auth_session.token_hash
            == hash_token(session_token)
        )
        assert (
            auth_session.csrf_token_hash
            == hash_token(csrf_token)
        )


def test_registration_cookie_security_attributes(
    api_client: TestClient,
) -> None:
    """Local cookies should use the required safety attributes."""

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    set_cookie_headers = response.headers.get_list(
        "set-cookie"
    )

    session_cookie_header = next(
        header
        for header in set_cookie_headers
        if header.startswith(
            f"{SESSION_COOKIE_NAME}="
        )
    )
    csrf_cookie_header = next(
        header
        for header in set_cookie_headers
        if header.startswith(
            f"{CSRF_COOKIE_NAME}="
        )
    )

    assert "HttpOnly" in session_cookie_header
    assert "HttpOnly" not in csrf_cookie_header

    assert "SameSite=lax" in session_cookie_header
    assert "SameSite=lax" in csrf_cookie_header

    assert "Max-Age=2592000" in session_cookie_header
    assert "Max-Age=2592000" in csrf_cookie_header

    assert "Path=/" in session_cookie_header
    assert "Path=/" in csrf_cookie_header

    assert "Secure" not in session_cookie_header
    assert "Secure" not in csrf_cookie_header


def test_hosted_registration_uses_secure_cookies(
    api_client: TestClient,
    monkeypatch,
) -> None:
    """Hosted HTTPS mode should mark both cookies Secure."""

    monkeypatch.setenv(
        "WORLDWAKE_COOKIE_SECURE",
        "true",
    )

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    set_cookie_headers = response.headers.get_list(
        "set-cookie"
    )

    assert all(
        "Secure" in header
        for header in set_cookie_headers
        if (
            header.startswith(
                f"{SESSION_COOKIE_NAME}="
            )
            or header.startswith(
                f"{CSRF_COOKIE_NAME}="
            )
        )
    )


def test_register_rejects_duplicate_identity_generically(
    api_client: TestClient,
) -> None:
    """Duplicate accounts should not reveal the conflicting field."""

    first_response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert first_response.status_code == 201

    duplicate_response = api_client.post(
        "/api/auth/register",
        json={
            "username": "DEVTHeMAPPER",
            "email": "different@example.com",
            "password": "AnotherRiver42",
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": (
            "Unable to create an account "
            "with those details."
        )
    }

    assert (
        duplicate_response.cookies.get(
            SESSION_COOKIE_NAME
        )
        is None
    )


def test_registration_validation_does_not_echo_password(
    api_client: TestClient,
) -> None:
    """Rejected requests must not repeat raw passwords."""

    submitted_password = "short"

    response = api_client.post(
        "/api/auth/register",
        json={
            "username": "DevTheMapper",
            "email": "dev@example.com",
            "password": submitted_password,
        },
    )

    assert response.status_code == 422
    assert submitted_password not in response.text

    response_data = response.json()

    assert response_data["detail"]
    assert all(
        "input" not in error
        for error in response_data["detail"]
    )