"""Username and email validation and normalization."""

import re
from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email


MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 30

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class IdentityValidationError(ValueError):
    """Raised when a username or email is not acceptable."""


@dataclass(frozen=True, slots=True)
class PreparedIdentity:
    """A validated identity value and its lookup representation."""

    value: str
    normalized: str


def prepare_username(username: str) -> PreparedIdentity:
    """Validate a username and create its case-insensitive form."""

    cleaned_username = username.strip()

    if len(cleaned_username) < MIN_USERNAME_LENGTH:
        raise IdentityValidationError(
            f"Username must contain at least "
            f"{MIN_USERNAME_LENGTH} characters."
        )

    if len(cleaned_username) > MAX_USERNAME_LENGTH:
        raise IdentityValidationError(
            f"Username must contain no more than "
            f"{MAX_USERNAME_LENGTH} characters."
        )

    if USERNAME_PATTERN.fullmatch(cleaned_username) is None:
        raise IdentityValidationError(
            "Username may contain only letters, numbers, "
            "underscores, and hyphens."
        )

    return PreparedIdentity(
        value=cleaned_username,
        normalized=cleaned_username.casefold(),
    )


def prepare_email(email: str) -> PreparedIdentity:
    """Validate an email and create its case-insensitive form."""

    cleaned_email = email.strip()

    try:
        validated_email = validate_email(
            cleaned_email,
            check_deliverability=False,
        )
    except EmailNotValidError as error:
        raise IdentityValidationError(
            "Enter a valid email address."
        ) from error

    normalized_email = validated_email.normalized

    return PreparedIdentity(
        value=normalized_email,
        normalized=normalized_email.casefold(),
    )