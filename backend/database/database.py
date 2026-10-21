"""
SQLAlchemy engine and session management.

Uses SQLite with WAL mode for concurrent read/write support.
Tables are created automatically on first startup via init_db().
"""

import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from backend.config import config

logger = logging.getLogger(__name__)

# SQLAlchemy engine — single connection pool for the entire app
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine (singleton)."""
    global _engine
    if _engine is None:
        db_url = f"sqlite:///{config.DB_PATH}"
        _engine = create_engine(
            db_url,
            echo=config.DB_ECHO,
            connect_args={"check_same_thread": False},  # needed for FastAPI threads
        )
        # Enable WAL mode for better concurrent access
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("Database engine created: %s", config.DB_PATH)
    return _engine


def get_session_factory():
    """Get or create the session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


def get_session() -> Session:
    """Create a new database session. Caller must close it."""
    factory = get_session_factory()
    return factory()


@contextmanager
def session_scope():
    """Context manager that provides a transactional session.

    Usage:
        with session_scope() as session:
            session.query(Article).all()
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create all tables defined by the ORM models.

    Called once on application startup. Safe to call multiple times —
    create_all() is a no-op if tables already exist.
    """
    from backend.database.models import Base  # import here to avoid circular deps

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
