from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..domain.entities import Collection, Enricher


def _resolve_collection(db: Session, selector: str) -> Collection:
    """Resolve a collection by UUID, external_id, or case-insensitive name.

    Raises ValueError when not found or ambiguous by name.
    """
    # Try UUID (exact)
    try:
        import uuid as _uuid

        _uuid.UUID(selector)
        col = db.query(Collection).filter(Collection.uuid == selector).first()
        if col:
            return col
    except Exception:
        pass

    # Try external_id (exact)
    col = db.query(Collection).filter(Collection.external_id == selector).first()
    if col:
        return col

    # Try name (case-insensitive, single match)
    matches = db.query(Collection).filter(Collection.name.ilike(selector)).all()
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"Multiple collections named '{selector}' exist. Please specify the UUID."
        )
    raise ValueError(f"Collection '{selector}' not found")


def _validate_enricher_exists(db: Session, enricher_id: str) -> None:
    """Validate an enricher exists by its enricher_id."""
    exists = (
        db.query(Enricher).filter(Enricher.enricher_id == enricher_id).first() is not None
    )
    if not exists:
        raise ValueError(f"Enricher not found: {enricher_id}")


def attach_enricher_to_collection(
    db: Session, *, collection_selector: str, enricher_id: str, priority: int
) -> dict[str, Any]:
    """Attach or update an enricher attachment on a collection.

    - Validates collection and enricher
    - Adds or updates entry in collection.config["enrichers"]
    - Does not commit (caller handles UnitOfWork)
    """
    collection = _resolve_collection(db, collection_selector)
    _validate_enricher_exists(db, enricher_id)

    cfg = dict(collection.config or {})
    enrichers = list(cfg.get("enrichers", []))

    # Normalize entries as dicts {enricher_id, priority}
    updated = False
    for entry in enrichers:
        if isinstance(entry, dict) and entry.get("enricher_id") == enricher_id:
            entry["priority"] = int(priority)
            updated = True
            break
    if not updated:
        enrichers.append({"enricher_id": enricher_id, "priority": int(priority)})

    # Sort by priority ascending
    try:
        enrichers.sort(key=lambda e: int(e.get("priority", 0)))
    except Exception:
        pass

    cfg["enrichers"] = enrichers
    collection.config = cfg
    db.add(collection)

    return {
        "collection_id": str(collection.uuid),
        "collection_name": collection.name,
        "enricher_id": enricher_id,
        "priority": int(priority),
        "status": "attached",
    }


def detach_enricher_from_collection(
    db: Session, *, collection_selector: str, enricher_id: str
) -> dict[str, Any]:
    """Detach an enricher from a collection.

    - Validates collection and enricher existence (enricher may have been deleted; allow detach)
    - Removes entry from collection.config["enrichers"] if present
    - Does not commit (caller handles UnitOfWork)
    """
    collection = _resolve_collection(db, collection_selector)

    cfg = dict(collection.config or {})
    enrichers = list(cfg.get("enrichers", []))

    new_list: list[dict[str, Any]] = []
    for entry in enrichers:
        if isinstance(entry, dict) and entry.get("enricher_id") == enricher_id:
            # skip to remove
            continue
        new_list.append(entry)

    cfg["enrichers"] = new_list
    collection.config = cfg
    db.add(collection)

    return {
        "collection_id": str(collection.uuid),
        "collection_name": collection.name,
        "enricher_id": enricher_id,
        "status": "detached",
    }


__all__ = [
    "attach_enricher_to_collection",
    "detach_enricher_from_collection",
]


