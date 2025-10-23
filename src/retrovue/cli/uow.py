"""
Unit of Work (UoW) for CLI operations.

This module provides database session management for CLI operations,
mirroring the get_db() semantics with proper commit/rollback handling.
"""

from __future__ import annotations

import contextlib
from typing import Generator

from sqlalchemy.orm import Session

from ..infra.db import SessionLocal


@contextlib.contextmanager
def session() -> Generator[Session, None, None]:
    """
    Database session context manager for CLI operations.
    
    Mirrors get_db() semantics:
    - Commits on success
    - Rolls back on error
    - Ensures session is closed
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

