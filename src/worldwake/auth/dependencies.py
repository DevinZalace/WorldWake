"""FastAPI dependencies for database and account access."""

from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from hmac import compare_digest

from worldwake.auth.cookies import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
)
from worldwake.auth.sessions import (
    find_active_auth_session,
    hash_token,
)
from worldwake.database import get_database_session
from worldwake.models import AuthSession, User



AUTHENTICATION_REQUIRED_MESSAGE = (
    "Authentication required."
)

CSRF_VALIDATION_MESSAGE = (
    "CSRF validation failed."
)


DatabaseSession = Annotated[
    Session,
    Depends(
        get_database_session,
        scope="function",
    ),
]

CsrfCookie = Annotated[
    str | None,
    Cookie(
        alias=CSRF_COOKIE_NAME,
    ),
]

CsrfHeader = Annotated[
    str | None,
    Header(
        alias=CSRF_HEADER_NAME,
    ),
]

SessionCookie = Annotated[
    str | None,
    Cookie(
        alias=SESSION_COOKIE_NAME,
    ),
]

def require_auth_session(
    database_session: DatabaseSession,
    session_token: SessionCookie = None,
) -> AuthSession:
    """Return the active session or reject the request."""

    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTHENTICATION_REQUIRED_MESSAGE,
        )

    auth_session = find_active_auth_session(
        database_session,
        session_token,
    )

    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTHENTICATION_REQUIRED_MESSAGE,
        )

    return auth_session


CurrentAuthSession = Annotated[
    AuthSession,
    Depends(require_auth_session),
]

def require_csrf_protection(
    auth_session: CurrentAuthSession,
    csrf_cookie: CsrfCookie = None,
    csrf_header: CsrfHeader = None,
) -> AuthSession:
    """Require matching CSRF credentials for an authenticated write."""

    if csrf_cookie is None or csrf_header is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CSRF_VALIDATION_MESSAGE,
        )

    if not compare_digest(
        csrf_cookie,
        csrf_header,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CSRF_VALIDATION_MESSAGE,
        )

    submitted_csrf_hash = hash_token(
        csrf_header
    )

    if not compare_digest(
        submitted_csrf_hash,
        auth_session.csrf_token_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CSRF_VALIDATION_MESSAGE,
        )

    return auth_session


CsrfProtectedSession = Annotated[
    AuthSession,
    Depends(require_csrf_protection),
]


def require_current_user(
    auth_session: CurrentAuthSession,
) -> User:
    """Return the user owning the active browser session."""

    return auth_session.user


CurrentUser = Annotated[
    User,
    Depends(require_current_user),
]