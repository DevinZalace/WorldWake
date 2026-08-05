"""Database configuration and request-scoped SQLAlchemy sessions."""

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
DEFAULT_DATABASE_PATH = DATA_DIRECTORY / "worldwake.db"
DEFAULT_DATABASE_URL = (
    f"sqlite+pysqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
)

DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


ENGINE_OPTIONS: dict[str, object] = {}

if DATABASE_URL.startswith("sqlite"):
    ENGINE_OPTIONS["connect_args"] = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    **ENGINE_OPTIONS,
)

if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        _connection_record,
    ) -> None:
        """Enforce declared foreign-key constraints in SQLite."""

        previous_autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        dbapi_connection.autocommit = previous_autocommit


SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


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