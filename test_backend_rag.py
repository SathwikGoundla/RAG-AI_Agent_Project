#!/usr/bin/env python
"""
Test backend with RAG endpoints after fixes
"""
import subprocess
import time
import requests
import json
import sys
import os

print("\n" + "="*80)
print("BACKEND RAG ENDPOINT TEST (POST-FIX)")
print("="*80 + "\n")

# Start backend in background
print("[TEST] Starting FastAPI backend...")
process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd="c:\\Users\\Sathwik\\advanced-rag-system",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for it to start
time.sleep(5)

BASE_URL = "http://localhost:8000"

tests_passed = 0
tests_failed = 0

# Test 1: Health check
print("[TEST 1] Health Check (GET /)")
try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    if r.status_code == 200:
        print(f"[PASS] Status: {r.status_code}")
        tests_passed += 1
    else:
        print(f"[FAIL] Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"[FAIL] Error: {e}")
    tests_failed += 1

# Test 2: Signup
print("\n[TEST 2] Signup (POST /api/v1/auth/signup)")
try:
    payload = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "TestPass123!",
        "full_name": "Test User 2"
    }
    r = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=payload, timeout=5)
    if r.status_code in [200, 201]:
        print(f"[PASS] Status: {r.status_code}")
        tests_passed += 1
    else:
        print(f"[FAIL] Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"[FAIL] Error: {e}")
    tests_failed += 1

# Test 3: Login
print("\n[TEST 3] Login (POST /api/v1/auth/login)")
token = None
try:
    payload = {
        "username": "testuser2",
        "password": "TestPass123!"
    }
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=5)
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token")
        print(f"[PASS] Status: {r.status_code}, Token obtained")
        tests_passed += 1
    else:
        print(f"[FAIL] Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"[FAIL] Error: {e}")
    tests_failed += 1

# Test 4: Check if RAG endpoints are accessible with auth
if token:
    print("\n[TEST 4] RAG Query Endpoint (POST /api/v1/rag/query)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "question": "What is RAG?",
            "language": "english",
            "n_results": 5
        }
        r = requests.post(f"{BASE_URL}/api/v1/rag/query", json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            print(f"[PASS] Status: {r.status_code}, RAG endpoint working")
            tests_passed += 1
        elif r.status_code == 400:
            print(f"[INFO] Status: {r.status_code}, Expected behavior (no documents uploaded yet)")
            print(f"Response: {r.json()}")
            tests_passed += 1
        else:
            print(f"[FAIL] Status: {r.status_code}")
            print(f"Response: {r.json()}")
            tests_failed += 1
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        tests_failed += 1
else:
    print("\n[SKIP] RAG tests skipped (no auth token)")

# Test 5: Check if document endpoints are accessible
if token:
    print("\n[TEST 5] List Documents (GET /api/v1/documents/user_documents)")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/v1/documents/user_documents", headers=headers, timeout=10)
        if r.status_code == 200:
            print(f"[PASS] Status: {r.status_code}, Documents endpoint working")
            print(f"Response: {json.dumps(r.json(), indent=2)[:200]}...")
            tests_passed += 1
        else:
            print(f"[FAIL] Status: {r.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        tests_failed += 1
else:
    print("\n[SKIP] Document tests skipped (no auth token)")

# Cleanup
print("\n[TEST] Stopping backend...")
process.terminate()
try:
    process.wait(timeout=5)
except subprocess.TimeoutExpired:
    process.kill()

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Passed: {tests_passed}")
print(f"Failed: {tests_failed}")
print(f"Total:  {tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n[SUCCESS] All tests passed!")
    sys.exit(0)
else:
    print(f"\n[ALERT] {tests_failed} tests failed")
    sys.exit(1)
