# FLOOD-X — Start Mobile Application Script (PowerShell)
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting FLOOD-X Citizen Mobile App (Expo)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location "$RootDir\mobile"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing mobile dependencies..." -ForegroundColor Yellow
    npm install
}

Write-Host "Starting Expo development server..." -ForegroundColor Green
npx expo start

