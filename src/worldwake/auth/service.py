"""Account creation and lookup services."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from worldwake.auth.identities import (
    IdentityValidationError,
    prepare_email,
    prepare_username,
)
from worldwake.auth.passwords import (
    hash_password,
    password_hash_needs_rehash,
    rehash_verified_password,
    verify_password,
)
from worldwake.auth.schemas import (
    LoginRequest,
    RegisterRequest,
)
from worldwake.models import User


ACCOUNT_CONFLICT_MESSAGE = (
    "Unable to create an account with those details."
)

INVALID_CREDENTIALS_MESSAGE = (
    "Invalid username, email, or password."
)


_DUMMY_PASSWORD_HASH = hash_password(
    "WorldWakeTimingEqualizer42"
)


class AccountConflictError(Exception):
    """Raised when registration conflicts with an existing account."""

class InvalidCredentialsError(Exception):
    """Raised when login credentials cannot be authenticated."""


def register_user(
    database_session: Session,
    registration: RegisterRequest,
) -> User:
    """Create a user without committing the surrounding transaction."""

    username = prepare_username(registration.username)
    email = prepare_email(registration.email)

    existing_user_id = database_session.scalar(
        select(User.id)
        .where(
            or_(
                User.username_normalized
                == username.normalized,
                User.email_normalized
                == email.normalized,
            )
        )
        .limit(1)
    )

    if existing_user_id is not None:
        raise AccountConflictError(
            ACCOUNT_CONFLICT_MESSAGE
        )

    user = User(
        username=username.value,
        username_normalized=username.normalized,
        email=email.value,
        email_normalized=email.normalized,
        password_hash=hash_password(
            registration.password.get_secret_value()
        ),
    )

    database_session.add(user)

    try:
        database_session.flush()
    except IntegrityError as error:
        raise AccountConflictError(
            ACCOUNT_CONFLICT_MESSAGE
        ) from error

    return user

def find_user_by_identifier(
    database_session: Session,
    identifier: str,
) -> User | None:
    """Find a user by normalized username or email."""

    cleaned_identifier = identifier.strip()

    try:
        if "@" in cleaned_identifier:
            normalized_identifier = prepare_email(
                cleaned_identifier
            ).normalized

            lookup_condition = (
                User.email_normalized
                == normalized_identifier
            )
        else:
            normalized_identifier = prepare_username(
                cleaned_identifier
            ).normalized

            lookup_condition = (
                User.username_normalized
                == normalized_identifier
            )
    except IdentityValidationError:
        return None

    return database_session.scalar(
        select(User)
        .where(lookup_condition)
        .limit(1)
    )


def authenticate_user(
    database_session: Session,
    login: LoginRequest,
) -> User:
    """Authenticate a username-or-email login request."""

    submitted_password = (
        login.password.get_secret_value()
    )

    user = find_user_by_identifier(
        database_session,
        login.identifier,
    )

    if user is None:
        verify_password(
            _DUMMY_PASSWORD_HASH,
            submitted_password,
        )

        raise InvalidCredentialsError(
            INVALID_CREDENTIALS_MESSAGE
        )

    if not verify_password(
        user.password_hash,
        submitted_password,
    ):
        raise InvalidCredentialsError(
            INVALID_CREDENTIALS_MESSAGE
        )

    if password_hash_needs_rehash(
        user.password_hash
    ):
        user.password_hash = (
            rehash_verified_password(
                submitted_password
            )
        )

        database_session.flush()

    return user