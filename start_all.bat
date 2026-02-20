@echo off
REM Start Both Backend and Frontend in Separate Windows
REM This batch file automatically starts both services

color 0A
cls
echo.
echo ========================================
echo Advanced RAG System - Start All Services
echo ========================================
echo.
echo Starting Backend Server...
echo.

REM Start backend in new window
start cmd /k "cd /d C:\Users\Sathwik\advanced-rag-system && call .venv\Scripts\activate.bat && cd backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak

echo Starting Frontend Server...
echo.

REM Start frontend in new window
start cmd /k "cd /d C:\Users\Sathwik\advanced-rag-system && call .venv\Scripts\activate.bat && cd frontend && streamlit run app.py"

timeout /t 2 /nobreak

echo.
echo ========================================
echo Services Starting...
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:8501
echo Docs:     http://127.0.0.1:8000/docs
echo.
echo Press any key to exit this window...
pause
