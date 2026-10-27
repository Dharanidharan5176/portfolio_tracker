# scripts/dev.ps1 - Local Development Runner for Windows PowerShell
Write-Host "Starting Local Portfolio Tracker (Local-First Mode)..." -ForegroundColor Cyan

# 1. Ensure local-data directories exist
$dataDir = Join-Path $PSScriptRoot "..\local-data"
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "backups") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "imports") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "exports") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "cache") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dataDir "logs") | Out-Null

# 2. Check Virtual Environment
$venvPython = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $PSScriptRoot "..\.venv")
    & $venvPython -m pip install -e (Join-Path $PSScriptRoot "..\backend")
}

# 3. Start Backend in separate process
Write-Host "Starting Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath $venvPython -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru

# 4. Start Frontend
Write-Host "Starting Frontend on http://127.0.0.1:5173..." -ForegroundColor Green
Set-Location (Join-Path $PSScriptRoot "..\frontend")
npm run dev

# Cleanup when frontend exits
Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
