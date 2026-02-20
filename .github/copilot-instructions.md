# Advanced RAG System - AI Coding Agent Instructions

## System Overview

**Multi-modal Retrieval-Augmented Generation (RAG)** system with Telugu language support for intelligent document Q&A, quiz generation, and study planning.

**Core Data Flow**: PDF/DOCX/Image Upload → Text Extraction (OCR) → Intelligent Chunking (sentence-based default) → SentenceTransformer Embeddings (all-MiniLM-L6-v2) → ChromaDB Storage (user-isolated) → Semantic Retrieval (cosine similarity) → OpenAI LLM Response Generation with Context

### Component Status Summary

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **FastAPI Backend** | `backend/main.py` | REST API endpoints (auth, upload, query, quiz) | ✅ **Fully Implemented** |
| **Embeddings** | `backend/rag_engine/embeddings.py` | SentenceTransformer (all-MiniLM-L6-v2) batch/single encoding | ✅ **Production Ready** |
| **Vector Store** | `backend/rag_engine/vector_store.py` | ChromaDB CRUD with user-isolated metadata filtering | ✅ **Production Ready** |
| **Document Processing** | `backend/document_processor/` | PDF/DOCX extraction, multi-strategy chunking (sentence/word/char) | ✅ **Complete** |
| **Retriever** | `backend/rag_engine/retriever.py` | Semantic search + similarity threshold filtering | ✅ **Complete** |
| **Generator** | `backend/rag_engine/generator.py` | OpenAI GPT-3.5/4 response generation with context | ✅ **Complete** |
| **Frontend** | `frontend/app.py` | Streamlit multi-page app (Chat, Quiz, Upload, Analytics) | ✅ **Complete** |
| **Auth** | `backend/auth/` | JWT tokens (access/refresh), bcrypt hashing, session mgmt | ✅ **Complete** |
| **Utils** | `backend/utils/` | Quiz generation, language detection, study planning, translation | ✅ **Complete** |

## Critical Data Flows

### **1. Document Upload & Indexing Pipeline:**
```
POST /upload → TextExtractor.extract_text(file_path)
  [Auto-detects PDF/DOCX, uses OCR for images]
  → TextChunker.chunk_by_sentences(text, sentences_per_chunk=3) [DEFAULT strategy]
  → Create chunk objects: [{"id": "chunk_0", "text": "..."}, ...]
  → EmbeddingGenerator.generate_batch(chunks) → numpy array (N × 384)
  → Create metadata: [{"user_id": "user123", "source_file": "doc.pdf", "chunk_index": 0}, ...]
  → VectorStore.add_documents(chunks, embeddings, metadata)
  → ChromaDB indexes with cosine similarity
```

### **2. Query & RAG Response Pipeline:**
```
POST /query → EmbeddingGenerator.generate(query_text) → embedding vector
  → Retriever.retrieve(query, user_id="user123", n_results=5, similarity_threshold=0.3)
  → ChromaDB searches with WHERE filter: {"user_id": user_id}
  → Returns: [{"text": "chunk text", "source_file": "doc.pdf", "similarity": 0.87}, ...]
  → ResponseGenerator.generate_response(query, context_docs, language="english")
  → OpenAI ChatCompletion: system_prompt + context + query
  → Returns: {"response": "answer text", "sources": [...], "tokens_used": 150}
```

## Quick Start for Development

```powershell
# 1. Activate virtual environment
cd c:\Users\Sathwik\advanced-rag-system
& .\venv\Scripts\Activate.ps1

# 2. Install dependencies + NLP models
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm

# 3. Create .env file with:
#    OPENAI_API_KEY=sk-your-key-from-platform.openai.com

# 4. Start Backend (Terminal 1)
cd backend
python -m uvicorn main:app --reload  # http://localhost:8000

# 5. Start Frontend (Terminal 2)
cd frontend
streamlit run app.py  # http://localhost:8501
```
 Key Project Patterns & Conventions

