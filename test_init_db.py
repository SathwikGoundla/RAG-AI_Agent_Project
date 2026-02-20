#!/usr/bin/env python
"""Test init_db flow same as main.py does"""

import sys
sys.path.insert(0, '.')

from backend.config import settings
from backend.database import init_db, SessionLocal, User, Base, engine

print("[TEST] Starting init_db simulation...")

# This is exactly what init_db does
try:
    print("[1] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("[1] OK - Tables created")
except Exception as e:
    print(f"[1] ERROR - Failed to create tables: {e}")
    sys.exit(1)

# Now try to query like init_db does
if getattr(settings, 'AUTO_CREATE_ADMIN', True):
    try:
        print("[2] Creating session...")
        db = SessionLocal()
        print("[2] OK - Session created")
        
        print("[3] Querying User table...")
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        print(f"[3] OK - Query succeeded. Admin exists: {admin_user is not None}")
        
        if not admin_user:
            print("[4] Creating admin user...")
            from backend.auth.security import get_password_hash
            admin_user = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="System Administrator",
                is_active=True,
                is_verified=True,
                role="admin",
                oauth_provider=None,
                oauth_id=None,
            )
            db.add(admin_user)
            db.commit()
            print("[4] OK - Admin user created")
        
        db.close()
        
    except Exception as e:
        print(f"[ERROR] Failed during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("[TEST] SUCCESS - All tests passed!")
