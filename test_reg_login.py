"""
Test registration and immediate login with SAME credentials
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def test_registration_and_login():
    """Test if we can register and then immediately login with same credentials"""
    print("\n" + "="*60)
    print("REGISTRATION + LOGIN TEST (Same Credentials)")
    print("="*60)
    
    # Use unique username/email each time to avoid conflicts
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    password = "TestPassword123!"
    
    print(f"\nCredentials:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Password: {password}")
    
    # STEP 1: Register
    print(f"\nSTEP 1: Registering user...")
    register_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Test User"
        },
        timeout=10
    )
    
    print(f"Status: {register_response.status_code}")
    print(f"Response: {json.dumps(register_response.json(), indent=2)}")
    
    if register_response.status_code != 201:
        print("❌ REGISTRATION FAILED")
        return False
    
    print("✅ Registration successful")
    
    # Wait a moment
    time.sleep(1)
    
    # STEP 2: Try login with USERNAME
    print(f"\nSTEP 2a: Login with USERNAME...")
    login_response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=10
    )
    
    print(f"Status: {login_response.status_code}")
    response_data = login_response.json()
    print(f"Response: {json.dumps(response_data, indent=2)}")
    
    if login_response.status_code == 200:
        print("✅ Login with USERNAME successful")
        return True
    else:
        print("❌ Login with USERNAME failed")
    
    # STEP 3: Try login with EMAIL
    print(f"\nSTEP 2b: Login with EMAIL...")
    login_response2 = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"username": email, "password": password},
        timeout=10
    )
    
    print(f"Status: {login_response2.status_code}")
    response_data2 = login_response2.json()
    print(f"Response: {json.dumps(response_data2, indent=2)}")
    
    if login_response2.status_code == 200:
        print("✅ Login with EMAIL successful")
        return True
    else:
        print("❌ Login with EMAIL failed")
    
    return False

if __name__ == "__main__":
    test_registration_and_login()
