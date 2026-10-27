from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.db.session import get_db
from backend.app.core.config import settings
from pathlib import Path
import sqlite3

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
def list_audit_events(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    # Will query AuditEvent table once model is defined
    return {"items": [], "total": 0, "limit": limit, "offset": offset}
