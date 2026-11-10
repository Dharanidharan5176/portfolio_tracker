# Local Portfolio Tracker — Backup and Restore Guide

## 1. Safety and Consistency
SQLite databases must not be copied naively while active write connections exist. The Local Portfolio Tracker uses SQLite's official online backup API (or vacuum into) to take point-in-time consistent snapshots.

## 2. Backup Workflow
1. The backup service opens a read-only lock or connects using SQLite backup API (`sqlite3.Connection.backup`).
2. Snapshot is written to `local-data/backups/portfolio_backup_YYYYMMDD_HHMMSS.db`.
3. A SHA-256 checksum is computed and stored alongside the file.
4. The backup is verified by opening it, running `PRAGMA integrity_check`, and validating core tables.
5. A `BackupRecord` is inserted into the audit log.

## 3. Restore Workflow
1. Destructive action protection: Before executing any restore, an automatic pre-restore safety backup is created (`pre_restore_YYYYMMDD_HHMMSS.db`).
2. The user must provide explicit confirmation.
3. The restore target file checksum is verified against its record.
4. Active connections are terminated gracefully.
5. The SQLite database file is restored and verified.

