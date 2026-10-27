from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()

@router.get("")
def get_settings():
    return {
        "app_env": settings.APP_ENV,
        "base_currency": settings.BASE_CURRENCY,
        "timezone": settings.APP_TIMEZONE,
        "market_data_provider": settings.MARKET_DATA_PROVIDER,
        "log_level": settings.LOG_LEVEL,
        "data_dir": str(settings.data_path)
    }
