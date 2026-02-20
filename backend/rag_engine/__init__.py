"""
RAG Engine Module
Core Retrieval-Augmented Generation pipeline components
"""

# Note: router import removed to prevent circular import dependency
# router is imported directly in backend/main.py where needed
from .retriever import RetrieverService, get_retriever_service
from .generator import ResponseGenerator
from .embeddings import EmbeddingService, get_embedding_service
from .vector_store import ChromaDBManager, get_chroma_manager
from .context_manager import ContextManager, get_context_manager

__all__ = [
    'RetrieverService',
    'get_retriever_service',
    'ResponseGenerator',
    'EmbeddingService',
    'get_embedding_service',
    'ChromaDBManager',
    'get_chroma_manager',
    'ContextManager',
    'get_context_manager'
]
