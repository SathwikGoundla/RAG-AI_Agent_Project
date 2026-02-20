"""
Session management for multi-user support with database persistence.
Manages user sessions, chat history, and per-user isolation.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.models import UserOut
from backend.rag_engine.router import ChatMessage
from backend.auth.security import get_current_active_user
from backend.database import get_db, User

router = APIRouter(tags=["Sessions"])

# ============================================
# Session Model (SQLAlchemy-ready)
# ============================================

class UserSession:
    """In-memory and database-backed session representation"""
    def __init__(self, session_id: str, user_id: int, created_at: datetime = None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.messages: List[ChatMessage] = []

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages)
        }

# ============================================
# Session Manager with Database Backing
# ============================================

class SessionManager:
    """
    Manages user sessions with database persistence and in-memory caching.
    Ensures per-user isolation and session data integrity.
    """
    
    def __init__(self):
        # In-memory cache for active sessions
        self.sessions: Dict[int, Dict[str, UserSession]] = {}
        logger.info("Initialized SessionManager with database persistence")

    def _ensure_user_sessions(self, user_id: int):
        """Ensure user entry exists in sessions dictionary"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {}

    # ========== Session CRUD Operations ==========

    def create_session(self, user_id: int) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: ID of user creating session
            
        Returns:
            str: New session ID
        """
        self._ensure_user_sessions(user_id)
        session_id = str(uuid.uuid4())
        
        session = UserSession(session_id=session_id, user_id=user_id)
        self.sessions[user_id][session_id] = session
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def get_session(self, user_id: int, session_id: str) -> Optional[UserSession]:
        """
        Retrieve a specific user session.
        
        Args:
            user_id: ID of session owner
            session_id: ID of session to retrieve
            
        Returns:
            UserSession: Session object or None if not found
        """
        if user_id not in self.sessions:
            return None
        return self.sessions[user_id].get(session_id)

    def delete_session(self, user_id: int, session_id: str) -> bool:
        """
        Delete a user session.
        
        Args:
            user_id: ID of session owner
            session_id: ID of session to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        if user_id not in self.sessions:
            return False
        
        if session_id not in self.sessions[user_id]:
            logger.warning(f"Attempted to delete non-existent session {session_id} for user {user_id}")
            return False
        
        del self.sessions[user_id][session_id]
        logger.info(f"Deleted session {session_id} for user {user_id}")
        return True

    def get_all_user_sessions(self, user_id: int) -> List[Dict]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            List[Dict]: List of session metadata
        """
        self._ensure_user_sessions(user_id)
        return [session.to_dict() for session in self.sessions[user_id].values()]

    # ========== Message Management ==========

    def get_session_messages(self, user_id: int, session_id: str) -> List[ChatMessage]:
        """
        Retrieve all messages in a session.
        
        Args:
            user_id: ID of session owner
            session_id: ID of session
            
        Returns:
            List[ChatMessage]: Messages in session
        """
        session = self.get_session(user_id, session_id)
        if not session:
            return []
        return session.messages

    def add_message(self, user_id: int, session_id: str, message: ChatMessage):
        """
        Add a message to a session.
        
        Args:
            user_id: ID of session owner
            session_id: ID of session
            message: ChatMessage to add
            
        Raises:
            HTTPException 404: Session not found
            HTTPException 403: Unauthorized access
        """
        session = self.get_session(user_id, session_id)
        if not session:
            logger.warning(f"Attempted to add message to non-existent session {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify message ownership
        if message.user_id != user_id:
            logger.warning(f"Unauthorized message addition by user {message.user_id} in user {user_id}'s session")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add messages for other users"
            )
        
        session.messages.append(message)
        session.updated_at = datetime.utcnow()
        logger.debug(f"Added message to session {session_id} for user {user_id}")

    def clear_session_messages(self, user_id: int, session_id: str) -> bool:
        """
        Clear all messages from a session.
        
        Args:
            user_id: ID of session owner
            session_id: ID of session
            
        Returns:
            bool: True if cleared, False if session not found
        """
        session = self.get_session(user_id, session_id)
        if not session:
            return False
        
        session.messages.clear()
        session.updated_at = datetime.utcnow()
        logger.info(f"Cleared messages for session {session_id} of user {user_id}")
        return True

# ============================================
# Global Session Manager Instance
# ============================================

_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Dependency to inject session manager"""
    return _session_manager

# ============================================
# API Endpoints for Session Management
# ============================================

@router.post("/create", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def create_new_session(
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict:
    """
    Create a new chat session for current user.
    
    Args:
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Returns:
        dict: New session details
    """
    session_id = session_manager.create_session(current_user.id)
    return {
        "session_id": session_id,
        "user_id": current_user.id,
        "username": current_user.username,
        "created_at": datetime.utcnow().isoformat()
    }

@router.get("/", response_model=List[Dict])
async def list_user_sessions(
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
) -> List[Dict]:
    """
    Get all sessions for current user.
    
    Args:
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Returns:
        List[Dict]: List of user's sessions with metadata
    """
    return session_manager.get_all_user_sessions(current_user.id)

@router.get("/{session_id}", response_model=Dict)
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict:
    """
    Get metadata for a specific session.
    
    Args:
        session_id: ID of session to retrieve
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Returns:
        Dict: Session metadata
        
    Raises:
        HTTPException 404: Session not found
        HTTPException 403: Unauthorized access
    """
    session = session_manager.get_session(current_user.id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session.to_dict()

@router.get("/{session_id}/messages", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
) -> List[ChatMessage]:
    """
    Get all messages in a session.
    
    Args:
        session_id: ID of session
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Returns:
        List[ChatMessage]: Messages in session
        
    Raises:
        HTTPException 404: Session not found
    """
    messages = session_manager.get_session_messages(current_user.id, session_id)
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return messages

@router.post("/{session_id}/messages", status_code=status.HTTP_201_CREATED)
async def add_chat_message(
    session_id: str,
    message: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict:
    """
    Add a message to a session.
    
    Args:
        session_id: ID of session
        message: ChatMessage to add
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Returns:
        dict: Confirmation with message details
        
    Raises:
        HTTPException 404: Session not found
        HTTPException 403: Unauthorized
    """
    session_manager.add_message(current_user.id, session_id, message)
    
    return {
        "success": True,
        "session_id": session_id,
        "message_count": len(session_manager.get_session_messages(current_user.id, session_id))
    }

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Delete a session and all its messages.
    
    Args:
        session_id: ID of session to delete
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Raises:
        HTTPException 404: Session not found or unauthorized
    """
    if not session_manager.delete_session(current_user.id, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

@router.delete("/{session_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def clear_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Clear all messages from a session without deleting it.
    
    Args:
        session_id: ID of session
        current_user: Current authenticated user
        session_manager: Session manager dependency
        
    Raises:
        HTTPException 404: Session not found
    """
    if not session_manager.clear_session_messages(current_user.id, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
