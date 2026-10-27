import logging
import sys
from pathlib import Path
from backend.app.core.config import settings

def redact_sensitive(text: str) -> str:
    """Redacts secrets and API keys from log strings."""
    if not text:
        return text
    if settings.MARKET_DATA_API_KEY and len(settings.MARKET_DATA_API_KEY) > 3:
        text = text.replace(settings.MARKET_DATA_API_KEY, "[REDACTED_API_KEY]")
    return text

class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        return redact_sensitive(orig)

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger("portfolio_tracker")
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (req:%(request_id)s): %(message)s",
            defaults={"request_id": "-"}
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        log_file = settings.data_path / "logs" / "app.log"
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

logger = setup_logging()
