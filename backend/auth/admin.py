"""
Admin management endpoints for user and system administration.
Requires admin role for all endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from backend.database import (
    get_db, User, Document, DocumentChunk, AuditLog, RefreshToken
)
from backend.models import (
    UserListResponse, UserOutAdmin, AdminUserStatsResponse,
    StorageStatsResponse, AdminActionResponse, AuditLogResponse,
    AuditLogItem, SystemHealthResponse
)
from backend.auth.security import get_current_admin_user, get_password_hash
from backend.config import settings

router = APIRouter(tags=["Admin"])

# ============================================
# User Management Endpoints
# ============================================

@router.get("/users", response_model=UserListResponse)
async def list_all_users(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all registered users (admin only).
    
    Args:
        current_admin: Current admin user
        db: Database session
        skip: Number of records to skip
        limit: Number of records to return (max 100)
        
    Returns:
        UserListResponse: List of all users with metadata
    """
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.role == "admin").count()
        
        users = db.query(User).offset(skip).limit(min(limit, 100)).all()
        
        users_out = []
        for user in users:
            doc_count = db.query(Document).filter(Document.user_id == user.id).count()
            users_out.append(
                UserOutAdmin(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    is_active=user.is_active,
                    role=user.role,
                    is_verified=user.is_verified,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                    last_login=user.last_login,
                    documents_count=doc_count
                )
            )
        
        logger.info(f"Admin {current_admin.username} listed {len(users)} users")
        
        return UserListResponse(
            total_users=total_users,
            active_users=active_users,
            admin_users=admin_users,
            users=users_out
        )
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/users/{user_id}/stats", response_model=AdminUserStatsResponse)
async def get_user_stats(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific user.
    
    Args:
        user_id: User ID to get stats for
        current_admin: Current admin user
        db: Database session
        
    Returns:
        AdminUserStatsResponse: User statistics
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate storage used
        documents = db.query(Document).filter(Document.user_id == user_id).all()
        storage_used = sum(doc.file_size or 0 for doc in documents)
        
        total_documents = len(documents)
        total_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.user_id == user_id
        ).count()
        
        # Get last activity from audit log
        last_activity = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).first()
        
        return AdminUserStatsResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_queries=0,  # Can track with audit logs
            total_quizzes_taken=0,  # Can expand for quiz stats
            storage_used_bytes=storage_used,
            joined_date=user.created_at,
            last_activity=last_activity.timestamp if last_activity else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    reason: Optional[str] = None
):
    """
    Disable a user account (prevents login but preserves data).
    
    Args:
        user_id: User ID to disable
        current_admin: Current admin user
        db: Database session
        reason: Reason for disabling account
        
    Returns:
        AdminActionResponse: Action result
    """
    try:
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable your own account"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.add(user)
        
        # Revoke all refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        
        # Log action
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="user_disable",
            resource_type="user",
            resource_id=str(user_id),
            status="success",
            status_code=200,
            details=f"Disabled user {user.username}. Reason: {reason}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Admin {current_admin.username} disabled user {user.username}")
        
        return AdminActionResponse(
            success=True,
            message=f"User {user.username} has been disabled",
            action="disable",
            affected_user=user.username,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error disabling user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable user"
        )

