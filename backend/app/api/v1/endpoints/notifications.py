from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db.session import get_db
from backend.app.db.models.audit import Notification
from backend.app.core.errors import NotFoundError

router = APIRouter()

@router.get("")
def list_notifications(
    status_filter: Optional[str] = Query(None), # 'unread', 'read'
    db: Session = Depends(get_db)
):
    query = select(Notification)
    if status_filter:
        query = query.where(Notification.status == status_filter)
    return list(db.scalars(query.order_by(Notification.created_at.desc())).all())

@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.get(Notification, notification_id)
    if not notif:
        raise NotFoundError(f"Notification {notification_id} not found.")
    notif.status = "read"
    notif.read_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return notif
