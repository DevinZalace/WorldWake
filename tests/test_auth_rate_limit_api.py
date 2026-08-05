"""Tests for authentication endpoint rate limits."""

from fastapi.testclient import TestClient

from worldwake.auth import (
    LOGIN_IDENTIFIER_LIMIT,
    RATE_LIMIT_MESSAGE,
    REGISTER_IP_LIMIT,
)


VALID_REGISTRATION = {
    "username": "DevTheMapper",
    "email": "dev@example.com",
    "password": "RiverStone42",
}


def test_registration_is_rate_limited_by_client(
    api_client: TestClient,
) -> None:
    """Excessive registration attempts should return 429."""

    for attempt in range(
        REGISTER_IP_LIMIT
    ):
        response = api_client.post(
            "/api/auth/register",
            json=VALID_REGISTRATION,
        )

        if attempt == 0:
            assert response.status_code == 201
        else:
            assert response.status_code == 409

    blocked_response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert blocked_response.status_code == 429
    assert blocked_response.json() == {
        "detail": RATE_LIMIT_MESSAGE
    }

    retry_after = blocked_response.headers.get(
        "retry-after"
    )

    assert retry_after is not None
    assert int(retry_after) >= 1


def test_failed_logins_are_rate_limited_by_identifier(
    api_client: TestClient,
) -> None:
    """Repeated password failures should eventually return 429."""

    registration_response = api_client.post(
        "/api/auth/register",
        json=VALID_REGISTRATION,
    )

    assert registration_response.status_code == 201

    api_client.cookies.clear()

    for _ in range(
        LOGIN_IDENTIFIER_LIMIT
    ):
        response = api_client.post(
            "/api/auth/login",
            json={
                "identifier": "DevTheMapper",
                "password": "CompletelyWrong42",
            },
        )

        assert response.status_code == 401

    blocked_response = api_client.post(
        "/api/auth/login",
        json={
            "identifier": "DEVTHeMAPPER",
            "password": "CompletelyWrong42",
        },
    )

    assert blocked_response.status_code == 429
    assert blocked_response.json() == {
        "detail": RATE_LIMIT_MESSAGE
    }

    retry_after = blocked_response.headers.get(
        "retry-after"
    )

    assert retry_after is not None
    assert int(retry_after) >= 1