"""
Document Processing Module
Handles document upload, text extraction, chunking, and multi-format support.
"""

from .router import router
from .services import DocumentProcessorService, get_document_processor_service

__all__ = ['router', 'DocumentProcessorService', 'get_document_processor_service']
