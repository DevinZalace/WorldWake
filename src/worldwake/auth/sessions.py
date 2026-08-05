"""Secure authentication-token and session creation."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from sqlalchemy.orm import Session

from worldwake.models import AuthSession, User


TOKEN_ENTROPY_BYTES = 32
SESSION_LIFETIME = timedelta(days=30)


@dataclass(frozen=True, slots=True)
class IssuedAuthSession:
    """A stored session record and its temporary raw credentials."""

    record: AuthSession
    session_token: str
    csrf_token: str


def generate_opaque_token() -> str:
    """Generate a cryptographically secure URL-safe token."""

    return secrets.token_urlsafe(TOKEN_ENTROPY_BYTES)


def hash_token(token: str) -> str:
    """Create the SHA-256 hexadecimal digest stored by WorldWake."""

    return sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_auth_session(
    database_session: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> IssuedAuthSession:
    """Create a revocable session without committing the transaction."""

    created_at = now or datetime.now(UTC)

    session_token = generate_opaque_token()
    csrf_token = generate_opaque_token()

    auth_session = AuthSession(
        user=user,
        token_hash=hash_token(session_token),
        csrf_token_hash=hash_token(csrf_token),
        created_at=created_at,
        last_used_at=created_at,
        expires_at=created_at + SESSION_LIFETIME,
    )

    database_session.add(auth_session)
    database_session.flush()

    return IssuedAuthSession(
        record=auth_session,
        session_token=session_token,
        csrf_token=csrf_token,
    )