"""Database connection and session management with PostgreSQL/SQLite fallback."""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Global flag to track database mode
_db_mode = None  # Will be set to "postgresql" or "sqlite"
_engine = None
SessionLocal = None


def _test_postgresql_connection():
    """Test if PostgreSQL is available."""
    try:
        test_engine = create_engine(
            settings.sqlalchemy_database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
            connect_args={"timeout": 5},
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ PostgreSQL connection successful")
        return True
    except (OperationalError, Exception) as e:
        logger.warning(f"✗ PostgreSQL unavailable: {type(e).__name__}")
        return False


def _init_database():
    """Initialize database connection (PostgreSQL or SQLite fallback)."""
    global _db_mode, _engine, SessionLocal

    if _engine is not None:
        return _db_mode  # Already initialized

    # Try PostgreSQL first
    if _test_postgresql_connection():
        _db_mode = "postgresql"
        _engine = create_engine(
            settings.sqlalchemy_database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )
    else:
        # Fall back to SQLite
        logger.info("Falling back to SQLite local cache...")
        from app.core.local_data import ensure_data_available, CACHE_DB
        ensure_data_available()

        _db_mode = "sqlite"
        _engine = create_engine(
            f"sqlite:///{CACHE_DB}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    logger.info(f"Database mode: {_db_mode}")
    return _db_mode


def get_db_mode():
    """Get current database mode (postgresql or sqlite)."""
    if _db_mode is None:
        _init_database()
    return _db_mode


def get_engine():
    """Get SQLAlchemy engine."""
    if _engine is None:
        _init_database()
    return _engine


def get_session():
    """Get database session factory."""
    if SessionLocal is None:
        _init_database()
    return SessionLocal


def get_db() -> Session:
    """Get database session."""
    _session_factory = get_session()
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from app.core.models import Base
    engine = get_engine()
    if get_db_mode() == "postgresql":
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("SQLite cache already initialized via local_data.py")


def reset_db() -> None:
    """Drop all tables and recreate (PostgreSQL only)."""
    if get_db_mode() != "postgresql":
        logger.warning("Reset only supported for PostgreSQL mode")
        return

    from app.core.models import Base
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
