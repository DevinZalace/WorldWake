"""Rate limiting for WorldWake authentication endpoints."""

from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
from math import ceil
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status


RATE_LIMIT_MESSAGE = (
    "Too many attempts. Try again later."
)

REGISTER_IP_LIMIT = 10
REGISTER_WINDOW_SECONDS = 60 * 60

LOGIN_IP_LIMIT = 30
LOGIN_IDENTIFIER_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60

MAX_RATE_LIMIT_KEYS = 10_000


@dataclass(slots=True)
class _RateLimitWindow:
    """Mutable attempt count for one fixed time window."""

    count: int
    expires_at: float


class RateLimitExceeded(Exception):
    """Raised when a rate-limit window has no attempts remaining."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(RATE_LIMIT_MESSAGE)

        self.retry_after = retry_after


class InMemoryRateLimiter:
    """Thread-safe, bounded fixed-window rate limiter."""

    def __init__(
        self,
        *,
        max_keys: int = MAX_RATE_LIMIT_KEYS,
    ) -> None:
        if max_keys < 1:
            raise ValueError(
                "max_keys must be at least 1."
            )

        self._max_keys = max_keys
        self._windows: OrderedDict[
            str,
            _RateLimitWindow,
        ] = OrderedDict()
        self._lock = Lock()

    def consume(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> None:
        """Consume one attempt or raise a rate-limit error."""

        if limit < 1:
            raise ValueError(
                "limit must be at least 1."
            )

        if window_seconds < 1:
            raise ValueError(
                "window_seconds must be at least 1."
            )

        current_time = (
            monotonic()
            if now is None
            else now
        )

        with self._lock:
            window = self._windows.get(key)

            if (
                window is None
                or current_time >= window.expires_at
            ):
                self._windows.pop(key, None)

                while (
                    len(self._windows)
                    >= self._max_keys
                ):
                    self._windows.popitem(
                        last=False
                    )

                self._windows[key] = (
                    _RateLimitWindow(
                        count=1,
                        expires_at=(
                            current_time
                            + window_seconds
                        ),
                    )
                )

                return

            self._windows.move_to_end(key)

            if window.count >= limit:
                retry_after = max(
                    1,
                    ceil(
                        window.expires_at
                        - current_time
                    ),
                )

                raise RateLimitExceeded(
                    retry_after
                )

            window.count += 1

    def clear(self, key: str) -> None:
        """Remove one tracked rate-limit window."""

        with self._lock:
            self._windows.pop(key, None)

    def clear_all(self) -> None:
        """Remove every tracked rate-limit window."""

        with self._lock:
            self._windows.clear()


def build_rate_limit_key(
    namespace: str,
    *parts: str,
) -> str:
    """Build a non-readable rate-limit storage key."""

    raw_key = "\x1f".join(
        (namespace, *parts)
    )

    return sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


def get_client_address(
    request: Request,
) -> str:
    """Return the direct client address for rate limiting."""

    if request.client is None:
        return "unknown"

    return request.client.host


auth_rate_limiter = InMemoryRateLimiter()


def get_auth_rate_limiter() -> InMemoryRateLimiter:
    """Return the application's authentication limiter."""

    return auth_rate_limiter


AuthRateLimiter = Annotated[
    InMemoryRateLimiter,
    Depends(get_auth_rate_limiter),
]


def enforce_registration_rate_limit(
    request: Request,
    rate_limiter: InMemoryRateLimiter,
) -> None:
    """Consume one registration attempt for this client."""

    client_address = get_client_address(
        request
    )

    key = build_rate_limit_key(
        "register-ip",
        client_address,
    )

    rate_limiter.consume(
        key,
        limit=REGISTER_IP_LIMIT,
        window_seconds=(
            REGISTER_WINDOW_SECONDS
        ),
    )


def enforce_login_rate_limit(
    request: Request,
    identifier: str,
    rate_limiter: InMemoryRateLimiter,
) -> str:
    """Consume login limits and return the identifier key."""

    client_address = get_client_address(
        request
    )
    normalized_identifier = (
        identifier.strip().casefold()
    )

    client_key = build_rate_limit_key(
        "login-ip",
        client_address,
    )
    identifier_key = build_rate_limit_key(
        "login-ip-identifier",
        client_address,
        normalized_identifier,
    )

    rate_limiter.consume(
        client_key,
        limit=LOGIN_IP_LIMIT,
        window_seconds=LOGIN_WINDOW_SECONDS,
    )
    rate_limiter.consume(
        identifier_key,
        limit=LOGIN_IDENTIFIER_LIMIT,
        window_seconds=LOGIN_WINDOW_SECONDS,
    )

    return identifier_key


def build_rate_limit_http_exception(
    error: RateLimitExceeded,
) -> HTTPException:
    """Convert a rate-limit failure into an HTTP response."""

    return HTTPException(
        status_code=(
            status.HTTP_429_TOO_MANY_REQUESTS
        ),
        detail=RATE_LIMIT_MESSAGE,
        headers={
            "Retry-After": str(
                error.retry_after
            ),
        },
    )