# Start All Services Script
# This PowerShell script starts both Backend and Frontend in separate windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Advanced RAG System - Starting All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend in new PowerShell window
Write-Host "Starting Backend Server in new window..." -ForegroundColor Green
$backendScript = "C:\Users\Sathwik\advanced-rag-system\start_backend.ps1"
Start-Process powershell -ArgumentList "-NoExit -File `"$backendScript`""

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Frontend in new PowerShell window
Write-Host "Starting Frontend Server in new window..." -ForegroundColor Green
$frontendScript = "C:\Users\Sathwik\advanced-rag-system\start_frontend.ps1"
Start-Process powershell -ArgumentList "-NoExit -File `"$frontendScript`""

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Services Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend window will open shortly..." -ForegroundColor Cyan
Write-Host "Frontend window will open after that..." -ForegroundColor Cyan
Write-Host ""
