from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.audit import BackupRecord
from backend.app.services.backup_service import backup_service

router = APIRouter()

@router.get("")
def list_backups(db: Session = Depends(get_db)):
    return list(db.scalars(select(BackupRecord).order_by(BackupRecord.created_at.desc())).all())

@router.post("", status_code=status.HTTP_201_CREATED)
def create_backup(label: str = Query("manual"), db: Session = Depends(get_db)):
    record = backup_service.create_backup(db, label=label)
    return {
        "id": record.id,
        "path": record.path,
        "size_bytes": record.size_bytes,
        "checksum": record.checksum,
        "status": record.status,
        "created_at": record.created_at.isoformat()
    }

@router.post("/{backup_id}/restore")
def restore_backup(
    backup_id: int,
    confirm: bool = Query(False),
    db: Session = Depends(get_db)
):
    return backup_service.restore_backup(db, backup_id, confirm=confirm)
