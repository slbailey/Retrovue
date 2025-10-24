from fastapi import APIRouter, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from retrovue.infra.uow import get_db
from retrovue.content_manager.library_service import LibraryService

router = APIRouter()

@router.post("/{asset_id}/enqueue")
def enqueue_review(asset_id: UUID, reason: str, score: float = 0.0, db: Session = Depends(get_db)):
    LibraryService(db).enqueue_review(asset_id, reason, score)
    return {"success": True}