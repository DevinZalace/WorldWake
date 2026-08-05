"""Tests for WorldWake password handling."""

import pytest

from worldwake.auth import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordValidationError,
    hash_password,
    password_hash_needs_rehash,
    verify_password,
    rehash_verified_password,
)


def test_hash_password_creates_argon2id_hash() -> None:
    """A valid password should become a usable Argon2id hash."""

    password = "RiverStone42"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")
    assert verify_password(password_hash, password) is True


def test_verify_password_rejects_incorrect_password() -> None:
    """An incorrect password should fail without raising an exception."""

    password_hash = hash_password("RiverStone42")

    assert verify_password(
        password_hash,
        "EntirelyWrong42",
    ) is False


def test_same_password_produces_different_hashes() -> None:
    """Fresh salts should make repeated hashes different."""

    password = "RiverStone42"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(first_hash, password) is True
    assert verify_password(second_hash, password) is True


@pytest.mark.parametrize(
    "password",
    [
        "x" * (MIN_PASSWORD_LENGTH - 1),
        "x" * (MAX_PASSWORD_LENGTH + 1),
    ],
)
def test_hash_password_rejects_invalid_lengths(
    password: str,
) -> None:
    """Passwords outside the accepted range should be rejected."""

    with pytest.raises(PasswordValidationError):
        hash_password(password)


def test_current_hash_does_not_need_rehash() -> None:
    """A newly created hash should use the current parameters."""

    password_hash = hash_password("RiverStone42")

    assert password_hash_needs_rehash(password_hash) is False


def test_malformed_hash_is_rejected_safely() -> None:
    """Malformed stored data should not crash password verification."""

    malformed_hash = "this-is-not-an-argon2-hash"

    assert verify_password(
        malformed_hash,
        "RiverStone42",
    ) is False

    assert password_hash_needs_rehash(malformed_hash) is True

    def test_rehash_verified_password_accepts_legacy_length() -> None:
        """A verified legacy password may be rehashed under new parameters."""

    legacy_password = "old-short"

    password_hash = rehash_verified_password(
        legacy_password
    )

    assert verify_password(
        password_hash,
        legacy_password,
    ) is True