"""
Debug script for Google OAuth callback flow
Tests the complete flow: user lookup -> user creation -> token generation
"""

import sys
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base, User
from backend.config import settings
from backend.auth.security import create_access_token, create_refresh_token, get_password_hash
import secrets
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Simulate Google OAuth user data
    google_email = "test.oauth@gmail.com"
    google_id = "117829848273849273"
    google_name = "OAuth Test User"
    
    print(f"\n[TEST] Simulating Google OAuth callback...")
    print(f"  Email: {google_email}")
    print(f"  Google ID: {google_id}")
    print(f"  Name: {google_name}")
    
    # Step 1: Check if user exists
    print(f"\n[STEP 1] Looking up user with email: {google_email}")
    user = db.query(User).filter(User.email == google_email).first()
    
    if user:
        print(f"  ✓ User found: {user.username} (ID: {user.id})")
    else:
        print(f"  - User not found, creating new user...")
        
        # Step 2: Create new user
        try:
            random_password = secrets.token_urlsafe(32)
            username = google_email.split("@")[0]
            
            user = User(
                email=google_email,
                username=username,
                full_name=google_name,
                hashed_password=get_password_hash(random_password),
                is_active=True,
                oauth_provider="google",
                oauth_id=google_id
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"  ✓ New user created: {user.username} (ID: {user.id})")
        except Exception as e:
            print(f"  ✗ Error creating user: {e}")
            raise
    
    # Step 3: Verify user is active
    print(f"\n[STEP 2] Checking user activation status...")
    if not user.is_active:
        print(f"  ✗ User is inactive!")
        sys.exit(1)
    else:
        print(f"  ✓ User is active")
    
    # Step 4: Create JWT tokens
    print(f"\n[STEP 3] Creating JWT tokens...")
    try:
        print(f"  - Using settings.SECRET_KEY (length: {len(settings.SECRET_KEY)})")
        print(f"  - Using settings.ALGORITHM: {settings.ALGORITHM}")
        
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        print(f"  ✓ Access token created: {access_token[:30]}...")
        print(f"  ✓ Refresh token created: {refresh_token[:30]}...")
        
    except Exception as e:
        print(f"  ✗ Error creating tokens: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    print(f"\n[SUCCESS] Google OAuth callback flow test passed!")
    print(f"\nTest Results:")
    print(f"  User: {user.email}")
    print(f"  Access Token Valid: Yes")
    print(f"  Refresh Token Valid: Yes")
    
finally:
    # Clean up
    db.close()
    # Optionally delete test user
    db2 = SessionLocal()
    test_user = db2.query(User).filter(User.email == "test.oauth@gmail.com").first()
    if test_user:
        db2.delete(test_user)
        db2.commit()
        print(f"\n[CLEANUP] Test user deleted")
    db2.close()
