#!/usr/bin/env python
"""
Test FastAPI backend startup and endpoint functionality
"""
import subprocess
import time
import requests
import json
import sys

print("\n" + "="*80)
print("BACKEND STARTUP & ENDPOINT TEST")
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

# Test 1: Health check
print("\n[TEST 1] Health Check Endpoint (GET /)")
try:
    r = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        print("[PASS] Health check working\n")
    else:
        print(f"[FAIL] Expected 200, got {r.status_code}\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 2: Signup endpoint
print("[TEST 2] Signup Endpoint (POST /api/v1/auth/signup)")
try:
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    r = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=payload, timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")
    if r.status_code in [200, 201]:
        print("[PASS] Signup endpoint working\n")
    else:
        print(f"[WARN] Got status {r.status_code} (may be expected if user already exists)\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Test 3: Login endpoint
print("[TEST 3] Login Endpoint (POST /api/v1/auth/login)")
try:
    payload = {
        "username": "testuser",
        "password": "TestPass123!"
    }
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)[:500]}...")
    if r.status_code == 200:
        print("[PASS] Login endpoint working\n")
        token = r.json().get("access_token")
    else:
        print(f"[WARN] Got status {r.status_code}\n")
        token = None
except Exception as e:
    print(f"[FAIL] Error: {e}\n")
    token = None

# Test 4: Check documentation endpoints
print("[TEST 4] Documentation Endpoints")
try:
    r = requests.get(f"{BASE_URL}/docs", timeout=5)
    print(f"Swagger UI (GET /docs): Status {r.status_code}")
    if r.status_code == 200:
        print("[PASS] Swagger UI accessible\n")
    else:
        print(f"[WARN] Status {r.status_code}\n")
except Exception as e:
    print(f"[FAIL] Error: {e}\n")

# Cleanup
print("[TEST] Stopping backend...")
process.terminate()
try:
    process.wait(timeout=5)
except subprocess.TimeoutExpired:
    process.kill()

print("\n" + "="*80)
print("BACKEND TEST COMPLETE")
print("="*80)
