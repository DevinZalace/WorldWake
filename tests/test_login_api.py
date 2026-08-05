"""Tests for the account-login API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from worldwake.auth import (
    CSRF_COOKIE_NAME,
    INVALID_CREDENTIALS_MESSAGE,
    SESSION_COOKIE_NAME,
)
from worldwake.models import AuthSession


VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": "RiverStone42",
}


def register_account(
    api_client: TestClient,
) -> None:
    """Create an account for login tests."""

    response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert response.status_code == 201

    api_client.cookies.clear()


def test_login_by_username_creates_fresh_session(
    api_client: TestClient,
) -> None:
    """A valid username login should sign in the browser."""

    register_account(api_client)

    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DEVTHeMAPPER",
            "password": "RiverStone42",
        },
    )

    assert response.status_code == 200

    assert response.json()["username"] == (
        "DevTheMapper"
    )

    assert response.cookies.get(
        SESSION_COOKIE_NAME
    ) is not None

    assert response.cookies.get(
        CSRF_COOKIE_NAME
    ) is not None

    me_response = api_client.get(
        "/api/auth/me"
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == (
        "dev@example.com"
    )


def test_login_by_email_is_case_insensitive(
    api_client: TestClient,
) -> None:
    """A valid email login should ignore letter casing."""

    register_account(api_client)

    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DEV@EXAMPLE.COM",
            "password": "RiverStone42",
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == (
        "DevTheMapper"
    )


@pytest.mark.parametrize(
    ("identifier", "password"),
    [
        (
            "DevTheMapper",
            "CompletelyWrong42",
        ),
        (
            "NobodyLivesHere",
            "RiverStone42",
        ),
    ],
)
def test_login_failures_are_indistinguishable(
    api_client: TestClient,
    test_session_factory: sessionmaker[Session],
    identifier: str,
    password: str,
) -> None:
    """Unknown and incorrect credentials should match."""

    register_account(api_client)

    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": identifier,
            "password": password,
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": INVALID_CREDENTIALS_MESSAGE
    }

    assert response.cookies.get(
        SESSION_COOKIE_NAME
    ) is None

    with test_session_factory() as session:
        session_count = session.scalar(
            select(
                func.count(AuthSession.id)
            )
        )

    # Registration created one session.
    # Failed login must not create another.
    assert session_count == 1


def test_login_validation_does_not_echo_password(
    api_client: TestClient,
) -> None:
    """Invalid login input must not expose its password."""

    submitted_password = (
        "VisibleSecretValue" * 10
    )

    response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DevTheMapper",
            "password": submitted_password,
        },
    )

    assert response.status_code == 422
    assert submitted_password not in response.text