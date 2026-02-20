# Advanced RAG System - PowerShell Startup Script
# Starts Backend and Frontend automatically

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Advanced RAG System - Full Stack Launch" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Get-Location

Write-Host "[INFO] Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "$ProjectRoot\.venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please activate it manually" -ForegroundColor Yellow
    Read-Host "Press Enter to continue"
    exit 1
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& "$ProjectRoot\.venv\Scripts\Activate.ps1"
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Check Python packages
Write-Host "[INFO] Checking required packages..." -ForegroundColor Yellow
$packages_ok = $true

try {
    python -c "import streamlit; import requests; import fastapi; import sqlalchemy" 2>$null
}
catch {
    $packages_ok = $false
}

if (-not $packages_ok) {
    Write-Host "[WARNING] Installing required packages..." -ForegroundColor Yellow
    pip install streamlit requests fastapi sqlalchemy pydantic -q
    Write-Host "[OK] Packages installed" -ForegroundColor Green
} else {
    Write-Host "[OK] All packages installed" -ForegroundColor Green
}
Write-Host ""

# Check if backend is already running
Write-Host "[INFO] Checking if backend is already running..." -ForegroundColor Yellow

$backend_running = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $backend_running = $true
    }
}
catch {
    $backend_running = $false
}

if (-not $backend_running) {
    Write-Host "[INFO] Backend not running - starting it..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Starting Backend Server (Port 8000)" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Start backend in a new window/process
    $backend_process = Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -WorkingDirectory "$ProjectRoot\backend" -WindowStyle Normal -PassThru
    
    Write-Host "[OK] Backend started (PID: $($backend_process.Id))" -ForegroundColor Green
    Write-Host "[INFO] Waiting for backend to initialize (5 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
} else {
    Write-Host "[OK] Backend is already running on port 8000" -ForegroundColor Green
}

# Check if frontend is already running
Write-Host "[INFO] Checking if frontend is already running..." -ForegroundColor Yellow

$frontend_running = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $frontend_running = $true
    }
}
catch {
    $frontend_running = $false
}

if (-not $frontend_running) {
    Write-Host "[INFO] Frontend not running - starting it..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Starting Frontend (Port 8501)" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Start frontend in a new window
    $frontend_process = Start-Process -FilePath "streamlit" -ArgumentList "run app_new.py" -WorkingDirectory "$ProjectRoot\frontend" -WindowStyle Normal -PassThru
    
    Write-Host "[OK] Frontend started (PID: $($frontend_process.Id))" -ForegroundColor Green
    
} else {
    Write-Host "[OK] Frontend is already running on port 8501" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "System Started Successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Backend API:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend URL: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "[INFO] Opening URLs in browser..." -ForegroundColor Cyan
Write-Host ""

# Wait a bit before opening
Start-Sleep -Seconds 2

# Open URLs
Start-Process "http://localhost:8501"
Start-Process "http://localhost:8000/docs"

Write-Host "[OK] URLs opened in browser" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Keep these windows open for the services to run" -ForegroundColor Yellow
Write-Host ""
