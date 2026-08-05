"""Authentication cookie configuration and response helpers."""

import os

from fastapi import Response

from worldwake.auth.sessions import (
    SESSION_LIFETIME,
    IssuedAuthSession,
)


SESSION_COOKIE_NAME = "ww_session"
CSRF_COOKIE_NAME = "ww_csrf"

COOKIE_PATH = "/"
COOKIE_SAME_SITE = "lax"

COOKIE_MAX_AGE_SECONDS = int(
    SESSION_LIFETIME.total_seconds()
)

SECURE_COOKIE_ENVIRONMENT_VARIABLE = (
    "WORLDWAKE_COOKIE_SECURE"
)


def secure_cookies_enabled() -> bool:
    """Return whether authentication cookies require HTTPS."""

    configured_value = os.getenv(
        SECURE_COOKIE_ENVIRONMENT_VARIABLE,
        "",
    )

    return configured_value.strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def set_authentication_cookies(
    response: Response,
    issued_session: IssuedAuthSession,
) -> None:
    """Attach session and CSRF cookies to an HTTP response."""

    cookie_secure = secure_cookies_enabled()
    expires_at = issued_session.record.expires_at

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=issued_session.session_token,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=expires_at,
        path=COOKIE_PATH,
        secure=cookie_secure,
        httponly=True,
        samesite=COOKIE_SAME_SITE,
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=issued_session.csrf_token,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=expires_at,
        path=COOKIE_PATH,
        secure=cookie_secure,
        httponly=False,
        samesite=COOKIE_SAME_SITE,
    )