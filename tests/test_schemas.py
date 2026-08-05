"""Tests for authentication request and response schemas."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from worldwake.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


def test_registration_request_cleans_identity_fields() -> None:
    """Registration should clean username and email input."""

    request = RegisterRequest.model_validate(
    {
        "username": "  DevTheMapper  ",
        "email": "  Dev@EXAMPLE.COM  ",
        "password": "RiverStone42",
    }
)

    assert request.username == "DevTheMapper"
    assert request.email == "Dev@example.com"
    assert (
        request.password.get_secret_value()
        == "RiverStone42"
    )


def test_registration_password_is_masked() -> None:
    """Password values should not appear in normal model output."""

    request = RegisterRequest.model_validate(
    {
        "username": "  DevTheMapper  ",
        "email": "  Dev@EXAMPLE.COM  ",
        "password": "RiverStone42",
    }
)

    assert "RiverStone42" not in repr(request)
    assert "RiverStone42" not in request.model_dump_json()
    assert "**********" in request.model_dump_json()


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("username", "Dev Mapper"),
        ("email", "not-an-email"),
        ("password", "too-short"),
    ],
)
def test_registration_rejects_invalid_fields(
    field_name: str,
    invalid_value: str,
) -> None:
    """Invalid registration fields should fail validation."""

    payload = {
        "username": "DevTheMapper",
        "email": "dev@example.com",
        "password": "RiverStone42",
    }
    payload[field_name] = invalid_value

    with pytest.raises(ValidationError):
        RegisterRequest.model_validate(payload)


def test_registration_rejects_extra_fields() -> None:
    """Unknown registration properties should be rejected."""

    with pytest.raises(ValidationError):
        RegisterRequest.model_validate(
        {
            "username": "DevTheMapper",
            "email": "dev@example.com",
            "password": "RiverStone42",
            "is_admin": True,
        }
    )


def test_login_cleans_identifier_but_not_password() -> None:
    """Password whitespace must remain part of the password."""

    request = LoginRequest.model_validate(
    {
        "identifier": "  DevTheMapper  ",
        "password": "  RiverStone42  ",
    }
)

    assert request.identifier == "DevTheMapper"
    assert (
        request.password.get_secret_value()
        == "  RiverStone42  "
    )


def test_change_password_validates_only_new_policy() -> None:
    """The replacement password must satisfy current rules."""

    request = ChangePasswordRequest.model_validate(
    {
        "current_password": "old-value",
        "new_password": "NewRiverStone42",
    }
)

    assert (
        request.current_password.get_secret_value()
        == "old-value"
    )

    with pytest.raises(ValidationError):
        ChangePasswordRequest.model_validate(
        {
            "current_password": "old-value",
            "new_password": "short",
        }
    )


def test_user_response_excludes_sensitive_fields() -> None:
    """The public user schema should expose safe fields only."""

    now = datetime.now(UTC)

    database_user = SimpleNamespace(
        id=uuid4(),
        username="DevTheMapper",
        email="dev@example.com",
        password_hash="never-return-this",
        username_normalized="devthemapper",
        email_normalized="dev@example.com",
        created_at=now,
        updated_at=now,
        sessions=[],
    )

    response = UserResponse.model_validate(database_user)
    response_data = response.model_dump()

    assert response_data["username"] == "DevTheMapper"
    assert response_data["email"] == "dev@example.com"
    assert "password_hash" not in response_data
    assert "username_normalized" not in response_data
    assert "email_normalized" not in response_data
    assert "sessions" not in response_data