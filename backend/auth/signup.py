"""
User registration and signup endpoints with secure bcrypt hashing.
Handles user account creation, email validation, and duplicate prevention.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Optional

logger = logging.getLogger(__name__)

from backend.database import get_db, User
from backend.models import UserCreate, UserOut
from backend.auth.security import get_password_hash

router = APIRouter(tags=["Authentication"])

# --- Validation Functions ---

def is_strong_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, None

def username_available(username: str, db: Session) -> bool:
    """Check if username is available for registration"""
    return db.query(User).filter(User.username == username).first() is None

def email_available(email: str, db: Session) -> bool:
    """Check if email is available for registration"""
    return db.query(User).filter(User.email == email).first() is None

# --- Signup Endpoint ---

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> UserOut:
    """
    Register a new user account.
    
    Args:
        user_in: UserCreate model with username, email, password, full_name
        db: Database session dependency
        
    Returns:
        UserOut: Created user details (without password hash)
        
    Raises:
        HTTPException 400: Username/email already exists or invalid input
        HTTPException 422: Weak password
    """
    
    # Strip whitespace
    user_in.username = user_in.username.strip()
    user_in.email = user_in.email.strip().lower()
    
    # Validate username length
    if len(user_in.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long"
        )
    
    if len(user_in.username) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must not exceed 50 characters"
        )
    
    # Validate username contains only alphanumeric and underscores
    if not user_in.username.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username can only contain alphanumeric characters, hyphens, and underscores"
        )
    
    # Check if username is available
    if not username_available(user_in.username, db):
        logger.warning("Signup attempt with existing username")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email is available
    if not email_available(user_in.email, db):
        logger.warning("Signup attempt with existing email")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_strong, error_msg = is_strong_password(user_in.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg
        )
    
    try:
        # Create new user with hashed password
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name or "",
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered successfully (ID: {new_user.id})")
        
        return UserOut(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
            created_at=new_user.created_at
        )
        
    except IntegrityError as e:
        """Handle database constraint violations (duplicate username/email)"""
        db.rollback()
        error_str = str(e).lower()
        
        logger.warning(f"Integrity constraint violation during signup: {str(e)}")
        
        if "username" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        elif "email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account information is already in use"
            )
    
    except SQLAlchemyError as e:
        """Handle other SQLAlchemy errors"""
        db.rollback()
        logger.error(f"SQLAlchemy error during user registration: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error. Please try again."
        )
    
    except Exception as e:
        """Handle unexpected errors"""
        db.rollback()
        logger.error(f"Unexpected error during user registration: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {type(e).__name__}. Please contact support."
        )

@router.post("/check-username/{username}")
async def check_username_availability(username: str, db: Session = Depends(get_db)):
    """
    Check if a username is available for registration.
    
    Args:
        username: Username to check
        db: Database session dependency
        
    Returns:
        dict: {"available": bool, "username": str}
    """
    username = username.strip()
    
    if len(username) < 3:
        return {"available": False, "username": username, "reason": "Too short (minimum 3 characters)"}
    
    available = username_available(username, db)
    return {
        "available": available,
        "username": username,
        "reason": None if available else "Username already taken"
    }

@router.post("/check-email/{email}")
async def check_email_availability(email: str, db: Session = Depends(get_db)):
    """
    Check if an email is available for registration.
    
    Args:
        email: Email to check
        db: Database session dependency
        
    Returns:
        dict: {"available": bool, "email": str}
    """
    email = email.strip().lower()
    available = email_available(email, db)
    return {
        "available": available,
        "email": email,
        "reason": None if available else "Email already registered"
    }
