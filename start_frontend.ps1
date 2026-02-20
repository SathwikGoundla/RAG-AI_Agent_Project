# Start Frontend Server Script
# This script starts the Streamlit frontend application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Advanced RAG System - Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
Set-Location "C:\Users\Sathwik\advanced-rag-system\frontend"

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "C:\Users\Sathwik\advanced-rag-system\.venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Starting Streamlit application..." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Make sure the backend is running first!" -ForegroundColor Yellow
Write-Host "Run: .\start_backend.ps1 in another terminal" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the frontend server
streamlit run app.py
