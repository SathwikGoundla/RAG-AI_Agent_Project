#!/usr/bin/env python
"""
Comprehensive import diagnostic for Advanced RAG System backend
"""
import sys
import os
import traceback

print("\n" + "="*80)
print("BACKEND IMPORT DIAGNOSTIC TEST")
print("="*80 + "\n")

# Critical imports to test
tests = [
    ("Config", "from backend.config import settings"),
    ("Database", "from backend.database import init_db"),
    ("Auth Signup", "from backend.auth.signup import router"),
    ("Auth Login", "from backend.auth.login import router"),
    ("Auth Session Manager", "from backend.auth.session_manager import router"),
    ("Auth Admin", "from backend.auth.admin import router"),
    ("Document Processor Router", "from backend.document_processor.router import router"),
    ("RAG Engine Router", "from backend.rag_engine.router import router"),
    ("Relationships Router", "from backend.rag_engine.relationships_router import router"),
    ("Quiz Router", "from backend.rag_engine.quiz_router import router"),
    ("Main App", "from backend.main import app"),
]

results = []
for name, import_stmt in tests:
    try:
        exec(import_stmt)
        print(f"[OK] {name:40} PASSED")
        results.append((name, True, None))
    except Exception as e:
        print(f"[FAIL] {name:40} FAILED")
        print(f"   Error: {str(e)[:100]}")
        results.append((name, False, str(e)))

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

passed = sum(1 for _, success, _ in results if success)
failed = sum(1 for _, success, _ in results if not success)

print(f"\n[PASSED] Count: {passed}/{len(results)}")
print(f"[FAILED] Count: {failed}/{len(results)}")

if failed > 0:
    print("\n" + "="*80)
    print("DETAILED ERROR INFORMATION")
    print("="*80 + "\n")
    
    for name, success, error in results:
        if not success:
            print(f"\n[ERROR] {name}")
            print(f"{'─'*80}")
            # Get full traceback
            try:
                import_stmt = next(stmt for test_name, stmt in tests if test_name == name)
                exec(import_stmt)
            except Exception:
                traceback.print_exc()

print("\n" + "="*80)
