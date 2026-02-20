import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

from backend.database import get_db, User
from backend.models import UserCreate, UserOut, Token
from backend.auth.security import get_password_hash, verify_password, create_access_token, get_current_active_user

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered: {new_user.username}")
    return new_user

@router.post("/login", response_model=Token)
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - requires prior registration"""
    # First check by username
    user = db.query(User).filter(User.username == login_request.username).first()
    
    # If not found by username, try by email
    if not user:
        user = db.query(User).filter(User.email == login_request.username).first()
    
    # User must exist and password must match
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not registered. Please register first.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    logger.info(f"User logged in: {user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