### **1. User Isolation (SECURITY CRITICAL - Applied in ALL queries)**
Every vector store operation **MUST** filter by `user_id` in metadata to prevent cross-user data leakage:
```python
# ✅ CORRECT: Filters retrieve ONLY this user's documents
results = retriever.retrieve(query, user_id="user123", n_results=5)

# ❌ WRONG: No user isolation - security breach
results = retriever.retrieve(query, n_results=5)  

# Metadata ALWAYS includes user_id for filtering
metadatas = [
    {"source_file": "doc.pdf", "chunk_index": i, "user_id": user_id} 
    for i in range(len(chunks))
]

# In ChromaDB queries:
results = collection.query(
    query_embeddings=[embedding],
    where={"user_id": user_id},  # CRITICAL FILTER
    n_results=5
)
```
- ✅ **main.py**: `/upload` endpoint saves files, `/query` is stub
## Project-Specific Patterns & Conventions

### **2. Document Chunking Strategies**
All strategies support configurable overlap for semantic coherence. **Default: sentence-based** (recommended).
```python
from backend.document_processor.chunker import TextChunker

# ✅ RECOMMENDED: Preserves sentence boundaries, semantic meaning
chunks = TextChunker.chunk_by_sentences(text, sentences_per_chunk=3)

# Word-based: Uniform token distribution
chunks = TextChunker.chunk_by_words(text, chunk_size=500, overlap=50)

# Character-based: Fixed-size chunks
chunks = TextChunker.chunk_by_characters(text, chunk_size=2000, overlap=200)
```

### **3. Text Extraction - Auto-Format Detection**
Extractor detects file type and routes to appropriate processor (PDF/DOCX/image):
```python
from backend.document_processor.text_extractor import TextExtractor

extractor = TextExtractor()
text = extractor.extract_from_pdf("doc.pdf")  # or .docx, .txt
# Returns: str, empty string on error (no exceptions thrown)
```

### **4. Embeddings - Batch vs. Single**
Use batch for documents, single for queries. Both return numpy arrays (384-dim):
```python
from backend.rag_engine.embeddings import EmbeddingGenerator

gen = EmbeddingGenerator()  # Loads all-MiniLM-L6-v2 (~133MB)

# Single embedding
query_emb = gen.generate("What is RAG?")  # Returns: np.ndarray shape (384,)

# Batch embeddings (more efficient for 10+ texts)
chunk_embs = gen.generate_batch(chunks, batch_size=32)  # Returns: np.ndarray shape (N, 384)
```

### **5. Multi-Language Support - Detection & Translation**
Language auto-detection enables adaptive responses:
```python
from backend.utils.language_detector import LanguageDetector
from backend.utils.translator import Translator

detector = LanguageDetector()
language = detector.detect("నీకు ఎలా ఉంది?")  # Returns: "te" (Telugu)

translator = Translator()
result = translator.translate("Hello", source_lang="en", target_lang="te")
# Returns: "హలో"

# Generator auto-translates if language != "english"
response = response_generator.generate_response(
    query="Tell me about this",
    context_documents=[...],
    language="telugu"  # Translates final response to Telugu
)
```

### **6. Frontend → Backend Communication Pattern**
All requests include JWT Bearer token; backend validates with `get_current_user` dependency:
```python
# Frontend (Streamlit)
headers = {"Authorization": f"Bearer {st.session_state.token}"}
response = requests.post(
    f"{BACKEND_URL}/query",
    json={"question": "Summarize this", "language": "english"},
    headers=headers
)

# Backend (FastAPI)
@app.post("/query")
async def query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)  # Validates token
):
    user_id = current_user["user_id"]
    # All retrieval automatically filtered by user_id
```## API Endpoints Reference

| Method | Endpoint | Purpose | Auth | Input | Output |
|--------|----------|---------|------|-------|--------|
| POST | `/auth/register` | Create user account | ❌ | `{username, email, password, full_name}` | `{user_id}` |
| POST | `/auth/login` | Get JWT tokens | ❌ | `{username, password}` | `{access_token, refresh_token, expires_in}` |
| POST | `/auth/logout` | Invalidate token | ✅ | - | `{status}` |
| POST | `/upload` | Upload document | ✅ | File (PDF/DOCX/image) | `{document_id, filename, status}` |
| POST | `/query` | Ask question on docs | ✅ | `{question, language}` | `{response, sources, tokens_used}` |
| POST | `/quiz/generate` | Create quiz from docs | ✅ | `{num_questions, difficulty}` | `{questions[], language}` |
| GET | `/health` | System status | ❌ | - | `{status, vector_store stats}` |
| GET | `/analytics/summary` | User stats | ✅ | - | `{docs_uploaded, queries, quiz_attempts}` |

## Directory Structure & Storage

