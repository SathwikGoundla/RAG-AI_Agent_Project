@echo off
REM Start Backend Server
echo ============================================
echo Starting Advanced RAG Backend Server
echo ============================================
cd c:\Users\Sathwik\advanced-rag-system\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
