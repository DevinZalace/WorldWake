"""Tests for authenticated password changes."""

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


OLD_PASSWORD = "RiverStone42"
NEW_PASSWORD = "MountainRiver84"

VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": OLD_PASSWORD,
}


def register_account(
    api_client: TestClient,
) -> tuple[str, str]:
    """Register and return the first issued credentials."""

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


def login_account(
    api_client: TestClient,
    password: str = OLD_PASSWORD,
) -> tuple[str, str]:
    """Log in and return the newly issued credentials."""

    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DevTheMapper",
            "password": password,
        },
    )

    assert response.status_code == 200

    session_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )
    csrf_token = api_client.cookies.get(
        CSRF_COOKIE_NAME
    )

    assert session_token is not None
    assert csrf_token is not None

    return session_token, csrf_token


def test_change_password_revokes_old_sessions_and_issues_fresh_one(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
) -> None:
    """Password replacement should rotate every browser credential."""

    first_token, _ = register_account(api_client)
    second_token, second_csrf = login_account(api_client)

    response = api_client.post(
        "/api/auth/change-password",
        headers={
            CSRF_HEADER_NAME: second_csrf,
        },
        json={
            "current_password": OLD_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "DevTheMapper"

    fresh_token = api_client.cookies.get(
        SESSION_COOKIE_NAME
    )
    fresh_csrf = api_client.cookies.get(
        CSRF_COOKIE_NAME
    )

    assert fresh_token is not None
    assert fresh_csrf is not None

    assert fresh_token != first_token
    assert fresh_token != second_token
    assert fresh_csrf != second_csrf

    with test_session_factory() as session:
        first_record = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(first_token)
            )
        )
        second_record = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(second_token)
            )
        )
        fresh_record = session.scalar(
            select(AuthSession).where(
                AuthSession.token_hash
                == hash_token(fresh_token)
            )
        )

        assert first_record is not None
        assert second_record is not None
        assert fresh_record is not None

        assert first_record.revoked_at is not None
        assert second_record.revoked_at is not None
        assert fresh_record.revoked_at is None


def test_old_session_token_loses_access_after_password_change(
    api_client: TestClient,
) -> None:
    """Previously issued tokens must not authenticate afterward."""

    old_token, old_csrf = register_account(api_client)

    response = api_client.post(
        "/api/auth/change-password",
        headers={
            CSRF_HEADER_NAME: old_csrf,
        },
        json={
            "current_password": OLD_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 200

    api_client.cookies.set(
        SESSION_COOKIE_NAME,
        old_token,
    )
    api_client.cookies.set(
        CSRF_COOKIE_NAME,
        old_csrf,
    )

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 401


def test_old_password_fails_and_new_password_succeeds(
    api_client: TestClient,
) -> None:
    """Only the replacement password should work afterward."""

    _, csrf_token = register_account(api_client)

    change_response = api_client.post(
        "/api/auth/change-password",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
        json={
            "current_password": OLD_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert change_response.status_code == 200

    api_client.cookies.clear()

    old_login = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DevTheMapper",
            "password": OLD_PASSWORD,
        },
    )

    assert old_login.status_code == 401

    new_login = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DevTheMapper",
            "password": NEW_PASSWORD,
        },
    )

    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(
    api_client: TestClient,
) -> None:
    """A wrong current password must not destroy the active session."""

    _, csrf_token = register_account(api_client)

    response = api_client.post(
        "/api/auth/change-password",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
        json={
            "current_password": "CompletelyWrong42",
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Current password is incorrect."
    }

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 200


def test_change_password_requires_csrf(
    api_client: TestClient,
) -> None:
    """Authentication alone must not authorize password changes."""

    register_account(api_client)

    response = api_client.post(
        "/api/auth/change-password",
        json={
            "current_password": OLD_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "CSRF validation failed."
    }


def test_change_password_validation_hides_new_password(
    api_client: TestClient,
) -> None:
    """Rejected passwords must not be echoed in API responses."""

    _, csrf_token = register_account(api_client)

    submitted_password = "tiny"

    response = api_client.post(
        "/api/auth/change-password",
        headers={
            CSRF_HEADER_NAME: csrf_token,
        },
        json={
            "current_password": OLD_PASSWORD,
            "new_password": submitted_password,
        },
    )

    assert response.status_code == 422
    assert submitted_password not in response.text