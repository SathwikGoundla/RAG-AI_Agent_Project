"""
Test Google OAuth callback with actual backend
"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

async def test_google_callback():
    """Test the Google OAuth callback endpoint"""
    print("\n" + "="*60)
    print("Testing Google OAuth Callback Endpoint")
    print("="*60)
    
    # First, we need to simulate getting a valid state
    # In a real flow, we'd do:
    # 1. Call GET /api/v1/auth/google to get the state
    # 2. Then use that state in the callback
    
    # For now, let's just try a callback with invalid state to see the error handling
    async with httpx.AsyncClient() as client:
        # Test 1: Try callback with invalid state
        print("\n[TEST 1] Callback with invalid state...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/auth/google/callback",
                params={
                    "code": "test_code",
                    "state": "invalid_state_12345"
                },
                follow_redirects=False,
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Try with missing parameters
        print("\n[TEST 2] Callback with missing code...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/auth/google/callback",
                params={"state": "invalid_state_12345"},
                follow_redirects=False,
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_google_callback())
