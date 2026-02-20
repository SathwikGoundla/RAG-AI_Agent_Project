"""
Deep diagnostic to find the exact login failure reason
"""

import sys
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import User, init_db, Base
from backend.config import settings

def test_password_hashing():
    """Test if password hashing works correctly"""
    print("\n" + "="*60)
    print("PASSWORD HASHING TEST")
    print("="*60)
    
    test_password = "TestPass123"
    
    # Generate hash
    hashed = generate_password_hash(test_password)
    print(f"Original: {test_password}")
    print(f"Hashed: {hashed}")
    
    # Verify
    is_correct = check_password_hash(hashed, test_password)
    print(f"Verification: {is_correct}")
    
    if is_correct:
        print("✅ Password hashing works correctly")
    else:
        print("❌ Password hashing FAILED")
    
    return is_correct

def test_database_user():
    """Test if we can create and retrieve a user from database"""
    print("\n" + "="*60)
    print("DATABASE USER TEST")
    print("="*60)
    
    # Initialize database
    init_db()
    
    # Get database session
    from backend.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Create test user
        test_username = "dbtest_user"
        test_email = "dbtest@example.com"
        test_password = "DBTestPass123"
        
        # Check if user already exists
        existing = db.query(User).filter(User.username == test_username).first()
        if existing:
            db.delete(existing)
            db.commit()
            print(f"Deleted existing user: {test_username}")
        
        # Create new user
        from backend.auth.security import get_password_hash
        
        hashed_pwd = get_password_hash(test_password)
        new_user = User(
            username=test_username,
            email=test_email,
            hashed_password=hashed_pwd,
            full_name="DB Test User"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✅ User created: {new_user.username}")
        print(f"  Stored hash: {new_user.hashed_password[:50]}...")
        
        # Retrieve user
        retrieved_user = db.query(User).filter(User.username == test_username).first()
        if retrieved_user:
            print(f"✅ User retrieved from DB: {retrieved_user.username}")
            
            # Test password verification
            from backend.auth.security import verify_password
            is_correct = verify_password(test_password, retrieved_user.hashed_password)
            print(f"  Password verification: {is_correct}")
            
            if is_correct:
                print("✅ Password verification works")
            else:
                print("❌ Password verification FAILED")
                print(f"  Stored hash: {retrieved_user.hashed_password}")
        else:
            print("❌ User not found in DB")
        
        # Clean up
        db.delete(retrieved_user)
        db.commit()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_login_endpoint_direct():
    """Test login by directly calling the login function"""
    print("\n" + "="*60)
    print("DIRECT LOGIN ENDPOINT TEST")
    print("="*60)
    
    from backend.database import SessionLocal, User
    from backend.auth.security import verify_password, get_password_hash, create_access_token
    
    db = SessionLocal()
    
    try:
        # Create a test user
        test_user = User(
            username="directtest",
            email="directtest@example.com",
            hashed_password=get_password_hash("DirectTest123"),
            full_name="Direct Test"
        )
        
        # Clear existing user if any
        existing = db.query(User).filter(User.username == "directtest").first()
        if existing:
            db.delete(existing)
            db.commit()
        
        db.add(test_user)
        db.commit()
        print(f"✅ Created test user: directtest")
        
        # Try to login
        login_user = db.query(User).filter(User.username == "directtest").first()
        
        if login_user:
            print(f"✅ User found: {login_user.username}")
            
            # Check password
            pwd_match = verify_password("DirectTest123", login_user.hashed_password)
            print(f"  Password match: {pwd_match}")
            
            if pwd_match:
                # Generate token
                token = create_access_token(data={"sub": login_user.username, "user_id": login_user.id})
                print(f"✅ Token generated: {token[:50]}...")
                print("✅ LOGIN WOULD SUCCEED")
            else:
                print("❌ PASSWORD MISMATCH - LOGIN WOULD FAIL")
        else:
            print("❌ User not found - LOGIN WOULD FAIL")
        
        # Clean up
        db.delete(login_user)
        db.commit()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    print("\n" + "#"*60)
    print("# DEEP DIAGNOSTIC - LOGIN FAILURE ANALYSIS")
    print("#"*60)
    
    # Test 1: Password hashing
    hashing_works = test_password_hashing()
    
    # Test 2: Database operations
    test_database_user()
    
    # Test 3: Login endpoint
    test_login_endpoint_direct()

if __name__ == "__main__":
    main()
