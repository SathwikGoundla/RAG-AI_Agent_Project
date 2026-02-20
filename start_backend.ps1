# Start Backend Server Script
# This script starts the FastAPI backend server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Advanced RAG System - Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
Set-Location "C:\Users\Sathwik\advanced-rag-system\backend"

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "C:\Users\Sathwik\advanced-rag-system\.venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting FastAPI Uvicorn server..." -ForegroundColor Green
Write-Host "Backend will be available at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the backend server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
