"""Pytest configuration and fixtures."""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.models import Base
from app.core.database import get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create in-memory test database before tests run."""
    # Use SQLite in-memory for tests
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # Create engine and tables
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override get_db dependency
    def override_get_db():
        try:
            db = TestSessionLocal()
            yield db
        finally:
            db.close()

    from app.api.main import app
    app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup
    Base.metadata.drop_all(bind=engine)
