#!/usr/bin/env python3
"""Quick test script for authentication endpoints"""

import requests
import json
import time
import sys

BACKEND_URL = "http://localhost:8000"

def test_auth_flow():
    """Test the complete authentication flow"""
    
    print("\n" + "="*60)
    print("ADVANCED RAG SYSTEM - AUTHENTICATION TEST")
    print("="*60 + "\n")
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to start...")
    for i in range(30):
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!\n")
                break
        except:
            pass
        if i < 29:
            time.sleep(1)
    else:
        print("❌ Backend did not start. Make sure it's running on port 8000")
        return False
    
    # Test 1: Health Check
    print("TEST 1: Health Check")
    print("-" * 60)
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Test 2: Register New User
    print("TEST 2: Register New Test User")
    print("-" * 60)
    test_username = "testuser12345"
    test_email = "testuser12345@example.com"
    test_password = "TestPassword123!"
    test_fullname = "Test User"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": test_username,
                "email": test_email,
                "password": test_password,
                "full_name": test_fullname
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("✅ Registration successful!")
            print(f"Response: {response.json()}\n")
        else:
            print(f"⚠️  Response: {response.json()}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Test 3: Login
    print("TEST 3: Login with Credentials")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={
                "username": test_username,
                "password": test_password
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
            print(f"Token Type: {data.get('token_type')}")
            print(f"User: {data.get('user', {}).get('username')}")
            print(f"Expires In: {data.get('expires_in')} seconds\n")
            
            access_token = data.get('access_token')
            
            # Test 4: Get Current User
            print("TEST 4: Get Current User Profile")
            print("-" * 60)
            try:
                headers = {"Authorization": f"Bearer {access_token}"}
                response = requests.get(
                    f"{BACKEND_URL}/api/v1/auth/me",
                    headers=headers,
                    timeout=10
                )
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Current user profile retrieved!")
                    print(f"Response: {response.json()}\n")
                else:
                    print(f"❌ Response: {response.json()}\n")
            except Exception as e:
                print(f"❌ Error: {e}\n")
        else:
            print(f"❌ Response: {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Test 5: Admin Login
    print("TEST 5: Admin User Login")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin-password-change-this"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Admin login successful!")
            print(f"User: {data.get('user', {}).get('username')}")
            print(f"Email: {data.get('user', {}).get('email')}\n")
        else:
            print(f"⚠️  Response: {response.json()}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    print("="*60)
    print("✅ ALL TESTS COMPLETED!")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = test_auth_flow()
    sys.exit(0 if success else 1)
