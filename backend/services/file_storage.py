"""
File storage service for secure document management with per-user isolation.
Handles upload, retrieval, deletion, and validation.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException, status
import hashlib

logger = logging.getLogger(__name__)

from backend.config import settings

class FileStorageService:
    """Manages file storage with security and per-user isolation"""
    
    def __init__(self):
        """Initialize file storage service"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        self.allowed_extensions = set(settings.ALLOWED_EXTENSIONS)
        
        # Create upload directory if it doesn't exist
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Ensure upload directory exists"""
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ready: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise
    
    def get_user_upload_dir(self, user_id: int) -> Path:
        """
        Get the upload directory for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Path: User's upload directory
        """
        user_dir = self.upload_dir / f"user_{user_id}"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _validate_file_extension(self, filename: str) -> bool:
        """
        Validate file extension.
        
        Args:
            filename: Original filename
            
        Returns:
            bool: True if extension is allowed
        """
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return extension in self.allowed_extensions
    
    def _validate_file_size(self, file_size: int) -> bool:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            
        Returns:
            bool: True if size is within limit
        """
        return file_size <= self.max_file_size
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove suspicious characters
        unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        
        return filename
    
    def save_file(
        self,
        user_id: int,
        filename: str,
        file_content: bytes,
        original_filename: Optional[str] = None
    ) -> tuple[str, int, str]:
        """
        Save an uploaded file with security checks.
        
        Args:
            user_id: User ID (for directory isolation)
            filename: Filename to save as
            file_content: File binary content
            original_filename: Original filename from upload
            
        Returns:
            tuple: (relative_path, file_size, file_hash)
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Validate extension
            if not self._validate_file_extension(original_filename or filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
                )
            
            # Validate size
            file_size = len(file_content)
            if not self._validate_file_size(file_size):
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE_MB} MB"
                )
            
            # Sanitize filename
            safe_filename = self._sanitize_filename(original_filename or filename)
            
            # Get user directory
            user_dir = self.get_user_upload_dir(user_id)
            
            # Construct full path
            file_path = user_dir / safe_filename
            
            # Verify path is still within user directory (prevent path traversal)
            try:
                file_path.resolve().relative_to(user_dir.resolve())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file path"
                )
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Calculate file hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Get relative path for storage in database
            relative_path = str(file_path.relative_to(self.upload_dir))
            
            logger.info(f"File saved for user {user_id}: {relative_path} ({file_size} bytes)")
            
            return relative_path, file_size, file_hash
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file"
            )
    
    def get_file(self, user_id: int, relative_path: str) -> bytes:
        """
        Retrieve a file with access control.
        
        Args:
            user_id: User ID requesting file
            relative_path: Relative path to file
            
        Returns:
            bytes: File content
            
        Raises:
            HTTPException: If file not found or access denied
        """
        try:
            # Verify path is within user directory
            file_path = self.upload_dir / relative_path
            user_dir = self.get_user_upload_dir(user_id)
            
            # Security check: ensure file is in user's directory
            try:
                file_path.resolve().relative_to(user_dir.resolve())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Check file exists
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Read file
            with open(file_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"File retrieved for user {user_id}: {relative_path}")
            return content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving file for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve file"
            )
    
    def delete_file(self, user_id: int, relative_path: str) -> bool:
        """
        Delete a file with access control.
        
        Args:
            user_id: User ID requesting deletion
            relative_path: Relative path to file
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            HTTPException: If access denied or file not found
        """
        try:
            # Verify path is within user directory
            file_path = self.upload_dir / relative_path
            user_dir = self.get_user_upload_dir(user_id)
            
            # Security check
            try:
                file_path.resolve().relative_to(user_dir.resolve())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Check file exists
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            # Delete file
            file_path.unlink()
            
            logger.info(f"File deleted for user {user_id}: {relative_path}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting file for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
    
    def delete_user_directory(self, user_id: int) -> bool:
        """
        Delete all files for a user (called when user is deleted).
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful
        """
        try:
            user_dir = self.get_user_upload_dir(user_id)
            if user_dir.exists():
                shutil.rmtree(user_dir)
                logger.info(f"User directory deleted: {user_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user directory {user_id}: {e}")
            return False
    
    def list_user_files(self, user_id: int) -> List[dict]:
        """
        List all files for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[dict]: List of file metadata
        """
        try:
            user_dir = self.get_user_upload_dir(user_id)
            files = []
            
            if user_dir.exists():
                for file_path in user_dir.iterdir():
                    if file_path.is_file():
                        stat = file_path.stat()
                        relative_path = str(file_path.relative_to(self.upload_dir))
                        files.append({
                            "filename": file_path.name,
                            "path": relative_path,
                            "size_bytes": stat.st_size,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
            
            logger.debug(f"Listed {len(files)} files for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files for user {user_id}: {e}")
            return []
    
    def get_user_storage_usage(self, user_id: int) -> int:
        """
        Get total storage used by a user in bytes.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Total size in bytes
        """
        try:
            user_dir = self.get_user_upload_dir(user_id)
            total_size = 0
            
            if user_dir.exists():
                for file_path in user_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            return total_size
            
        except Exception as e:
            logger.error(f"Error calculating storage usage for user {user_id}: {e}")
            return 0


# Global instance
_storage_service: Optional[FileStorageService] = None

def get_file_storage_service() -> FileStorageService:
    """Get or create file storage service singleton"""
    global _storage_service
    if _storage_service is None:
        _storage_service = FileStorageService()
    return _storage_service
