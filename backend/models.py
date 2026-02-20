from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- User Models ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: int  # Seconds until expiration
    refresh_expires_in: Optional[int] = None  # Seconds until refresh token expires


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    username: Optional[str] = None
    type: Optional[str] = "access"  # access or refresh

# --- Document Models ---
class DocumentMetadata(BaseModel):
    id: str
    user_id: int
    filename: str
    file_path: str
    file_type: str
    file_size: Optional[int] = None
    status: str = "processing"  # processing, completed, failed
    text_content_summary: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime = datetime.now()
    
    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Response model for document listing and retrieval."""
    id: str
    filename: str
    file_type: str
    file_size: Optional[int] = None
    status: str
    text_content_summary: Optional[str] = None
    chunk_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChunkMetadata(BaseModel):
    document_id: str
    user_id: int
    chunk_index: int
    page_number: Optional[int] = None
    chunk_type: str = "text"  # text, table, image_ocr
    content_summary: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# --- Citation Models for Explainable AI ---
class CitationInfo(BaseModel):
    """Citation information with confidence scores"""
    document: str  # Document name/filename
    chunk_index: int  # Chunk index in document
    page: Optional[int] = None  # Page number if available
    confidence: float  # Overall confidence (0-1)
    similarity: float  # Vector similarity score (0-1)
    excerpt: str  # Text excerpt from chunk
    chunk_id: Optional[str] = None  # Unique chunk ID


class ExplainableQueryResponse(BaseModel):
    """Response model with full explainability"""
    answer: str  # Generated answer
    citations: List[CitationInfo]  # List of citations with metadata
    answer_confidence: float  # Overall confidence in answer (0-1)
    language: str  # Response language
    model_used: str  # Model name
    tokens_used: dict  # Token usage stats
    context_count: int  # Number of context documents used


class ExplainableChatResponse(BaseModel):
    """Chat response with explainability"""
    message: str  # Generated message
    citations: List[CitationInfo]  # Source citations
    message_confidence: float  # Confidence in message (0-1)
    session_id: str  # Session ID
    language: str  # Message language

# --- Quiz Models ---
class QuizGenerateRequest(BaseModel):
    """Request model for quiz generation"""
    num_questions: int  # Number of questions (1-50)
    difficulty: str = "medium"  # easy, medium, hard
    language: str = "english"  # english, telugu
    topic: Optional[str] = None  # Optional topic filter
    question_types: Optional[List[str]] = None  # Types: multiple_choice, short_answer, true_false


class QuestionData(BaseModel):
    """Single question in a quiz"""
    id: str
    question_number: int
    question_type: str  # multiple_choice, short_answer, true_false
    question_text: str
    difficulty: str
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: Optional[str] = None  # Correct answer (hidden during quiz)
    expected_answer: Optional[str] = None  # For short answer questions
    explanation: Optional[str] = None
    source_document: Optional[str] = None
    topic: Optional[str] = None


class QuizSessionResponse(BaseModel):
    """Response model for quiz session"""
    session_id: str
    num_questions: int
    difficulty: str
    language: str
    topic: Optional[str] = None
    status: str  # in_progress, completed, abandoned
    questions: List[QuestionData]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class QuizDisplayQuestion(BaseModel):
    """Question displayed to user (hides correct answer)"""
    id: str
    question_number: int
    question_type: str
    question_text: str
    difficulty: str
    options: Optional[List[str]] = None


class QuizSessionStartResponse(BaseModel):
    """Response when quiz session starts"""
    session_id: str
    num_questions: int
    difficulty: str
    language: str
    first_question: QuizDisplayQuestion
    created_at: datetime


class SubmitAnswerRequest(BaseModel):
    """Request model for submitting quiz answer"""
    session_id: str
    question_id: str
    user_answer: str
    time_taken_seconds: Optional[int] = None


class SubmitAnswerResponse(BaseModel):
    """Response after submitting answer"""
    is_correct: Optional[bool]  # True/False/None if manual grading needed
    explanation: str
    feedback: Optional[str] = None
    next_question: Optional[QuizDisplayQuestion] = None
    session_status: str  # in_progress, completed


class QuizResultsResponse(BaseModel):
    """Final quiz results"""
    session_id: str
    num_questions: int
    correct_count: int
    attempted_count: int
    score: float  # Percentage (0-100)
    difficulty: str
    language: str
    duration_seconds: Optional[int] = None
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class QuizHistoryItem(BaseModel):
    """Single quiz in user's history"""
    session_id: str
    num_questions: int
    correct_count: int
    attempted_count: int
    score: float
    difficulty: str
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class QuizHistoryResponse(BaseModel):
    """User's quiz history"""
    total_quizzes: int
    total_questions_attempted: int
    average_score: float
    quizzes: List[QuizHistoryItem]


# --- Admin Models ---
class UserOutAdmin(BaseModel):
    """User model for admin view (includes sensitive fields)"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    documents_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class AdminUserStatsResponse(BaseModel):
    """Statistics for a user (admin view)"""
    user_id: int
    username: str
    email: str
    total_documents: int
    total_chunks: int
    total_queries: int
    total_quizzes_taken: int
    storage_used_bytes: int
    joined_date: datetime
    last_activity: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Response for listing users"""
    total_users: int
    active_users: int
    admin_users: int
    users: List[UserOutAdmin]


class StorageStatsResponse(BaseModel):
    """Storage and system statistics"""
    total_documents: int
    total_chunks: int
    total_storage_bytes: int
    average_document_size: int
    vector_db_size_bytes: int
    database_size_bytes: int
    system_uptime_seconds: int


class AdminActionRequest(BaseModel):
    """Request for admin actions"""
    user_id: int
    action: str  # disable, delete, reset_password
    reason: Optional[str] = None


class AdminActionResponse(BaseModel):
    """Response for admin actions"""
    success: bool
    message: str
    action: str
    affected_user: str
    timestamp: datetime


class AuditLogItem(BaseModel):
    """Single audit log entry"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: str
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    details: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Response for audit logs"""
    total_logs: int
    logs: List[AuditLogItem]


class SystemHealthResponse(BaseModel):
    """System health check response"""
    status: str  # healthy, degraded, down
    timestamp: datetime
    version: str
    environment: str
    database_status: str
    vector_store_status: str
    uptime_seconds: int
    active_sessions: int
    message: Optional[str] = None
