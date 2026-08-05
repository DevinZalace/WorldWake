"""Secure authentication-token and session creation."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from sqlalchemy.orm import Session
from worldwake.models import AuthSession, User
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload


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

def ensure_utc(value: datetime) -> datetime:
    """Return a datetime interpreted or converted to UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def find_active_auth_session(
    database_session: Session,
    session_token: str,
    *,
    now: datetime | None = None,
) -> AuthSession | None:
    """Find and refresh a valid authentication session."""

    current_time = ensure_utc(
        now or datetime.now(UTC)
    )

    auth_session = database_session.scalar(
        select(AuthSession)
        .options(
            joinedload(AuthSession.user)
        )
        .where(
            AuthSession.token_hash
            == hash_token(session_token)
        )
    )

    if auth_session is None:
        return None

    if auth_session.revoked_at is not None:
        return None

    expires_at = ensure_utc(
        auth_session.expires_at
    )

    if expires_at <= current_time:
        return None

    auth_session.last_used_at = current_time

    return auth_session

def revoke_auth_session(
    auth_session: AuthSession,
    *,
    now: datetime | None = None,
) -> None:
    """Mark an authentication session as permanently revoked."""

    auth_session.revoked_at = ensure_utc(
        now or datetime.now(UTC)
    )

def revoke_all_auth_sessions(
    database_session: Session,
    user_id: UUID,
    *,
    now: datetime | None = None,
) -> int:
    """Revoke every currently active session belonging to a user."""

    revocation_time = ensure_utc(
        now or datetime.now(UTC)
    )

    active_sessions = database_session.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )
    ).all()

    for auth_session in active_sessions:
        auth_session.revoked_at = revocation_time

    database_session.flush()

    return len(active_sessions)

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