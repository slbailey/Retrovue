"""
Application settings for Retrovue.

This module defines all configuration settings for Retrovue using Pydantic BaseSettings.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings using Pydantic BaseSettings."""
    
    # Database settings (keep existing)
    database_url: str = Field(default="postgresql+psycopg://retrovue:retrovue@localhost:5432/retrovue", alias="DATABASE_URL")
    echo_sql: bool = Field(default=False, alias="ECHO_SQL")
    pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    
    # New settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    media_roots: str = Field(default="", alias="MEDIA_ROOTS")  # Comma-separated paths
    plex_token: str = Field(default="", alias="PLEX_TOKEN")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")  # Comma-separated origins
    env: str = Field(default="dev", alias="ENV")  # dev|prod|test

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
