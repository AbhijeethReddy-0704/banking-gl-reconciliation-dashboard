"""Configuration management for the application."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = "postgresql://postgres:password@localhost:5432/banking_db"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "banking_db"
    db_user: str = "postgres"
    db_password: str = "password"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"

    num_customers: int = 25000
    num_accounts: int = 40000
    num_transactions: int = 500000
    num_gl_entries: int = 500000
    data_months: int = 12
    seed: int = 42

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return SQLAlchemy database URL."""
        return self.database_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
