"""Password validation, hashing, and verification."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128


password_hasher = PasswordHasher()


class PasswordValidationError(ValueError):
    """Raised when a password violates WorldWake's password policy."""


def validate_password(password: str) -> None:
    """Ensure a password satisfies WorldWake's length requirements."""

    password_length = len(password)

    if password_length < MIN_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    if password_length > MAX_PASSWORD_LENGTH:
        raise PasswordValidationError(
            f"Password must contain no more than "
            f"{MAX_PASSWORD_LENGTH} characters."
        )


def hash_password(password: str) -> str:
    """Validate and securely hash a password using Argon2id."""

    validate_password(password)

    return password_hasher.hash(password)


def verify_password(
    password_hash: str,
    submitted_password: str,
) -> bool:
    """Return whether a submitted password matches an encoded hash."""

    try:
        return password_hasher.verify(
            password_hash,
            submitted_password,
        )
    except (VerificationError, InvalidHashError):
        return False


def password_hash_needs_rehash(password_hash: str) -> bool:
    """Return whether a stored hash should use newer parameters."""

    try:
        return password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True

    