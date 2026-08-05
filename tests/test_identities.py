"""Tests for username and email preparation."""

import pytest

from worldwake.auth import (
    MAX_USERNAME_LENGTH,
    MIN_USERNAME_LENGTH,
    IdentityValidationError,
    prepare_email,
    prepare_username,
)


def test_prepare_username_preserves_display_case() -> None:
    """Username display casing should be preserved."""

    identity = prepare_username("  DevTheMapper  ")

    assert identity.value == "DevTheMapper"
    assert identity.normalized == "devthemapper"


@pytest.mark.parametrize(
    "username",
    [
        "Dev",
        "MapMaker42",
        "north-watch",
        "world_waker",
    ],
)
def test_prepare_username_accepts_allowed_characters(
    username: str,
) -> None:
    """Supported username characters should be accepted."""

    identity = prepare_username(username)

    assert identity.value == username


@pytest.mark.parametrize(
    "username",
    [
        "x" * (MIN_USERNAME_LENGTH - 1),
        "x" * (MAX_USERNAME_LENGTH + 1),
        "Dev Zalace",
        "Dev!",
        "Map.Maker",
    ],
)
def test_prepare_username_rejects_invalid_values(
    username: str,
) -> None:
    """Invalid lengths and characters should be rejected."""

    with pytest.raises(IdentityValidationError):
        prepare_username(username)


def test_username_normalization_is_case_insensitive() -> None:
    """Equivalent username casing should create one lookup value."""

    first = prepare_username("WorldWaker")
    second = prepare_username("WORLDWAKER")

    assert first.normalized == second.normalized


def test_prepare_email_normalizes_address() -> None:
    """A valid email should receive a stable stored representation."""

    identity = prepare_email("  Dev@EXAMPLE.COM  ")

    assert identity.value == "Dev@example.com"
    assert identity.normalized == "dev@example.com"


def test_email_normalization_is_case_insensitive() -> None:
    """Equivalent email casing should create one lookup value."""

    first = prepare_email("Dev@example.com")
    second = prepare_email("DEV@EXAMPLE.COM")

    assert first.normalized == second.normalized


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "missing-domain@",
        "@example.com",
        "spaces are bad@example.com",
        "",
    ],
)
def test_prepare_email_rejects_invalid_addresses(
    email: str,
) -> None:
    """Malformed email addresses should be rejected safely."""

    with pytest.raises(
        IdentityValidationError,
        match="Enter a valid email address",
    ):
        prepare_email(email)