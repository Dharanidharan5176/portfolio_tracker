import sys
import argparse
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.db.session import SessionLocal
from backend.app.services.backup_service import backup_service

def main():
    parser = argparse.ArgumentParser(description="Restore database from a verified backup record.")
    parser.add_argument("backup_id", type=int, help="ID of the BackupRecord to restore from")
    parser.add_argument("--confirm", action="store_true", help="Explicit confirmation of destructive restore")
    args = parser.parse_args()

    if not args.confirm:
        print("ERROR: Destructive database restore requires explicit --confirm flag.")
        sys.exit(1)

    print(f"Restoring database from BackupRecord #{args.backup_id}...")
    db = SessionLocal()
    try:
        res = backup_service.restore_backup(db, args.backup_id, confirm=True)
        print(f"Restore Successful: {res}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

