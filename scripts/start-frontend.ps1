# FLOOD-X — Start Web Frontend Script (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting FLOOD-X Authority Command Dashboard" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location "$RootDir\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting Vite dev server on http://localhost:5173..." -ForegroundColor Green
npm run dev

