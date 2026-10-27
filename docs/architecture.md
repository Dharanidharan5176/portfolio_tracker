# Local Portfolio Tracker — Architecture

## 1. Overview
The Local Portfolio Tracker is a local-first personal investment ledger, analytics, data quality, and notification application. It is designed to run exclusively on the user's local machine without mandatory cloud dependencies, remote databases, or external analytics telemetry.

## 2. Architecture Principles
1. **Local-First & Privacy Preserving**: Binds exclusively to `127.0.0.1`. No automatic cloud sync, no tracking, no remote logging.
2. **Authoritative Backend Ledger**: The FastAPI backend and SQLite database are the single source of truth. The frontend does not calculate balances or financial metrics independently.
3. **Auditability & Non-Destructive Operations**: Financial transactions are immutable once posted. Corrections and reversals are recorded explicitly through compensating transactions and audit events.
4. **Reproducibility**: Every valuation, return, and performance calculation records its as-of date, currency, price source, and method.
5. **Decoupled Provider Interface**: Market data is retrieved through clean abstraction adapters (`MarketDataProvider`). The app operates fully offline with CSV/manual data entry.

## 3. High-Level System Architecture
```mermaid
graph TD
    UI[React + Vite Frontend (127.0.0.1:5173)]
    API[FastAPI Backend (127.0.0.1:8000)]
    DB[(SQLite Database / local-data/portfolio.db)]
    SCHED[Local Background Scheduler (APScheduler)]
    FILES[Local Filesystem (Backups, CSVs, Logs)]
    PROV[Market Data Providers (manual_csv / optional adapters)]

    UI -->|REST JSON API| API
    API -->|SQLAlchemy 2.x ORM| DB
    SCHED -->|Scheduled Service Calls| API
    API -->|Atomic Backups & CSV Storage| FILES
    API -->|Abstract Data Provider Interface| PROV
```

## 4. Component Layers
- **Frontend (`frontend/src`)**:
  - `features/`: Vertical domain slices (dashboard, portfolios, holdings, transactions, performance, allocation, income, imports, data-quality, notifications, reports, settings, system).
  - `components/`: UI components (layout, charts, tables, forms, feedback).
  - `api/`: Strongly-typed API client and DTO schemas.
- **Backend (`backend/app`)**:
  - `api/v1/`: Versioned route handlers and request/response models.
  - `services/`: Core financial domain services (portfolio, transaction, valuation, performance, allocation, import, data quality, notification, backup, scheduler).
  - `db/models/`: Declarative SQLAlchemy 2.x models with foreign keys, constraints, and index definitions.
  - `providers/`: Extensible market data adapters conforming to `MarketDataProvider`.
  - `jobs/`: Background scheduled tasks with overlap prevention and run tracking.
- **Persistence (`local-data/`)**:
  - `portfolio.db`: SQLite database running in WAL mode with foreign key enforcement enabled.
  - `backups/`: Verified SQLite backups with SHA256 checksums.
  - `imports/`: Archived CSV uploads with SHA256 hashes.
  - `logs/`: Redacted structured log files.
