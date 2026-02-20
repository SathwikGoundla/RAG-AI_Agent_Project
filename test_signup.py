"""
Test script for signup functionality
Tests the signup endpoint with various scenarios
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"
API_V1_STR = "/api/v1"

def print_response(response, test_name):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_signup():
    """Test signup with various scenarios"""
    
    print("🧪 TESTING SIGNUP FUNCTIONALITY")
    print(f"Backend URL: {BACKEND_URL}")
    
    # Test 1: Valid signup
    print("\n\n📝 TEST 1: Valid Signup")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPassword123",
            "full_name": "Test User"
        }
    )
    print_response(response, "Valid Signup")
    
    # Test 2: Duplicate username
    print("\n\n❌ TEST 2: Duplicate Username")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": "sath1",
            "email": f"new_{int(time.time())}@example.com",
            "password": "TestPassword123",
            "full_name": "Another User"
        }
    )
    print_response(response, "Duplicate Username")
    
    # Test 3: Duplicate email
    print("\n\n❌ TEST 3: Duplicate Email")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": f"newuser_{int(time.time())}",
            "email": "sathwikgoundla1@gmail.com",
            "password": "TestPassword123",
            "full_name": "Another User"
        }
    )
    print_response(response, "Duplicate Email")
    
    # Test 4: Weak password - no uppercase
    print("\n\n❌ TEST 4: Weak Password - No Uppercase")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": f"user_{int(time.time())}",
            "email": f"email_{int(time.time())}@example.com",
            "password": "weakpassword123",
            "full_name": "Test User"
        }
    )
    print_response(response, "Weak Password - No Uppercase")
    
    # Test 5: Weak password - no digit
    print("\n\n❌ TEST 5: Weak Password - No Digit")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": f"user_{int(time.time())}",
            "email": f"email_{int(time.time())}@example.com",
            "password": "WeakPassword",
            "full_name": "Test User"
        }
    )
    print_response(response, "Weak Password - No Digit")
    
    # Test 6: Short username
    print("\n\n❌ TEST 6: Short Username")
    response = requests.post(
        f"{BACKEND_URL}{API_V1_STR}/auth/signup",
        json={
            "username": "ab",
            "email": f"email_{int(time.time())}@example.com",
            "password": "ValidPassword123",
            "full_name": "Test User"
        }
    )
    print_response(response, "Short Username")
    
    print("\n\n" + "="*60)
    print("✅ SIGNUP TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    try:
        test_signup()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend")
        print("Make sure backend is running: python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")
