"""Tests for authentication rate limiting."""

import pytest

from worldwake.auth.rate_limits import (
    InMemoryRateLimiter,
    RateLimitExceeded,
    build_rate_limit_key,
)


def test_limiter_allows_configured_attempt_count() -> None:
    """The configured number of attempts should be accepted."""

    limiter = InMemoryRateLimiter()

    for _ in range(3):
        limiter.consume(
            "example-key",
            limit=3,
            window_seconds=60,
            now=100.0,
        )


def test_limiter_blocks_attempt_beyond_limit() -> None:
    """The next attempt should include a retry duration."""

    limiter = InMemoryRateLimiter()

    for _ in range(3):
        limiter.consume(
            "example-key",
            limit=3,
            window_seconds=60,
            now=100.0,
        )

    with pytest.raises(
        RateLimitExceeded
    ) as error:
        limiter.consume(
            "example-key",
            limit=3,
            window_seconds=60,
            now=101.0,
        )

    assert error.value.retry_after == 59


def test_limiter_starts_fresh_after_window_expires() -> None:
    """An expired window should allow a new attempt."""

    limiter = InMemoryRateLimiter()

    limiter.consume(
        "example-key",
        limit=1,
        window_seconds=60,
        now=100.0,
    )

    with pytest.raises(RateLimitExceeded):
        limiter.consume(
            "example-key",
            limit=1,
            window_seconds=60,
            now=120.0,
        )

    limiter.consume(
        "example-key",
        limit=1,
        window_seconds=60,
        now=160.0,
    )


def test_clear_removes_existing_window() -> None:
    """A successful login may clear its identifier limit."""

    limiter = InMemoryRateLimiter()

    limiter.consume(
        "example-key",
        limit=1,
        window_seconds=60,
        now=100.0,
    )

    limiter.clear("example-key")

    limiter.consume(
        "example-key",
        limit=1,
        window_seconds=60,
        now=101.0,
    )


def test_rate_limit_key_hides_raw_values() -> None:
    """Stored keys should not expose identity information."""

    email = "dev@example.com"

    key = build_rate_limit_key(
        "login",
        "127.0.0.1",
        email,
    )

    assert email not in key
    assert "127.0.0.1" not in key
    assert len(key) == 64