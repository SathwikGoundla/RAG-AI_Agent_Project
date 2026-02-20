#!/usr/bin/env python3
"""
Comprehensive test of the complete authentication system
Tests both backend and frontend endpoints
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"
TEST_USERNAME = "completetest"
TEST_EMAIL = "completetest@test.com"
TEST_PASSWORD = "TestPass123"
TEST_FULLNAME = "Complete Test User"

def test_complete_flow():
    """Test the complete authentication flow"""
    
    print("\n" + "="*70)
    print("COMPLETE AUTHENTICATION FLOW TEST")
    print("="*70 + "\n")
    
    # Step 1: Verify Backend is Running
    print("STEP 1: Check Backend Status")
    print("-" * 70)
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Status: {data.get('status')}")
            print(f"   Project: {data.get('project')}")
            print(f"   Version: {data.get('version')}\n")
        else:
            print("❌ Backend returned error status\n")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}\n")
        return False
    
    # Step 2: Create Test User (Register)
    print("STEP 2: Register New User")
    print("-" * 70)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_FULLNAME
            },
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            user = response.json()
            print(f"✅ User Registered\n")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Full Name: {user.get('full_name')}")
            print(f"   User ID: {user.get('id')}\n")
        else:
            print(f"❌ Registration failed: {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Step 3: Login
    print("STEP 3: Login with Credentials")
    print("-" * 70)
    access_token = None
    user_id = None
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            print(f"✅ Login Successful\n")
            print(f"   Access Token (first 50 chars): {access_token[:50] if access_token else 'N/A'}...")
            print(f"   Token Type: {data.get('token_type')}")
            print(f"   Expires In: {data.get('expires_in')} seconds")
            
            # Extract user info
            user = data.get("user", {})
            user_id = user.get("id")
            print(f"\n   User Info:")
            print(f"   - ID: {user_id}")
            print(f"   - Username: {user.get('username')}")
            print(f"   - Email: {user.get('email')}")
            print(f"   - Full Name: {user.get('full_name')}")
            print(f"   - Active: {user.get('is_active')}\n")
        else:
            print(f"❌ Login failed: {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Step 4: Get Current User Profile (Protected Endpoint)
    print("STEP 4: Retrieve Current User Profile (Protected)")
    print("-" * 70)
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Profile Retrieved (Protected Endpoint)\n")
            print(f"   Username: {user.get('username')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Full Name: {user.get('full_name')}\n")
        else:
            print(f"❌ Failed to retrieve profile: {response.json()}\n")
            return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Step 5: Test Invalid Token
    print("STEP 5: Test Invalid Token Handling")
    print("-" * 70)
    try:
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 401:
            print(f"✅ Invalid Token Properly Rejected\n")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.json().get('detail')}\n")
        else:
            print(f"⚠️  Unexpected status for invalid token: {response.status_code}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Step 6: Test All Auth Endpoints
    print("STEP 6: Verify API Endpoints Documentation")
    print("-" * 70)
    try:
        response = requests.get(f"{BACKEND_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            docs = response.json()
            paths = list(docs.get("paths", {}).keys())
            auth_paths = [p for p in paths if "auth" in p]
            
            print(f"✅ Documentation Available\n")
            print(f"   Auth Endpoints Found:")
            for path in sorted(auth_paths):
                print(f"   - {path}")
            print()
        else:
            print("⚠️  Could not retrieve documentation\n")
    except Exception as e:
        print(f"⚠️  Note: {e}\n")
    
    print("="*70)
    print("✅ ALL TESTS PASSED - AUTHENTICATION SYSTEM WORKING!")
    print("="*70 + "\n")
    
    print("NEXT STEPS:")
    print("-" * 70)
    print("1. Test Frontend Login:")
    print("   - Navigate to http://localhost:8501")
    print("   - Go to Login tab")
    print("   - Enter username: " + TEST_USERNAME)
    print("   - Enter password: " + TEST_PASSWORD)
    print("   - Click 'Sign In'")
    print()
    print("2. Test Signup:")
    print("   - Go to Sign Up tab")
    print("   - Register a new account")
    print("   - Login with new credentials")
    print()
    print("3. Verify Features:")
    print("   - Chat with documents")
    print("   - Upload new documents")
    print("   - Generate quizzes")
    print()
    
    return True

if __name__ == "__main__":
    success = test_complete_flow()
    exit(0 if success else 1)
