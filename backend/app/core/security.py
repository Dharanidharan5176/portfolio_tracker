import re
from typing import Any
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.errors import AppError

def sanitize_csv_cell(val: Any) -> str:
    """Protects against spreadsheet formula injection (=, +, -, @, tab, cr)."""
    if val is None:
        return ""
    s = str(val)
    if s.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{s}"
    return s

def sanitize_filename(filename: str) -> str:
    """Sanitizes file upload names preventing directory traversal."""
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', Path(filename).name)
    return cleaned or "unnamed_file.csv"

def resolve_safe_data_path(relative_path: str) -> Path:
    """Ensures a path resolves strictly inside the local data directory."""
    base = Path(settings.DATA_DIR).resolve()
    target = (base / relative_path).resolve()
    if not str(target).startswith(str(base)):
        raise AppError("Path traversal violation detected.", code="SECURITY_VIOLATION", status_code=403)
    return target
