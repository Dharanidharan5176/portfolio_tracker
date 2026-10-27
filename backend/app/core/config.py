from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    FRONTEND_HOST: str = "127.0.0.1"
    FRONTEND_PORT: int = 5173
    
    # Storage
    DATA_DIR: str = str(PROJECT_ROOT / "local-data")
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/local-data/portfolio.db"
    
    # Financial defaults
    BASE_CURRENCY: str = "INR"
    APP_TIMEZONE: str = "Asia/Kolkata"
    LOG_LEVEL: str = "INFO"
    
    # Market Data
    MARKET_DATA_PROVIDER: str = "manual_csv"
    MARKET_DATA_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("APP_HOST")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if v not in ("127.0.0.1", "localhost"):
            # Warn / enforce local-first default
            pass
        return v

    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR)
        p.mkdir(parents=True, exist_ok=True)
        (p / "backups").mkdir(parents=True, exist_ok=True)
        (p / "imports").mkdir(parents=True, exist_ok=True)
        (p / "exports").mkdir(parents=True, exist_ok=True)
        (p / "cache").mkdir(parents=True, exist_ok=True)
        (p / "logs").mkdir(parents=True, exist_ok=True)
        return p

settings = Settings()
