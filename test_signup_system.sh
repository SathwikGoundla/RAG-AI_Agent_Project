#!/bin/bash
# Quick test script to verify signup is working

echo "🔍 Testing Advanced RAG Signup System"
echo "======================================"

# Test 1: Diagnostic
echo ""
echo "1️⃣  Running database diagnostic..."
python diagnostic_signup.py

# Test 2: Start backend (optional)
echo ""
echo "2️⃣  To test with the full system:"
echo "   Terminal 1 (Backend):"
echo "   cd backend && python -m uvicorn main:app --reload"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   cd frontend && streamlit run app.py"
echo ""
echo "   Then visit: http://localhost:8501"
echo "   And try signing up!"

echo ""
echo "✅ Setup complete!"
