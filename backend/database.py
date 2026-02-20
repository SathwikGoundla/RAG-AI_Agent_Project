from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from backend.config import settings

# Create SQLite engine with improved settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 10},
    pool_pre_ping=True
)

# Disable WAL mode for development to avoid locking issues
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Disable WAL mode and set other SQLite pragmas"""
    if hasattr(dbapi_connection, 'execute'):
        dbapi_connection.execute("PRAGMA journal_mode=DELETE")
        dbapi_connection.execute("PRAGMA synchronous=NORMAL")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # "user" or "admin"
    is_verified = Column(Boolean, default=False)  # Email verification status
    
    # OAuth Integration
    oauth_provider = Column(String, nullable=True)  # "google", "github", etc.
    oauth_id = Column(String, nullable=True)  # Provider-specific user ID
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    quiz_sessions = relationship("QuizSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Represents an uploaded document with metadata for per-user isolation."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to stored file
    file_type = Column(String, nullable=False)  # pdf, docx, txt, jpg, png
    file_size = Column(Integer, nullable=True)  # Size in bytes
    status = Column(String, default="processing")  # processing, completed, failed
    text_content_summary = Column(Text, nullable=True)  # First 500 chars of extracted text
    chunk_count = Column(Integer, default=0)  # Number of chunks created
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Represents chunks of a document stored in vector database."""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Denormalized for faster queries
    chunk_index = Column(Integer, nullable=False)  # Order within document
    page_number = Column(Integer, nullable=True)  # For PDFs
    chunk_type = Column(String, default="text")  # text, table, image_ocr
    content_summary = Column(Text, nullable=True)  # First 200 chars
    embedding_id = Column(String, nullable=True)  # ID in ChromaDB
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class RefreshToken(Base):
    """Stores refresh tokens for users to maintain long-lived sessions."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)  # Hashed token
    is_revoked = Column(Boolean, default=False)  # For token revocation
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # Expiry time
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    """Audit trail for tracking user actions and system events."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for system events
    action = Column(String, nullable=False, index=True)  # login, logout, upload, delete, etc.
    resource_type = Column(String, nullable=True)  # document, user, settings, etc.
    resource_id = Column(String, nullable=True)  # ID of affected resource
    status = Column(String, nullable=False)  # success, failure
    status_code = Column(Integer, nullable=True)  # HTTP status code
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # Additional details
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class QuizSession(Base):
    """Represents a quiz session for a user."""
    __tablename__ = "quiz_sessions"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    num_questions = Column(Integer, nullable=False)  # Total number of questions
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    language = Column(String, default="english")  # english, telugu
    topic = Column(String, nullable=True)  # Optional topic filter
    status = Column(String, default="in_progress")  # in_progress, completed, abandoned
    score = Column(Float, nullable=True)  # Final score percentage
    correct_count = Column(Integer, default=0)  # Number of correct answers
    attempted_count = Column(Integer, default=0)  # Number of attempted questions
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Quiz duration in seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="quiz_sessions")
    questions = relationship("QuizQuestion", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("UserQuizAnswer", back_populates="session", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """Represents a single question in a quiz session."""
    __tablename__ = "quiz_questions"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    quiz_session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False, index=True)
    question_number = Column(Integer, nullable=False)  # Order in quiz (1-based)
    question_type = Column(String, nullable=False)  # multiple_choice, short_answer, true_false
    question_text = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False)  # easy, medium, hard
    topic = Column(String, nullable=True)  # Topic this question covers
    
    # Multiple choice specific
    options = Column(Text, nullable=True)  # JSON array of options
    correct_answer = Column(String, nullable=True)  # Correct answer (for MCQ/T/F)
    
    # Short answer specific
    expected_answer = Column(Text, nullable=True)  # Expected answer for short questions
    answer_keywords = Column(Text, nullable=True)  # JSON array of keywords to check
    
    explanation = Column(Text, nullable=True)  # Explanation after answering
    source_document = Column(String, nullable=True)  # Source document filename
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("QuizSession", back_populates="questions")
    answers = relationship("UserQuizAnswer", back_populates="question", cascade="all, delete-orphan")


class UserQuizAnswer(Base):
    """Represents a user's answer to a quiz question."""
    __tablename__ = "user_quiz_answers"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    quiz_session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False, index=True)
    question_id = Column(String, ForeignKey("quiz_questions.id"), nullable=False, index=True)
    user_answer = Column(Text, nullable=True)  # User's submitted answer
    is_correct = Column(Boolean, nullable=True)  # True/False/None (not graded yet)
    time_taken_seconds = Column(Integer, nullable=True)  # Time spent on this question
    feedback = Column(Text, nullable=True)  # AI-generated feedback for wrong answers
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence rating from LLM
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("QuizSession", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")

# Create tables
def init_db():
    """Initialize database tables and create default admin user if configured"""
    print("[INFO] Initializing database...")
    
    # Create all tables from the declarative models
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created successfully")
    except Exception as e:
        print(f"[ERROR] Failed to create database tables: {e}")
        return
    
    # Ensure oauth columns exist (SQLAlchemy sometimes doesn't include them on first create)
    try:
        from sqlalchemy import text
        db = SessionLocal()
        
        # Check if oauth columns exist
        cursor = engine.raw_connection().cursor()
        cursor.execute("PRAGMA table_info(users);")
        existing_cols = {row[1] for row in cursor.fetchall()}
        cursor.close()
        
        # Add oauth columns if missing
        if 'oauth_provider' not in existing_cols:
            print("[INFO] Adding missing oauth_provider column...")
            db.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR"))
            db.commit()
        
        if 'oauth_id' not in existing_cols:
            print("[INFO] Adding missing oauth_id column...")
            db.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR"))
            db.commit()
        
        db.close()
    except Exception as e:
        print(f"[WARNING] Could not verify oauth columns: {e}")
        # Don't fail init_db for this, continue anyway
    
    # Create default admin user if enabled
    if getattr(settings, 'AUTO_CREATE_ADMIN', True):
        try:
            db = SessionLocal()
            admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
            
            if not admin_user:
                from backend.auth.security import get_password_hash
                
                admin_user = User(
                    username=settings.ADMIN_USERNAME,
                    email=settings.ADMIN_EMAIL,
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    full_name="System Administrator",
                    is_active=True,
                    is_verified=True,
                    role="admin",
                    oauth_provider=None,
                    oauth_id=None,
                    created_at=datetime.utcnow()
                )
                db.add(admin_user)
                db.commit()
                print(f"[OK] Admin user '{settings.ADMIN_USERNAME}' created successfully")
                print(f"     WARNING: Change the password immediately in production!")
            else:
                print(f"[OK] Admin user '{settings.ADMIN_USERNAME}' already exists")
            
            db.close()
        except Exception as e:
            print(f"[ERROR] Failed to create admin user: {e}")
            import traceback
            traceback.print_exc()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
