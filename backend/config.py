from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Advanced RAG AI Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days
    ALGORITHM: str = "HS256"
    
    # Admin Configuration
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin-password-change-this"
    AUTO_CREATE_ADMIN: bool = True  # Create admin user on startup if not exists
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Vector DB
    CHROMA_PERSIST_DIRECTORY: str = "storage/vector_db"
    
    # AI Models
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3"
    
    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    STORAGE_DOCUMENTS_PATH: str = "storage/uploads"
    CACHE_DIR: str = "storage/cache"
    MAX_FILE_SIZE_MB: int = 50  # 50 MB
    ALLOWED_EXTENSIONS: list = ["pdf", "docx", "txt", "jpg", "jpeg", "png"]
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:8501"
    FRONTEND_HTTPS: bool = False  # Set to True in production
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "storage/logs"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
    ]
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Security
    ENABLE_HTTPS: bool = False  # Set to True in production
    REQUIRE_HTTPS: bool = False  # Force HTTPS in production

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),  # Look in project root
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
