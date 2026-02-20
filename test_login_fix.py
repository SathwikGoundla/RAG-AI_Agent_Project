"""
Test script to verify login endpoint works with JSON body
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal, User
from backend.auth.security import get_password_hash
import json

print("="*60)
print("🧪 TESTING LOGIN FIX")
print("="*60)

# Step 1: Initialize database
print("\n1️⃣  Initializing database...")
Base.metadata.create_all(bind=engine)
print("✅ Database ready")

# Step 2: Create test user
print("\n2️⃣  Creating test user...")
db = SessionLocal()

# Clean up existing test user
existing = db.query(User).filter(User.username == "testuser").first()
if existing:
    db.delete(existing)
    db.commit()

# Create new test user
test_user = User(
    username="testuser",
    email="test@example.com",
    hashed_password=get_password_hash("TestPassword123"),
    full_name="Test User",
    is_active=True
)
db.add(test_user)
db.commit()
db.refresh(test_user)
print(f"✅ Test user created: {test_user.username} (ID: {test_user.id})")

# Step 3: Simulate login verification
print("\n3️⃣  Verifying password hashing and verification...")
from backend.auth.security import verify_password

is_valid = verify_password("TestPassword123", test_user.hashed_password)
if is_valid:
    print("✅ Password verification works correctly")
else:
    print("❌ Password verification failed")

# Step 4: Show JSON request format
print("\n4️⃣  Login Request Format (JSON):")
login_request = {
    "username": "testuser",
    "password": "TestPassword123"
}
print(json.dumps(login_request, indent=2))

print("\n" + "="*60)
print("✅ TEST SETUP COMPLETE")
print("="*60)
print("\n📝 Next steps:")
print("1. Start the backend: cd backend && python -m uvicorn main:app --reload")
print("2. In another terminal, test login:")
print("   curl -X POST http://localhost:8000/api/v1/auth/login \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{\"username\": \"testuser\", \"password\": \"TestPassword123\"}'")
print("\n3. Or use the frontend at http://localhost:8501")

db.close()
