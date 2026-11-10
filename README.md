# Local Portfolio Tracker

A production-minded, local-first personal investment record, analytics, data-quality, and notification application.

## Overview
- **Local-First & Offline Capable**: Binds exclusively to `127.0.0.1`. No required cloud account, telemetry, remote database, or auto-trading.
- **Authoritative Backend Ledger**: Financial balances are derived strictly from transactions.
- **Technology Stack**:
  - **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide icons.
  - **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x, SQLite (WAL mode, Foreign Keys enabled).
  - **Data Persistence**: `local-data/portfolio.db` (gitignored).

## Quick Start

### 1. Requirements
- Python 3.11+
- Node.js 18+ and npm

### 2. Setup
Clone the repository and install dependencies:
```bash
# Backend setup
python -m venv .venv
# On Windows:
.venv\Scripts\pip install -r backend/requirements.txt (or pip install -e backend)
# On Linux/macOS:
.venv/bin/pip install -e backend

# Frontend setup
cd frontend
npm install
cd ..
```

### 3. Running Locally
Run the combined development script:
```powershell
# Windows PowerShell:
.\scripts\dev.ps1
```
Or Unix shell:
```bash
./scripts/dev.sh
```

Alternatively, start backend and frontend in separate terminals:
**Terminal 1 (Backend):**
```bash
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open your browser at `http://127.0.0.1:5173`.
API documentation is available at `http://127.0.0.1:8000/docs`.

### 4. Running Tests
```bash
.venv\Scripts\pytest -v
```

## Security & Data Privacy
All portfolio data, transactions, price records, and database files remain strictly on your local disk under `./local-data/`. No external telemetry, tracking, or cloud sync is performed.

