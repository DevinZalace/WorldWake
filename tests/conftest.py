"""Shared Pytest fixtures for isolated WorldWake tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from worldwake.database import (
    create_database_engine,
    create_session_factory,
)
from worldwake.models import Base


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