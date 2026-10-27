import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.db.session import SessionLocal
from backend.app.services.backup_service import backup_service

def main():
    print("Initiating consistent SQLite database backup...")
    db = SessionLocal()
    try:
        record = backup_service.create_backup(db, label="cli")
        print(f"Backup created successfully:")
        print(f" - Path: {record.path}")
        print(f" - Checksum (SHA-256): {record.checksum}")
        print(f" - Size: {record.size_bytes} bytes")
        print(f" - Integrity Status: {record.status}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
