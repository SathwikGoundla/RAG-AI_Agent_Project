"""
RAG Engine Router
Handles chat and query endpoints for the RAG pipeline
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from backend.auth.security import get_current_active_user
from backend.models import UserOut
from backend.rag_engine.retriever import RetrieverService, get_retriever_service
from backend.rag_engine.generator import ResponseGenerator
from backend.rag_engine.context_manager import ContextManager
from backend.database import get_db
from backend.utils.bilingual_handler import BilingualHandler, BilingualContextManager, Language

# ============================================
# Pydantic Models
# ============================================

class QueryRequest(BaseModel):
    """User query request"""
    question: str
    language: Optional[str] = "english"
    document_ids: Optional[List[str]] = None
    n_results: Optional[int] = 5


class QueryResponse(BaseModel):
    """Response to user query"""
    answer: str
    sources: List[Dict[str, Any]]
    language: str
    model_used: str
    tokens_used: Dict[str, int]
    context_count: int


class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str
    language: Optional[str] = "english"
    session_id: Optional[str] = None
    include_context: Optional[bool] = True


class ChatResponse(BaseModel):
    """Chat message response"""
    message: str
    sources: List[Dict[str, Any]]
    language: str
    session_id: str


# ============================================
# Router Setup
# ============================================

router = APIRouter()


# ============================================
# Query Endpoint
# ============================================

@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def query_documents(
    request: QueryRequest,
    current_user: UserOut = Depends(get_current_active_user),
    retriever_service: RetrieverService = Depends(get_retriever_service),
    db = Depends(get_db)
):
    """
    Query documents using RAG pipeline with bilingual support.
    
    Retrieves relevant document chunks and generates an answer using LLM.
    Supports both English and Telugu queries and responses.
    
    Args:
        request: Query request with question and optional language
        current_user: Authenticated user
        retriever_service: RAG retriever service
        db: Database connection
        
    Returns:
        QueryResponse with answer, sources, and metadata
    """
    try:
        logger.info(f"User {current_user.username} querying: {request.question[:50]}...")
        
        # Validate input
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Bilingual processing
        user_language_pref = request.language if request.language else "english"
        processed_question, query_lang, response_lang = BilingualHandler.process_bilingual_query(
            request.question,
            user_language_pref
        )
        
        logger.info(f"Query language detected: {query_lang.value}, Response language: {response_lang.value}")
        
        # Retrieve relevant chunks (using processed/translated question for better matching)
        retrieved_chunks = retriever_service.retrieve_chunks(
            query_text=processed_question,
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            n_results=request.n_results
        )
        
        if not retrieved_chunks:
            logger.warning(f"No documents found for user {current_user.username}")
            
            # Return message in appropriate language
            if response_lang == Language.TELUGU:
                no_doc_msg = "సంబంధితమైన డాక్యుమెంట్‌లు కనుగొనబడలేదు. దయచేసి మీ ప్రశ్నకు సంబంధించిన డాక్యుమెంట్‌లను అప్‌లోడ్ చేయండి."
            else:
                no_doc_msg = "No relevant documents found. Please upload documents related to your question."
            
            return QueryResponse(
                answer=no_doc_msg,
                sources=[],
                language=response_lang.value,
                model_used="none",
                tokens_used={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                context_count=0
            )
        
        # Build context from retrieved chunks with citation info
        context_documents = []
        citations = []
        
        for idx, chunk in enumerate(retrieved_chunks):
            similarity_score = chunk.get("similarity_score", 0)
            metadata = chunk["metadata"]
            
            context_documents.append({
                "content": chunk["content"],
                "source_file": metadata.get("filename", "Unknown"),
                "page_number": metadata.get("page_number"),
                "chunk_id": metadata.get("chunk_id"),
                "chunk_index": metadata.get("chunk_index", idx),
                "similarity_score": similarity_score
            })
            
            # Create citation info
            citations.append({
                "document": metadata.get("filename", "Unknown"),
                "chunk_index": metadata.get("chunk_index", idx),
                "page": metadata.get("page_number"),
                "confidence": similarity_score,
                "similarity": similarity_score,
                "excerpt": chunk["content"][:150].strip(),
                "chunk_id": metadata.get("chunk_id")
            })
        
        # Generate response using LLM
        generator = ResponseGenerator()
        
        # Get language-specific prompt
        lang_prompt = BilingualHandler.get_language_specific_prompt(response_lang)
        
        response_data = generator.generate_response(
            query=processed_question,  # Use processed/translated query
            context_documents=context_documents,
            language=response_lang.value,
            system_prompt=lang_prompt
        )
        
        if response_data.get("status") != "success":
            logger.error(f"Error generating response: {response_data.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate response: {response_data.get('message')}"
            )
        
        # Get the generated answer
        answer = response_data.get("answer", "")
        
        # If response language is different from query language, answer is already in target language
        # If response language matches query language, answer is in that language
        
        # Format sources with citations
        sources = citations
        
        logger.info(f"Query successful for user {current_user.username} in {response_lang.value}")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            language=response_lang.value,
            model_used=response_data.get("model", "gpt-3.5-turbo"),
            tokens_used=response_data.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }),
            context_count=len(context_documents)
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in query endpoint for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


# ============================================
# Chat Endpoint (Bilingual)
# ============================================

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_documents(
    request: ChatRequest,
    current_user: UserOut = Depends(get_current_active_user),
    retriever_service: RetrieverService = Depends(get_retriever_service),
    db = Depends(get_db)
):
    """
    Chat with AI about your documents with bilingual support.
    
    Maintains conversation context and retrieves relevant document chunks
    for each message. Supports both English and Telugu conversations.
    
    Args:
        request: Chat message request
        current_user: Authenticated user
        retriever_service: RAG retriever service
        db: Database connection
        
    Returns:
        ChatResponse with assistant's reply in requested language
    """
    try:
        logger.info(f"User {current_user.username} chatting: {request.message[:50]}...")
        
        # Validate input
        if not request.message or len(request.message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Bilingual processing
        user_language_pref = request.language if request.language else "english"
        processed_message, query_lang, response_lang = BilingualHandler.process_bilingual_query(
            request.message,
            user_language_pref
        )
        
        logger.info(f"Chat message language detected: {query_lang.value}, Response language: {response_lang.value}")
        
        # Initialize context manager for conversation
        context_manager = ContextManager()
        session_id = request.session_id or context_manager.create_session(current_user.id)
        
        # Retrieve relevant chunks if requested
        sources = []
        if request.include_context:
            retrieved_chunks = retriever_service.retrieve_chunks(
                query_text=processed_message,  # Use processed/translated message
                user_id=str(current_user.id),
                n_results=5
            )
            
            # Build citations
            for idx, chunk in enumerate(retrieved_chunks):
                similarity_score = chunk.get("similarity_score", 0)
                metadata = chunk["metadata"]
                
                sources.append({
                    "document": metadata.get("filename", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", idx),

                    "page": metadata.get("page_number"),
                    "confidence": similarity_score,
                    "similarity": similarity_score,
                    "excerpt": chunk["content"][:150].strip(),
                    "chunk_id": metadata.get("chunk_id")
                })
            
            context_documents = [
                {
                    "content": chunk["content"],
                    "source_file": chunk["metadata"].get("filename", "Unknown"),
                    "page_number": chunk["metadata"].get("page_number"),
                    "chunk_index": chunk["metadata"].get("chunk_index", idx),
                    "similarity_score": chunk.get("similarity_score", 0)
                }
                for idx, chunk in enumerate(retrieved_chunks)
            ]
        else:
            context_documents = []
        
        # Get conversation history
        messages = context_manager.get_conversation_history(session_id)
        
        # Generate response with language-specific prompt
        generator = ResponseGenerator()
        lang_prompt = BilingualHandler.get_language_specific_prompt(response_lang)
        
        if context_documents:
            response_data = generator.generate_response(
                query=request.message,
                context_documents=context_documents,
                language=response_lang.value,
                system_prompt=lang_prompt
            )
        else:
            # Chat without context
            response_data = generator.generate_response(
                query=request.message,
                context_documents=[],
                language=response_lang.value,
                system_prompt=lang_prompt
            )
        
        if response_data.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response"
            )
        
        # Store messages in conversation history with language info
        context_manager.add_message(session_id, "user", request.message)
        context_manager.add_message(session_id, "assistant", response_data.get("answer", ""))
        
        logger.info(f"Chat successful for user {current_user.username} in {response_lang.value}")
        
        return ChatResponse(
            message=response_data.get("answer", ""),
            sources=sources,
            language=response_lang.value,
            session_id=session_id
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in chat endpoint for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


# ============================================
# Search Endpoint (Bilingual)
# ============================================

@router.post("/search", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def search_documents(
    request: QueryRequest,
    current_user: UserOut = Depends(get_current_active_user),
    retriever_service: RetrieverService = Depends(get_retriever_service)
):
    """
    Semantic search over documents with bilingual support.
    
    Returns matching document chunks without generating an answer.
    Useful for finding relevant information quickly. Supports English and Telugu queries.
    
    Args:
        request: Query request with search terms
        current_user: Authenticated user
        retriever_service: RAG retriever service
        
    Returns:
        List of relevant document chunks with bilingual metadata
    """
    try:
        logger.info(f"User {current_user.username} searching: {request.question[:50]}...")
        
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Bilingual processing: Detect language and translate Telugu to English for retrieval
        user_language_pref = request.language if request.language else "english"
        processed_query, search_lang, _ = BilingualHandler.process_bilingual_query(
            request.question,
            user_language_pref
        )
        
        logger.info(f"Search query language detected: {search_lang.value}, using for retrieval: {processed_query[:50]}...")
        
        # Retrieve chunks using processed/translated query
        retrieved_chunks = retriever_service.retrieve_chunks(
            query_text=processed_query,  # Use processed/translated query
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            n_results=request.n_results
        )
        
        # Format results with language metadata
        results = [
            {
                "chunk_id": chunk["metadata"].get("chunk_id"),
                "document_id": chunk["metadata"].get("document_id"),
                "filename": chunk["metadata"].get("filename", "Unknown"),
                "page_number": chunk["metadata"].get("page_number"),
                "content": chunk["content"],
                "chunk_type": chunk["metadata"].get("chunk_type", "text"),
                "similarity_score": chunk.get("similarity_score", 0),
                "query_language": search_lang.value,  # Language of original query
            }
            for chunk in retrieved_chunks
        ]
        
        logger.info(f"Search found {len(results)} results for user {current_user.username} in {search_lang.value}")
        return results
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in search endpoint for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# ============================================
# Health Check
# ============================================

@router.get("/health", status_code=status.HTTP_200_OK)
async def rag_health():
    """Check RAG engine health"""
    return {
        "status": "healthy",
        "components": {
            "retriever": "ready",
            "generator": "ready",
            "embeddings": "ready",
            "vector_store": "ready"
        }
    }
