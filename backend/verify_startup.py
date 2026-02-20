#!/usr/bin/env python3
"""
Backend startup verification script.
Tests database initialization, admin user creation, and basic API functionality.
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("startup_check")

def check_environment():
    """Check if required environment variables are set"""
    logger.info("✓ Checking environment configuration...")
    from backend.config import settings
    
    checks = {
        "SECRET_KEY": settings.SECRET_KEY != "your-super-secret-key-change-in-production",
        "DATABASE_URL": settings.DATABASE_URL is not None,
        "UPLOAD_DIR": settings.UPLOAD_DIR is not None,
        "OPENAI_API_KEY_OPTIONAL": True,  # Optional
    }
    
    for key, status in checks.items():
        if status:
            logger.info(f"  ✓ {key}: configured")
        else:
            logger.warning(f"  ⚠ {key}: not configured")
    
    return all([v for k, v in checks.items() if "OPTIONAL" not in k])

def check_storage_dirs():
    """Check if storage directories exist"""
    logger.info("✓ Checking storage directories...")
    from backend.config import settings
    
    dirs = [
        settings.UPLOAD_DIR,
        settings.CACHE_DIR,
        settings.LOG_DIR,
        settings.CHROMA_PERSIST_DIRECTORY
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        if path.exists():
            logger.info(f"  ✓ {dir_path}: exists")
        else:
            logger.info(f"  → Creating {dir_path}...")
            path.mkdir(parents=True, exist_ok=True)
    
    return True

def check_database():
    """Check if database can be initialized"""
    logger.info("✓ Checking database...")
    try:
        from backend.database import init_db, SessionLocal, User
        
        init_db()
        logger.info("  ✓ Database tables created")
        
        # Check if admin user exists
        db = SessionLocal()
        from backend.config import settings
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        
        if admin_user:
            logger.info(f"  ✓ Admin user '{settings.ADMIN_USERNAME}' exists")
        else:
            logger.warning(f"  ⚠ Admin user not found (will be created on startup)")
        
        db.close()
        return True
    except Exception as e:
        logger.error(f"  ✗ Database error: {e}")
        return False

def check_imports():
    """Check if all critical imports work"""
    logger.info("✓ Checking imports...")
    
    imports_to_check = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("SQLAlchemy", "from sqlalchemy import create_engine"),
        ("Pydantic", "from pydantic import BaseModel"),
        ("Security", "from backend.auth.security import get_current_user"),
        ("Admin Router", "from backend.auth import admin"),
        ("File Storage", "from backend.services.file_storage import FileStorageService"),
    ]
    
    for name, import_stmt in imports_to_check:
        try:
            exec(import_stmt)
            logger.info(f"  ✓ {name} imported successfully")
        except Exception as e:
            logger.error(f"  ✗ {name} import failed: {e}")
            return False
    
    return True

def check_api():
    """Check if FastAPI app initializes"""
    logger.info("✓ Checking FastAPI application...")
    try:
        from backend.main import app
        logger.info("  ✓ FastAPI app initialized")
        
        # Check if routes are registered
        routes = [route.path for route in app.routes]
        logger.info(f"  ✓ {len(routes)} routes registered")
        
        # Check for critical endpoints
        critical_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/admin/users",
            "/docs"
        ]
        
        for endpoint in critical_endpoints:
            if endpoint in routes or any(endpoint in str(route) for route in app.routes):
                logger.info(f"  ✓ {endpoint} registered")
            else:
                logger.warning(f"  ⚠ {endpoint} not found")
        
        return True
    except Exception as e:
        logger.error(f"  ✗ FastAPI app error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all startup checks"""
    logger.info("\n" + "="*60)
    logger.info("Advanced RAG System - Backend Startup Verification")
    logger.info("="*60 + "\n")
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Storage Directories", check_storage_dirs),
        ("Database", check_database),
        ("Imports", check_imports),
        ("API Routes", check_api),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"\n✗ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
        logger.info("")
    
    # Summary
    logger.info("="*60)
    logger.info("STARTUP VERIFICATION SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.info("\n🎉 All checks passed! Backend is ready to start.")
        logger.info("\nTo start the backend, run:")
        logger.info("  cd backend")
        logger.info("  python -m uvicorn main:app --reload")
        return 0
    else:
        logger.error(f"\n⚠ {total - passed} check(s) failed. Please fix the issues before starting.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
