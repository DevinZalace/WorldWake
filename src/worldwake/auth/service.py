"""Account creation and lookup services."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from worldwake.auth.identities import (
    prepare_email,
    prepare_username,
)
from worldwake.auth.passwords import hash_password
from worldwake.auth.schemas import RegisterRequest
from worldwake.models import User


ACCOUNT_CONFLICT_MESSAGE = (
    "Unable to create an account with those details."
)


class AccountConflictError(Exception):
    """Raised when registration conflicts with an existing account."""


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