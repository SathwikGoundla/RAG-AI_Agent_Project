"""
Diagnostic script to test signup and identify database issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base, SessionLocal, User
from backend.auth.security import get_password_hash
from sqlalchemy.exc import IntegrityError
import traceback

print("="*60)
print("🔍 DIAGNOSTIC: SIGNUP DATABASE TEST")
print("="*60)

# Step 1: Check database connection
print("\n1️⃣  Testing database connection...")
try:
    with engine.connect() as conn:
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Step 2: Initialize database tables
print("\n2️⃣  Initializing database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
except Exception as e:
    print(f"❌ Failed to create tables: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test user creation
print("\n3️⃣  Testing user creation...")
db = SessionLocal()
test_username = "diagnostic_test_user"
test_email = "diagnostic_test@example.com"

try:
    # Check if user exists
    existing = db.query(User).filter(User.username == test_username).first()
    if existing:
        print(f"⚠️  Cleaning up existing test user: {test_username}")
        db.delete(existing)
        db.commit()
    
    # Try to create new user
    print(f"   Creating user: {test_username} / {test_email}")
    new_user = User(
        username=test_username,
        email=test_email,
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Diagnostic Test User",
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"✅ User created successfully: ID={new_user.id}, Username={new_user.username}")
    
    # Clean up
    db.delete(new_user)
    db.commit()
    print("✅ Test user cleaned up")
    
except IntegrityError as e:
    db.rollback()
    print(f"❌ Integrity error: {e}")
    print(f"   (Likely: Duplicate username or email)")
    traceback.print_exc()
except Exception as e:
    db.rollback()
    print(f"❌ Unexpected error: {type(e).__name__}: {e}")
    traceback.print_exc()
finally:
    db.close()

# Step 4: Check existing users
print("\n4️⃣  Checking existing users in database...")
db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"✅ Total users in database: {len(users)}")
    for user in users[:5]:  # Show first 5
        print(f"   - {user.id}: {user.username} ({user.email})")
    if len(users) > 5:
        print(f"   ... and {len(users) - 5} more")
except Exception as e:
    print(f"❌ Error querying users: {e}")
finally:
    db.close()

print("\n" + "="*60)
print("✅ DIAGNOSTIC COMPLETE")
print("="*60)
print("\nIf issues found:")
print("1. Delete sql_app.db and restart backend")
print("2. Check file permissions")
print("3. Ensure .env or CONFIG.env has correct settings")
