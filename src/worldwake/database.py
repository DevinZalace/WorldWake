"""Database configuration and request-scoped SQLAlchemy sessions."""

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
DEFAULT_DATABASE_PATH = DATA_DIRECTORY / "worldwake.db"
DEFAULT_DATABASE_URL = (
    f"sqlite+pysqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
)

DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


def create_database_engine(database_url: str) -> Engine:
    """Create a configured SQLAlchemy engine for a database URL."""

    engine_options: dict[str, object] = {}

    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {
            "check_same_thread": False,
        }

    database_engine = create_engine(
        database_url,
        **engine_options,
    )

    if database_url.startswith("sqlite"):

        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(
            dbapi_connection,
            _connection_record,
        ) -> None:
            """Enforce declared foreign-key constraints in SQLite."""

            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


def create_session_factory(
    database_engine: Engine,
) -> sessionmaker[Session]:
    """Create consistently configured SQLAlchemy sessions."""

    return sessionmaker(
        bind=database_engine,
        autoflush=False,
        expire_on_commit=False,
    )


engine = create_database_engine(DATABASE_URL)
SessionFactory = create_session_factory(engine)


def get_database_session() -> Iterator[Session]:
    """Provide one managed database session for an application request."""

    session = SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()