from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, select, func
from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.db.models.audit import AuditEvent
from pathlib import Path
from typing import Optional

router = APIRouter()

@router.get("/health")
def system_health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        res = db.execute(text("SELECT 1")).scalar()
        db_ok = (res == 1)
    except Exception:
        db_ok = False

    data_dir_writable = False
    try:
        test_file = Path(settings.DATA_DIR) / ".writable_test"
        test_file.write_text("ok")
        test_file.unlink()
        data_dir_writable = True
    except Exception:
        data_dir_writable = False

    return {
        "status": "healthy" if (db_ok and data_dir_writable) else "degraded",
        "database_connected": db_ok,
        "database_path": settings.DATABASE_URL,
        "data_directory_writable": data_dir_writable,
        "provider": settings.MARKET_DATA_PROVIDER,
        "base_currency": settings.BASE_CURRENCY,
        "timezone": settings.APP_TIMEZONE,
        "local_first_enforced": settings.APP_HOST in ("127.0.0.1", "localhost")
    }

@router.get("/audit-events")
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Return paginated audit trail from the audit_events table."""
    q = select(AuditEvent).order_by(AuditEvent.timestamp.desc())
    count_q = select(func.count()).select_from(AuditEvent)

    if action:
        q = q.where(AuditEvent.action == action)
        count_q = count_q.where(AuditEvent.action == action)
    if entity_type:
        q = q.where(AuditEvent.entity_type == entity_type)
        count_q = count_q.where(AuditEvent.entity_type == entity_type)

    total = db.scalar(count_q) or 0
    rows = db.scalars(q.limit(limit).offset(offset)).all()

    items = [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "actor": r.actor,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "reason": r.reason,
            "correlation_id": r.correlation_id,
        }
        for r in rows
    ]
    return {"items": items, "total": total, "limit": limit, "offset": offset}