@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    reason: Optional[str] = None
):
    """
    Delete a user account and all associated data.
    
    Args:
        user_id: User ID to delete
        current_admin: Current admin user
        db: Database session
        reason: Reason for deletion
        
    Returns:
        AdminActionResponse: Action result
    """
    try:
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete all user data (cascade handled by database)
        db.delete(user)
        
        # Log action
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="user_delete",
            resource_type="user",
            resource_id=str(user_id),
            status="success",
            status_code=200,
            details=f"Deleted user {user.username}. Reason: {reason}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.warning(f"Admin {current_admin.username} deleted user {user.username}")
        
        return AdminActionResponse(
            success=True,
            message=f"User {user.username} and all associated data have been deleted",
            action="delete",
            affected_user=user.username,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Admin reset user password.
    
    Args:
        user_id: User ID
        new_password: New password
        current_admin: Current admin user
        db: Database session
        
    Returns:
        AdminActionResponse: Action result
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.hashed_password = get_password_hash(new_password)
        
        # Revoke all refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        
        # Log action
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="password_reset",
            resource_type="user",
            resource_id=str(user_id),
            status="success",
            status_code=200,
            details=f"Admin reset password for user {user.username}"
        )
        db.add(audit_log)
        db.add(user)
        db.commit()
        
        logger.info(f"Admin {current_admin.username} reset password for user {user.username}")
        
        return AdminActionResponse(
            success=True,
            message=f"Password reset for {user.username}",
            action="reset_password",
            affected_user=user.username,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# ============================================
# System Statistics Endpoints
# ============================================

@router.get("/stats/storage", response_model=StorageStatsResponse)
async def get_storage_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system storage and vector database statistics.
    
    Args:
        current_admin: Current admin user
        db: Database session
        
    Returns:
        StorageStatsResponse: Storage statistics
    """
    try:
        total_documents = db.query(Document).count()
        total_chunks = db.query(DocumentChunk).count()
        
        # Calculate total storage
        storage_result = db.query(func.sum(Document.file_size)).scalar()
        total_storage = storage_result or 0
        
        # Average document size
        avg_size_result = db.query(func.avg(Document.file_size)).scalar()
        avg_size = int(avg_size_result) if avg_size_result else 0
        
        return StorageStatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_storage_bytes=int(total_storage),
            average_document_size=avg_size,
            vector_db_size_bytes=0,  # Can be enhanced with ChromaDB stats
            database_size_bytes=0,  # Can be enhanced with actual DB stats
            system_uptime_seconds=0  # Can track server start time
        )
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage statistics"
        )

# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    days: int = 7
):
    """
    Get audit logs for monitoring system activities.
    
    Args:
        current_admin: Current admin user
        db: Database session
        skip: Number of records to skip
        limit: Number of records to return
        user_id: Filter by user ID
        action: Filter by action type
        days: Days of logs to retrieve (default 7)
        
    Returns:
        AuditLogResponse: Audit logs
    """
    try:
        query = db.query(AuditLog)
        
        # Filter by date
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(AuditLog.timestamp >= since)
        
        # Optional filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        
        total_logs = query.count()
        logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(min(limit, 100)).all()
        
        audit_items = [
            AuditLogItem(
                id=log.id,
                user_id=log.user_id,
                username=db.query(User).filter(User.id == log.user_id).first().username if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                status=log.status,
                status_code=log.status_code,
                ip_address=log.ip_address,
                timestamp=log.timestamp,
                details=log.details
            )
            for log in logs
        ]
        
        return AuditLogResponse(total_logs=total_logs, logs=audit_items)
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )

# ============================================
# System Health Endpoint
# ============================================

@router.get("/health", response_model=SystemHealthResponse)
async def system_health(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system health status and metrics.
    
    Args:
        current_admin: Current admin user
        db: Database session
        
    Returns:
        SystemHealthResponse: System health information
    """
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        db_status = "healthy"
        
        # Get active sessions (logged in users with recent activity)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= five_minutes_ago,
            AuditLog.action == "login"
        ).count()
        
        return SystemHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            database_status=db_status,
            vector_store_status="healthy",  # Can enhance with actual check
            uptime_seconds=0,  # Can track server start time
            active_sessions=recent_logs,
            message="All systems operational"
        )
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return SystemHealthResponse(
            status="degraded",
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            database_status="error" if "database" in str(e).lower() else "healthy",
            vector_store_status="error" if "vector" in str(e).lower() else "healthy",
            uptime_seconds=0,
            active_sessions=0,
            message=f"System error: {str(e)}"
        )
