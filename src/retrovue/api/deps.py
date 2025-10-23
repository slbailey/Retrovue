from typing import Generator
from retrovue.infra.db import SessionLocal

def get_db() -> Generator:
    """
    Provide a Session per-request with a unit-of-work:
    - success => commit once
    - error => rollback
    - always close
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