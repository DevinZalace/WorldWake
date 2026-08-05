"""Shared Pytest fixtures for isolated WorldWake tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from worldwake.database import get_database_session
from worldwake.main import app

from worldwake.database import (
    create_database_engine,
    create_session_factory,
)
from worldwake.models import Base

from worldwake.auth.rate_limits import (
    InMemoryRateLimiter,
    get_auth_rate_limiter,
)



@pytest.fixture
def test_engine(
    tmp_path: Path,
) -> Iterator[Engine]:
    """Create a temporary SQLite database for one test."""

    database_path = tmp_path / "test_worldwake.db"
    database_url = (
        f"sqlite+pysqlite:///{database_path.as_posix()}"
    )

    engine = create_database_engine(database_url)

    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_session_factory(
    test_engine: Engine,
) -> sessionmaker[Session]:
    """Create sessions connected to the temporary database."""

    return create_session_factory(test_engine)


@pytest.fixture
def database_session(
    test_session_factory: sessionmaker[Session],
) -> Iterator[Session]:
    """Provide one temporary database session to a test."""

    session = test_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def api_client(
    test_session_factory: sessionmaker[Session],
) -> Iterator[TestClient]:
    """Run the FastAPI application against a temporary database."""

    test_rate_limiter = InMemoryRateLimiter()

    def override_database_session() -> Iterator[Session]:
        session = test_session_factory()

        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[
        get_database_session
    ] = override_database_session
    app.dependency_overrides[
        get_auth_rate_limiter
    ] = lambda: test_rate_limiter

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(
            get_database_session,
            None,
        )
        app.dependency_overrides.pop(
            get_auth_rate_limiter,
            None,
        )