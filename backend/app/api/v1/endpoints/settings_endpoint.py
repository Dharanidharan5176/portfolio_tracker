from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Any

from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.db.models.audit import AppSetting
from datetime import datetime, timezone

router = APIRouter()

MUTABLE_KEYS = {"base_currency", "timezone", "log_level", "market_data_provider", "stale_price_days"}

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    # Merge env-based settings with any DB overrides
    db_settings: Dict[str, str] = {
        r.key: r.value
        for r in db.scalars(select(AppSetting)).all()
    }
    return {
        "app_env": settings.APP_ENV,
        "base_currency": db_settings.get("base_currency", settings.BASE_CURRENCY),
        "timezone": db_settings.get("timezone", settings.APP_TIMEZONE),
        "market_data_provider": db_settings.get("market_data_provider", settings.MARKET_DATA_PROVIDER),
        "log_level": db_settings.get("log_level", settings.LOG_LEVEL),
        "data_dir": str(settings.data_path),
        "stale_price_days": int(db_settings.get("stale_price_days", str(settings.STALE_PRICE_DAYS))),
        "db_overrides": db_settings,
    }

@router.patch("")
def update_settings(
    body: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Persist user-configurable settings to app_settings table. Only known mutable keys are accepted."""
    updated: Dict[str, Any] = {}
    rejected: Dict[str, str] = {}

    for key, value in body.items():
        if key not in MUTABLE_KEYS:
            rejected[key] = "unknown or immutable key"
            continue
        existing = db.get(AppSetting, key)
        if existing:
            existing.value = str(value)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(AppSetting(key=key, value=str(value)))
        updated[key] = str(value)

    db.commit()
    return {"updated": updated, "rejected": rejected}

