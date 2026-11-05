# FLOOD-X -- Full System Verification Script (PowerShell)
$ErrorActionPreference = "Continue"
$RootDir = (Get-Item $PSScriptRoot).Parent.FullName

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " FLOOD-X Phase 0: System Architecture Verification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Backend Pytest
Write-Host "`n[1/4] Running Backend Pytest Suite..." -ForegroundColor Yellow
$pytestExe = Join-Path $RootDir "backend\.venv\Scripts\pytest.exe"
if (Test-Path $pytestExe) {
    Set-Location "$RootDir\backend"
    & $pytestExe tests -v
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Backend tests passed!" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Backend tests failed!" -ForegroundColor Red
    }
} else {
    Write-Host "[WARN] Backend virtualenv not found." -ForegroundColor DarkYellow
}

# 2. Frontend Build
Write-Host "`n[2/4] Verifying Frontend Production Build..." -ForegroundColor Yellow
Set-Location "$RootDir\frontend"
npm.cmd run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Frontend build succeeded!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Frontend build failed!" -ForegroundColor Red
}

# 3. Mobile Typecheck
Write-Host "`n[3/4] Verifying Mobile TypeScript Compilation..." -ForegroundColor Yellow
Set-Location "$RootDir\mobile"
npm.cmd run typecheck
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Mobile typecheck passed!" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Mobile typecheck failed!" -ForegroundColor Red
}

# 4. Docker Compose Validation
Write-Host "`n[4/4] Validating Docker Compose Blueprint..." -ForegroundColor Yellow
Set-Location "$RootDir"
docker.exe compose config --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Docker compose configuration is valid!" -ForegroundColor Green
} else {
    Write-Host "[WARN] Docker compose check returned code $LASTEXITCODE." -ForegroundColor DarkYellow
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host " Phase 0 System Verification Complete!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
