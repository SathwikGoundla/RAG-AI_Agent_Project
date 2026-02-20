@echo off
REM Advanced RAG System - Complete Startup Script
REM Starts Backend and Frontend automatically

echo.
echo ============================================
echo Advanced RAG System - Full Stack Launch
echo ============================================
echo.

REM Get the project root directory
SET PROJECT_ROOT=%CD%

echo [INFO] Project Root: %PROJECT_ROOT%
echo.

REM Check if virtual environment exists
if not exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please activate it manually: .\venv\Scripts\Activate.ps1
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
echo [OK] Virtual environment activated
echo.

REM Check Python packages
echo [INFO] Checking required packages...
python -c "import streamlit; import requests; import fastapi; import sqlalchemy" >nul 2>&1

if %errorlevel% neq 0 (
    echo [WARNING] Installing required packages...
    pip install streamlit requests fastapi sqlalchemy pydantic -q
    echo [OK] Packages installed
) else (
    echo [OK] All packages installed
)
echo.

REM Check if backend is already running
echo [INFO] Checking if backend is already running...
netstat -ano | findstr :8000 >nul 2>&1

if errorlevel 1 (
    echo [INFO] Backend not running - starting it...
    echo.
    echo ============================================
    echo Starting Backend Server (Port 8000)
    echo ============================================
    echo.
    
    REM Start backend in a new window
    start cmd /k "cd %PROJECT_ROOT%\backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    
    echo [OK] Backend started in new window
    echo [INFO] Waiting for backend to initialize (5 seconds)...
    timeout /t 5 /nobreak
    
) else (
    echo [OK] Backend is already running on port 8000
)

REM Check if frontend is already running
echo [INFO] Checking if frontend is already running...
netstat -ano | findstr :8501 >nul 2>&1

if errorlevel 1 (
    echo [INFO] Frontend not running - starting it...
    echo.
    echo ============================================
    echo Starting Frontend (Port 8501)
    echo ============================================
    echo.
    
    REM Start frontend in a new window
    start cmd /k "cd %PROJECT_ROOT%\frontend && streamlit run app_new.py"
    
    echo [OK] Frontend started in new window
    
) else (
    echo [OK] Frontend is already running on port 8501
)

echo.
echo ============================================
echo System Started Successfully!
echo ============================================
echo.
echo Backend URL:  http://localhost:8000
echo Backend API:  http://localhost:8000/docs
echo Frontend URL: http://localhost:8501
echo.
echo [INFO] Windows will open for backend and frontend
echo [INFO] Both windows will stay open - do NOT close them
echo.
echo Press any key to continue...
pause

echo.
echo ============================================
echo Opening URLs...
echo ============================================
echo.

REM Open URLs in default browser
timeout /t 2 /nobreak
start http://localhost:8501
start http://localhost:8000/docs

echo.
echo [OK] URLs opened in browser
echo [INFO] You can close this window now
echo.
