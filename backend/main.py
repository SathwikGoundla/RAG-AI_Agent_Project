"""
FastAPI backend for Advanced RAG System with multi-user support.
Implements secure authentication, RAG pipeline, document management, and session handling.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.database import (
    init_db, 
    User, Document, DocumentChunk, RefreshToken, 
    AuditLog, QuizSession, QuizQuestion, UserQuizAnswer
)

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# NOTE: init_db() is called in app startup event below, NOT here

# ============================================
# FastAPI Application Setup
# ============================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade API for Multi-User Multi-Modal RAG AI Platform with Secure Authentication",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Support",
        "url": "https://github.com/sathwik/advanced-rag-system",
    }
)

# ============================================
# Startup Event - Initialize Database
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on app startup after all models are imported"""
    init_db()

# ============================================
# Middleware Configuration
# ============================================

# CORS Configuration - Allow frontend, Streamlit, and development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(settings.FRONTEND_URL),
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directories
import os
for directory in [settings.UPLOAD_DIR, settings.CACHE_DIR, settings.LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Add security and logging middleware
from backend.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Track and log request processing time"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(f"Request: {request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions gracefully"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."},
    )

# ============================================
# Health Check Endpoint
# ============================================

@app.get("/", tags=["Health"])
async def health_check():
    """API health check endpoint"""
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": time.time(),
        "environment": "production" if not settings.DEBUG else "development"
    }

# ============================================
# Authentication Routers
# ============================================

from backend.auth import signup, login, session_manager, admin, google_oauth, debug_oauth
from backend.document_processor.router import router as doc_router
from backend.rag_engine.router import router as rag_router
from backend.rag_engine import relationships_router
from backend.rag_engine import quiz_router

# Authentication endpoints
app.include_router(
    signup.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

app.include_router(
    login.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

app.include_router(
    google_oauth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication - OAuth"]
)

# Debug endpoints for auth (safe, does not expose secrets)
app.include_router(
    debug_oauth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication - Debug"]
)

# Admin endpoints
app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"]
)

# Session management endpoints
app.include_router(
    session_manager.router,
    prefix=f"{settings.API_V1_STR}/sessions",
    tags=["Sessions"]
)

# Document management endpoints
app.include_router(
    doc_router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["Documents"]
)

# RAG Pipeline endpoints (Query, Chat, Search)
app.include_router(
    rag_router,
    prefix=f"{settings.API_V1_STR}/rag",
    tags=["RAG Pipeline"]
)

# Document Relationships endpoints (Relationship analysis, insights, visualization)
app.include_router(
    relationships_router.router,
    prefix=f"{settings.API_V1_STR}/relationships",
    tags=["Relationships"]
)

# Quiz endpoints (Quiz generation, session management, results)
app.include_router(
    quiz_router.router,
    prefix=f"{settings.API_V1_STR}/quiz",
    tags=["Quiz"]
)

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {settings.PROJECT_NAME} on {settings.HOST}:{settings.PORT}")
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
