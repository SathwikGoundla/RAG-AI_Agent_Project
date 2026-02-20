"""
User login and authentication endpoints with JWT token management.
Handles login, logout, token refresh, and user profile endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from backend.database import get_db, User
from backend.models import UserOut, Token
from backend.auth.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    decode_token,
    TokenData
)
from backend.config import settings

router = APIRouter(tags=["Authentication"])

# --- Request/Response Models ---

class LoginRequest(BaseModel):
    """Login request with username and password"""
    username: str
    password: str

class LoginResponse(Token):
    """Extended token response with user info"""
    user: UserOut
    expires_in: int  # seconds until expiration

class RefreshTokenRequest(Token):
    """Request model for token refresh"""
    refresh_token: str

# --- Login Endpoint ---

@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and return JWT access and refresh tokens.
    
    Args:
        login_request: Contains username and password
        db: Database session dependency
        
    Returns:
        LoginResponse: Contains access_token, refresh_token, user info, and expiration
        
    Raises:
        HTTPException 401: Invalid username or password
        HTTPException 404: User not found
    """
    
    # Retrieve user from database - try username first, then email
    user = db.query(User).filter(User.username == login_request.username).first()
    
    # If not found by username, try by email (allows login with email)
    if not user:
        user = db.query(User).filter(User.email == login_request.username).first()
    
    if not user:
        logger.warning("Login attempt with invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_request.password, user.hashed_password):
        logger.warning("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning("Login attempt for inactive account")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    try:
        # Create tokens
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        logger.info(f"User logged in successfully: {user.username} (ID: {user.id})")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserOut(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            ),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Error during login for user {user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again."
        )

# --- Token Refresh Endpoint ---

@router.post("/refresh", response_model=LoginResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    Refresh expired access token using refresh token.
    
    Args:
        request: Contains refresh token
        db: Database session dependency
        
    Returns:
        LoginResponse: New access token with user info
        
    Raises:
        HTTPException 401: Invalid or expired refresh token
    """
    
    # Validate refresh token
    token_data = decode_token(request.refresh_token, token_type="refresh")
    
    if not token_data:
        logger.warning("Invalid or expired refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retrieve user
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if not user:
        logger.warning(f"Refresh token for non-existent user: {token_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        logger.warning(f"Refresh token for inactive user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    try:
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        logger.info(f"Token refreshed for user: {user.username}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=request.refresh_token,  # Return same refresh token
            token_type="bearer",
            user=UserOut(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            ),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh."
        )

# --- User Profile Endpoint ---

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserOut:
    """
    Get current authenticated user's profile.
    
    Args:
        current_user: Current authenticated user (from JWT token)
        
    Returns:
        UserOut: Current user's profile information
    """
    logger.debug(f"User profile accessed: {current_user.username}")
    
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

# --- Logout Endpoint ---

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user (invalidates token on client-side).
    Note: Tokens are stateless JWTs, so server-side invalidation would require a blacklist.
    Client should delete tokens from storage.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Logout confirmation message
    """
    logger.info(f"User logged out: {current_user.username}")
    
    return {
        "message": "Successfully logged out",
        "username": current_user.username,
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Token Validation Endpoint ---

@router.post("/validate-token", status_code=status.HTTP_200_OK)
async def validate_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate if provided token is still valid.
    
    Args:
        current_user: Current authenticated user (auto-validates token)
        
    Returns:
        dict: Token validation status and user info
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
