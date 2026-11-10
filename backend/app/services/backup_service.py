import hashlib
import sqlite3
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.errors import AppError, NotFoundError, ValidationError
from backend.app.db.models.audit import BackupRecord
from backend.app.services.audit_service import audit_service
from backend.app.core.logging import logger

class BackupService:
    @staticmethod
    def get_db_file_path() -> Path:
        url = settings.DATABASE_URL
        if url.startswith("sqlite:///"):
            clean_path = url.replace("sqlite:///", "")
            return Path(clean_path).resolve()
        raise AppError("Non-SQLite database configured.")

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify_backup_integrity(backup_path: Path) -> bool:
        """Opens backup file and executes PRAGMA integrity_check."""
        try:
            conn = sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            conn.close()
            return res is not None and res[0] == "ok"
        except Exception as ex:
            logger.error("Backup integrity check failed: %s", ex)
            return False

    @staticmethod
    def create_backup(db: Session, label: str = "manual") -> BackupRecord:
        db_file = BackupService.get_db_file_path()
        if not db_file.exists():
            raise NotFoundError("Live database file not found for backup.")

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"portfolio_backup_{timestamp_str}_{label}.db"
        backup_dir = settings.data_path / "backups"
        backup_path = backup_dir / backup_filename

        # Use SQLite backup API for a point-in-time clean consistent snapshot
        src_conn = sqlite3.connect(str(db_file))
        dst_conn = sqlite3.connect(str(backup_path))
        with dst_conn:
            src_conn.backup(dst_conn, pages=100)
        dst_conn.close()
        src_conn.close()

        # Compute checksum & verify
        checksum = BackupService.compute_sha256(backup_path)
        is_valid = BackupService.verify_backup_integrity(backup_path)

        size_bytes = backup_path.stat().st_size

        record = BackupRecord(
            path=str(backup_path),
            created_at=datetime.now(timezone.utc),
            size_bytes=size_bytes,
            checksum=checksum,
            status="valid" if is_valid else "corrupt",
            verified_at=datetime.now(timezone.utc) if is_valid else None
        )
        db.add(record)
        db.flush()

        audit_service.log(
            db,
            action="CREATE_DATABASE_BACKUP",
            entity_type="backup_record",
            entity_id=record.id,
            after_state={"filename": backup_filename, "size": size_bytes, "checksum": checksum, "status": record.status}
        )
        db.commit()
        db.refresh(record)

        logger.info("Database backup created successfully: %s", backup_path)
        return record

    @staticmethod
    def restore_backup(
        db: Session,
        backup_id: int,
        confirm: bool = False
    ) -> Dict[str, Any]:
        if not confirm:
            raise ValidationError("Explicit confirmation (confirm=True) required before destructive database restore.")

        record = db.get(BackupRecord, backup_id)
        if not record:
            raise NotFoundError(f"Backup record #{backup_id} not found.")

        target_backup = Path(record.path)
        if not target_backup.exists():
            raise NotFoundError(f"Backup file '{record.path}' does not exist on disk.")

        # 1. Verify checksum
        cur_hash = BackupService.compute_sha256(target_backup)
        if cur_hash != record.checksum:
            raise ValidationError("Backup checksum mismatch! File may be corrupted or modified.")

        # 2. Pre-restore safety backup
        live_db = BackupService.get_db_file_path()
        pre_restore_filename = f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"
        pre_restore_path = settings.data_path / "backups" / pre_restore_filename
        if live_db.exists():
            shutil.copy2(live_db, pre_restore_path)

        # 3. Restore using SQLite backup API
        src_conn = sqlite3.connect(str(target_backup))
        dst_conn = sqlite3.connect(str(live_db))
        with dst_conn:
            src_conn.backup(dst_conn, pages=100)
        dst_conn.close()
        src_conn.close()

        audit_service.log(
            db,
            action="RESTORE_DATABASE_BACKUP",
            entity_type="backup_record",
            entity_id=record.id,
            reason="User confirmed restore",
            after_state={"restored_from": str(target_backup), "pre_restore_backup": str(pre_restore_path)}
        )

        return {
            "status": "success",
            "message": "Database restored successfully.",
            "restored_from": str(target_backup),
            "pre_restore_safety_backup": str(pre_restore_path)
        }

backup_service = BackupService()

