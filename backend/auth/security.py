"""
Security utilities for JWT token management, password hashing, and user authentication.
Implements werkzeug PBKDF2 hashing, JWT token generation/validation, and OAuth2 dependencies.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from werkzeug.security import generate_password_hash, check_password_hash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

logger = logging.getLogger(__name__)

from backend.config import settings
from backend.database import get_db, User
from backend.models import TokenData

# ============================================
# OAuth2 Scheme
# ============================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    description="Enter JWT token from login response"
)

# ============================================
# Password Hashing Functions
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its werkzeug PBKDF2 hash.
    
    Args:
        plain_password: User-provided password
        hashed_password: Stored werkzeug hash from database
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    try:
        return check_password_hash(hashed_password, plain_password)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a plain password using werkzeug PBKDF2.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Werkzeug PBKDF2 hashed password
    """
    try:
        return generate_password_hash(password, method='pbkdf2:sha256')
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise

# ============================================
# JWT Token Functions
# ============================================

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with optional custom expiration.
    
    Args:
        data: Payload data (should include "sub" for username)
        expires_delta: Custom expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise

def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token with extended expiration.
    
    Args:
        data: Payload data (should include "sub" for username)
        expires_delta: Custom expiration time, defaults to 7 days
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh token valid for 7 days
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {str(e)}")
        raise

# ============================================
# Token Decoding and Validation
# ============================================

class TokenData:
    """Enhanced token data class with type checking"""
    def __init__(self, username: Optional[str] = None, user_id: Optional[int] = None):
        self.username = username
        self.user_id = user_id

def decode_token(
    token: str,
    token_type: str = "access"
) -> Optional[TokenData]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        token_type: Type of token ("access" or "refresh")
        
    Returns:
        TokenData: Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
        
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None:
            logger.warning("Token missing 'sub' claim")
            return None
        
        return TokenData(username=username, user_id=user_id)
        
    except JWTError as e:
        logger.debug(f"JWT validation failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        return None

# ============================================
# FastAPI Dependencies
# ============================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    Validates token and retrieves user from database.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 404: User not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode and validate token
    token_data = decode_token(token, token_type="access")
    
    if token_data is None:
        logger.warning("Failed to decode access token")
        raise credentials_exception
    
    # Retrieve user from database
    try:
        user = db.query(User).filter(
            User.username == token_data.username
        ).first()
        
        if user is None:
            logger.warning(f"Token for non-existent user: {token_data.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Error retrieving user from token: {str(e)}")
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException 403: User is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is an admin.
    
    Args:
        current_user: Current authenticated active user
        
    Returns:
        User: Current admin user
        
    Raises:
        HTTPException 403: User is not an admin
    """
    if current_user.role != "admin":
        logger.warning(f"Non-admin user {current_user.username} attempted admin operation")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user
