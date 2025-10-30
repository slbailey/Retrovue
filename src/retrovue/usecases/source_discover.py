from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..domain.entities import Source


def discover_collections(db: Session, *, source_id: str) -> List[Dict[str, Any]]:
    """
    Discover collections from a Source. Single operation; no persistence.
    """
    source = db.query(Source).filter(Source.external_id == source_id).first() or db.query(Source).filter(Source.id == source_id).first() or db.query(Source).filter(Source.name == source_id).first()
    if not source:
        raise ValueError(f"Source not found: {source_id}")

    # This is a placeholder; actual importer-based discovery belongs in adapters
    # For contract alignment, return an empty list when not implemented.
    return []



__all__ = ["discover_collections"]