```
storage/
  documents/      # Raw uploaded files: {user_id}_{filename}
  vector_db/      # ChromaDB persistent directory (all embeddings + metadata)
  cache/          # Query result caching (future use)

backend/
  main.py                          # FastAPI app, all endpoints
  config.py                        # Settings class (loads .env)
  auth/authentication.py           # JWT + password hashing
  document_processor/
    text_extractor.py              # Auto-detects PDF/DOCX/image
    chunker.py                     # 3 chunking strategies
    pdf_processor.py               # PyPDF2/pdfplumber extraction
  rag_engine/
    embeddings.py                  # SentenceTransformer batch/single
    vector_store.py                # ChromaDB CRUD + user filtering
    retriever.py                   # Semantic search + threshold filtering
    generator.py                   # OpenAI + context injection
    relationship_mapper.py         # Document relationship extraction

frontend/
  app.py                          # Main Streamlit router
  pages/
    chat.py                        # Q&A interface
    upload.py                      # Document upload UI
    quiz.py                        # Quiz generation/review
    analytics.py                   # User statistics
  components/
    voice_input.py                 # Speech-to-text
    source_display.py              # Retrieved sources visualization
```

## Environment Configuration (.env)

```bash
# MANDATORY - Get from https://platform.openai.com/account/api-keys
OPENAI_API_KEY=sk-proj-xxxxx

# OPTIONAL - Defaults provided below
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage paths (relative to project root)
VECTOR_DB_PATH=../storage/vector_db
UPLOAD_DIR=../storage/documents
CACHE_DIR=../storage/cache

# RAG Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.5

# LLM Settings
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=500

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# File Upload
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=pdf,docx,txt,jpg,jpeg,png
```

## Common Development Workflows

### Adding a New API Endpoint
1. Define Pydantic request/response model in `models.py`
2. Create route in `backend/main.py` with `@app.post()` or `@app.get()`
3. Add `get_current_user` dependency for protected routes
4. Extract `user_id` and pass to backend services
5. Test via Swagger UI: `http://localhost:8000/docs`

### Debugging Vector Store Issues
```python
from backend.rag_engine.vector_store import VectorStore

vs = VectorStore()
# Check collection stats
stats = vs.get_collection_stats()  # {"document_count": N, "collection_name": "documents"}

# Retrieve all documents for a user
results = vs.collection.get(where={"user_id": "user123"})

# Clear all data (fresh start)
vs.collection.delete(where={})
# OR delete storage/vector_db/ directory entirely and restart backend
```

### Testing Retriever End-to-End
```python
from backend.rag_engine.embeddings import EmbeddingGenerator
from backend.rag_engine.retriever import Retriever
from backend.rag_engine.generator import ResponseGenerator

# 1. Embed and index sample documents
gen = EmbeddingGenerator()
embeddings = gen.generate_batch(["Sample doc 1", "Sample doc 2"])

# 2. Retrieve relevant documents
retriever = Retriever()
results = retriever.retrieve("What is RAG?", user_id="test_user", n_results=5)

# 3. Generate response
response_gen = ResponseGenerator()
response = response_gen.generate_response(
    "What is RAG?", 
    results,  # List of dict with 'text' and 'source_file'
    language="english"
)
```

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `OpenAI API errors` | Missing or invalid `OPENAI_API_KEY` | Verify key at https://platform.openai.com/account/api-keys; check `.env` file |
| `ChromaDB connection fails` | `storage/vector_db/` doesn't exist | First run creates it automatically; or `mkdir storage/vector_db` |
| `Retriever returns empty results` | No documents indexed or wrong user_id | Check: `vs.get_collection_stats()`; verify `user_id` parameter matches uploaded docs |
| `OSError: Can't find model 'en_core_web_sm'` | Spacy model not installed | Run: `python -m spacy download en_core_web_sm` |
| `401 Unauthorized on /query` | JWT token invalid/expired | Token refresh handled by frontend; may require re-login |
| `Document upload fails silently` | File type not supported or file too large | Check `ALLOWED_EXTENSIONS` and `MAX_FILE_SIZE_MB` in config; log at `backend/main.py` upload endpoint |

---

**Last Updated**: January 23, 2026  
**Status**: ✅ Production-ready - All core RAG components fully implemented  
**Language Support**: English + Telugu  
**Key Technologies**: FastAPI, Streamlit, ChromaDB, SentenceTransformer, OpenAI GPT-3.5/4
