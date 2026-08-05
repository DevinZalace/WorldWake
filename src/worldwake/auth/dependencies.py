"""FastAPI dependencies for database and account access."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from worldwake.auth.cookies import SESSION_COOKIE_NAME
from worldwake.auth.sessions import find_active_auth_session
from worldwake.database import get_database_session
from worldwake.models import AuthSession, User


AUTHENTICATION_REQUIRED_MESSAGE = (
    "Authentication required."
)


DatabaseSession = Annotated[
    Session,
    Depends(
        get_database_session,
        scope="function",
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


def require_current_user(
    auth_session: CurrentAuthSession,
) -> User:
    """Return the user owning the active browser session."""

    return auth_session.user


CurrentUser = Annotated[
    User,
    Depends(require_current_user),
]