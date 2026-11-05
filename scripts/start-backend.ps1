# FLOOD-X — Start Backend Server Script (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting FLOOD-X FastAPI Intelligence Engine" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location "$RootDir\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    & ".\.venv\Scripts\pip" install -r requirements.txt
}

Write-Host "Activating virtual environment & launching uvicorn..." -ForegroundColor Green
& ".\.venv\Scripts\python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

