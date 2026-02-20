# 📊 Advanced RAG System - Use Case Diagrams & Scenarios

---

## 1️⃣ SYSTEM ACTORS

```
┌──────────────────────────────────────┐
│         SYSTEM ACTORS                │
├──────────────────────────────────────┤
│                                      │
│  👤 Regular User                    │
│     - Authenticate                  │
│     - Upload documents              │
│     - Ask questions                 │
│     - Take quizzes                  │
│     - View analytics                │
│                                      │
│  👨‍💼 Administrator                  │
│     - Manage users                  │
│     - Monitor system health         │
│     - View audit logs               │
│     - Manage resources              │
│                                      │
│  🤖 AI System                       │
│     - Process documents             │
│     - Generate embeddings           │
│     - Retrieve context              │
│     - Generate responses            │
│                                      │
│  🔌 External Services               │
│     - OpenAI LLM                    │
│     - Google OAuth                  │
│     - Storage service               │
│                                      │
└──────────────────────────────────────┘
```

---

## 2️⃣ PRIMARY USE CASES FOR REGULAR USERS

### **Use Case 1: User Registration & Authentication**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Use Case: Register New Account                    │
│                                                     │
│  Actors: New User, System                          │
│                                                     │
│  Preconditions:                                    │
│    - User has valid email                         │
│    - User has not registered before              │
│                                                     │
│  Main Flow:                                        │
│  1. User opens sign-up page                       │
│  2. Enters username, email, password              │
│  3. System validates input                        │
│  4. System hashes password with Bcrypt           │
│  5. User created in database                      │
│  6. Welcome email sent                            │
│  7. User redirected to login                      │
│                                                     │
│  Postconditions:                                   │
│    ✅ User account created                        │
│    ✅ Ready to login                              │
│    ✅ User isolated collection created            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### **Use Case 2: User Login & Authentication**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Use Case: Login & Get JWT Tokens                 │
│                                                     │
│  Actors: User, Authentication System              │
│                                                     │
│  Preconditions:                                    │
│    - User has valid account                       │
│    - User remembers credentials                   │
│                                                     │
│  Main Flow:                                        │
│  1. User opens login page                         │
│  2. Enters username and password                  │
│  3. System validates credentials                  │
│  4. Password verified with Bcrypt                 │
│  5. JWT access token generated (7 days)         │
│  6. Refresh token generated                       │
│  7. Tokens stored in client session              │
│  8. User redirected to dashboard                  │
│                                                     │
│  Postconditions:                                   │
│    ✅ User authenticated                          │
│    ✅ Session established                         │
│    ✅ Access to protected resources              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### **Use Case 3: Upload & Process Documents**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Use Case: Upload Document for Analysis          │
│                                                     │
│  Actors: User, Document Processor, Vector Store   │
│                                                     │
│  Preconditions:                                    │
│    - User authenticated                           │
│    - Document is valid (PDF, DOCX, Image)        │
│    - File size < 10 MB                           │
│                                                     │
│  Main Flow:                                        │
│  1. User selects document file                    │
│  2. System validates file type and size          │
│  3. File uploaded to storage/user_{id}/          │
│  4. Text extracted:                              │
│     - PDF  → PyPDF2/Pdfplumber                   │
│     - DOCX → python-docx                         │
│     - IMG  → Tesseract OCR                       │
│  5. Text split into chunks (sentence-based)      │
│  6. Embeddings generated (SentenceTransformer)   │
│  7. Vectors stored in ChromaDB (user-isolated)   │
│  8. Document metadata saved to database          │
│  9. Success notification displayed               │
│                                                     │
│  Postconditions:                                   │
│    ✅ Document indexed                            │
│    ✅ Ready for queries                           │
│    ✅ Searchable in RAG                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### **Use Case 4: Ask Questions (RAG Query)**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: Query Documents with RAG                │
│                                                      │
│  Actors: User, Retriever, LLM, Vector Store        │
│                                                      │
│  Preconditions:                                     │
│    - User authenticated                            │
│    - Documents uploaded                            │
│    - RAG system initialized                        │
│                                                     │
│  Main Flow:                                         │
│  1. User types question in chat interface          │
│  2. Question embedded to 384-dim vector            │
│  3. Semantic search in ChromaDB:                   │
│     - User filter applied                         │
│     - Cosine similarity computed                  │
│     - Top 5 relevant chunks retrieved             │
│  4. Context window assembled:                      │
│     - System prompt + Instructions                │
│     - Retrieved document chunks                   │
│     - Chat history (up to 4000 tokens)            │
│  5. OpenAI GPT-3.5/4 generates answer            │
│  6. Response + source citations returned          │
│  7. Message saved to session history              │
│  8. UI displays response + sources                │
│                                                      │
│  Alternate Flow (No relevant documents):           │
│  → LLM acknowledges limitation                    │
│  → Suggests related topics                        │
│  → Offers to upload relevant documents            │
│                                                      │
│  Postconditions:                                    │
│    ✅ User received answer                         │
│    ✅ Sources cited                                │
│    ✅ History saved                                │
│    ✅ Tokens counted                               │
│                                                     │
└──────────────────────────────────────────────────────┘
```

### **Use Case 5: Generate & Take Quizzes**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: Generate Quiz from Documents           │
│                                                      │
│  Actors: User, Quiz Generator, LLM                 │
│                                                      │
│  Preconditions:                                     │
│    - User authenticated                            │
│    - Documents uploaded                            │
│                                                     │
│  Main Flow:                                         │
│  1. User selects "Generate Quiz"                   │
│  2. Chooses parameters:                            │
│     - Number of questions (5-50)                  │
│     - Difficulty (Easy/Medium/Hard)               │
│     - Question type (MCQ/T-F/ShortAnswer)         │
│  3. System retrieves document chunks              │
│  4. LLM generates questions based on content      │
│  5. Questions validated and formatted             │
│  6. Quiz presented to user                        │
│  7. User answers all questions                    │
│  8. System evaluates answers                      │
│  9. Score calculated and saved                    │
│  10. Results & explanations displayed             │
│                                                      │
│  Postconditions:                                    │
│    ✅ Quiz completed                               │
│    ✅ Score recorded                               │
│    ✅ Learning insights provided                   │
│                                                     │
└──────────────────────────────────────────────────────┘
```

### **Use Case 6: View Analytics & Usage**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: View Personal Analytics                │
│                                                      │
│  Actors: User, Analytics Engine                    │
│                                                      │
│  Preconditions:                                     │
│    - User authenticated                            │
│    - User has activity history                     │
│                                                     │
│  Main Flow:                                         │
│  1. User opens Analytics page                      │
│  2. System retrieves user's metrics:              │
│     - Documents uploaded                          │
│     - Queries made                                │
│     - Quiz attempts                               │
│     - Study time                                  │
│     - Storage used                                │
│  3. Visualizations generated:                      │
│     - Charts (line, bar, pie)                     │
│     - Trends over time                            │
│     - Performance metrics                         │
│  4. Detailed statistics displayed                  │
│  5. Export option provided                         │
│                                                      │
│  Postconditions:                                    │
│    ✅ Analytics displayed                          │
│    ✅ Insights visible                             │
│                                                     │
└──────────────────────────────────────────────────────┘
```

---

## 3️⃣ ADMINISTRATOR USE CASES

### **Use Case 7: Admin User Management**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: Manage Users (Admin)                    │
│                                                      │
│  Actors: Administrator                             │
│                                                      │
│  Preconditions:                                     │
│    - Admin authenticated                           │
│    - Admin role verified                           │
│                                                     │
│  Main Flow:                                         │
│  1. Admin opens Admin Dashboard                    │
│  2. Selects "User Management"                      │
│  3. Views list of all users                        │
│  4. Can perform actions:                           │
│     - View user profile                           │
│     - View user documents                         │
│     - View user activity logs                     │
│     - Reset user password                         │
│     - Disable user account                        │
│     - Delete user (cascade delete)                │
│     - View storage usage                          │
│  5. Changes logged to audit trail                 │
│  6. Confirmation required for destructive ops    │
│                                                      │
│  Postconditions:                                    │
│    ✅ User modified as requested                   │
│    ✅ Audit trail updated                          │
│                                                     │
└──────────────────────────────────────────────────────┘
```

### **Use Case 8: System Monitoring**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: Monitor System Health                   │
│                                                      │
│  Actors: Administrator                             │
│                                                      │
│  Preconditions:                                     │
│    - Admin authenticated                           │
│                                                     │
│  Main Flow:                                         │
│  1. Admin opens Monitoring Dashboard               │
│  2. Views real-time metrics:                       │
│     - System health status                        │
│     - API response times                          │
│     - Database connections                       │
│     - Vector DB status                           │
│     - Storage usage                              │
│     - Active sessions                            │
│  3. Views error logs and alerts                   │
│  4. Checks backup status                          │
│  5. Reviews audit logs                            │
│  6. Alerts configured for thresholds              │
│                                                      │
│  Postconditions:                                    │
│    ✅ System status visible                        │
│    ✅ Issues identified early                      │
│                                                     │
└──────────────────────────────────────────────────────┘
```

### **Use Case 9: View Audit Logs**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Use Case: Access Audit Trail                     │
│                                                      │
│  Actors: Administrator                             │
│                                                      │
│  Preconditions:                                     │
│    - Admin authenticated                           │
│    - Audit logs exist                              │
│                                                     │
│  Main Flow:                                         │
│  1. Admin opens Audit Logs section                 │
│  2. Views filtered logs by:                        │
│     - User                                         │
│     - Action type                                 │
│     - Date range                                  │
│     - Status                                      │
│  3. Each log shows:                                │
│     - User ID                                     │
│     - Action performed                            │
│     - Timestamp                                   │
│     - IP address                                  │
│     - Result (success/failure)                    │
│  4. Search and filter capabilities                │
│  5. Export logs as CSV/JSON                       │
│                                                      │
│  Postconditions:                                    │
│    ✅ Audit trail reviewed                         │
│    ✅ Compliance verified                          │
│                                                     │
└──────────────────────────────────────────────────────┘
```

---

## 4️⃣ SYSTEM-LEVEL USE CASES

### **Use Case 10: Document Processing Pipeline**

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  Use Case: End-to-End Document Processing       │
│                                                  │
│  ┌────────────────────────────────────────┐    │
│  │ 1. FILE UPLOAD                         │    │
│  │    - Validate type (PDF/DOCX/IMG)      │    │
│  │    - Check size limit (10 MB)          │    │
│  │    - Store in user directory           │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ┌────────────────────────────────────────┐    │
│  │ 2. TEXT EXTRACTION                     │    │
│  │    - PDF → PyPDF2/pdfplumber           │    │
│  │    - DOCX → python-docx                │    │
│  │    - IMG → Tesseract OCR               │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ┌────────────────────────────────────────┐    │
│  │ 3. TEXT CHUNKING                       │    │
│  │    - Sentence-based (default)          │    │
│  │    - Word-based (alternative)          │    │
│  │    - Character-based (fallback)        │    │
│  │    - Overlap: 50 tokens                │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ┌────────────────────────────────────────┐    │
│  │ 4. EMBEDDING GENERATION                │    │
│  │    - SentenceTransformer model         │    │
│  │    - Batch processing (32 items)       │    │
│  │    - 384-dimensional vectors           │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ┌────────────────────────────────────────┐    │
│  │ 5. VECTOR STORAGE                      │    │
│  │    - ChromaDB indexed                  │    │
│  │    - User metadata added               │    │
│  │    - Cosine similarity enabled         │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ┌────────────────────────────────────────┐    │
│  │ 6. METADATA STORAGE                    │    │
│  │    - Document info saved               │    │
│  │    - Chunk mapping stored              │    │
│  │    - Indexed for fast retrieval        │    │
│  └────────────────────────────────────────┘    │
│           ↓                                     │
│  ✅ READY FOR QUERIES                         │
│                                                  │
└──────────────────────────────────────────────────┘
```

### **Use Case 11: RAG Query Resolution**

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  Use Case: RAG Query Processing                  │
│                                                    │
│  ┌──────────────────────────────────────────┐   │
│  │ 1. QUERY INPUT                           │   │
│  │    - User question received               │   │
│  │    - Language detected                   │   │
│  │    - Translated if needed                │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 2. QUERY EMBEDDING                       │   │
│  │    - Convert to 384-dim vector            │   │
│  │    - SentenceTransformer model            │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 3. SEMANTIC RETRIEVAL                    │   │
│  │    - User filter applied                 │   │
│  │    - Cosine similarity computed          │   │
│  │    - Top 5 results retrieved             │   │
│  │    - Threshold filter (0.3)              │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 4. CONTEXT ASSEMBLY                      │   │
│  │    - System prompt                       │   │
│  │    - Retrieved chunks (documents)        │   │
│  │    - Chat history (last N messages)      │   │
│  │    - Token budget management             │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 5. LLM RESPONSE GENERATION                │   │
│  │    - OpenAI GPT-3.5 or GPT-4            │   │
│  │    - Context injection                   │   │
│  │    - Temperature: 0.3 (consistent)       │   │
│  │    - Max tokens: 500                     │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 6. RESPONSE PROCESSING                   │   │
│  │    - Extract citations                   │   │
│  │    - Count tokens used                   │   │
│  │    - Format for display                  │   │
│  │    - Save to session history             │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ┌──────────────────────────────────────────┐   │
│  │ 7. RESPONSE DELIVERY                     │   │
│  │    - Return answer                       │   │
│  │    - Include source documents            │   │
│  │    - Show relevance scores               │   │
│  │    - Translate if needed                 │   │
│  └──────────────────────────────────────────┘   │
│           ↓                                      │
│  ✅ USER RECEIVES ANSWER WITH SOURCES          │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## 5️⃣ INTERACTION DIAGRAMS

### **User Authentication Flow**

```
User                Frontend           Backend             Database
  │                   │                   │                   │
  ├─► Click "Sign Up" ─────────────────► │                   │
  │                   │                   │                   │
  │                   │ Enter credentials │                   │
  │◄─ Show form ──────│                   │                   │
  │                   │                   │                   │
  ├─► Submit form ────────────────────► │                   │
  │                   │                   │                   │
  │                   │ Validate input    │                   │
  │                   │ Hash password     │                   │
  │                   │ Create user ──────────────────────► │
  │                   │                   │                   │
  │◄─ "Account Created" ────────────────│◄──────────────────│
  │                   │                   │                   │
```

### **Document Upload & Processing Flow**

```
User             Frontend            Backend            Storage/Vector DB
  │                 │                   │                   │
  ├─► Select file ──┤                   │                   │
  │                 │                   │                   │
  ├─► Upload ───────────────────────► │                   │
  │                 │                   │                   │
  │                 │ Store file ───────────────────────► │
  │                 │                   │                   │
  │                 │ Extract text      │                   │
  │                 │ (PDF/DOCX/OCR)    │                   │
  │                 │                   │                   │
  │                 │ Chunk text        │                   │
  │                 │                   │                   │
  │                 │ Generate embeddings │                 │
  │                 │                   │                   │
  │                 │ Store in ChromaDB ────────────────► │
  │                 │                   │                   │
  │◄─ "Upload successful" ──────────────────────────────│
  │                 │                   │                   │
```

### **RAG Query Processing Flow**

```
User             Frontend            Backend            External API
  │                 │                   │                   │
  ├─► Ask question ──────────────────► │                   │
  │                 │                   │                   │
  │                 │ Embed query       │                   │
  │                 │ Retrieve docs     │                   │
  │                 │ Build context     │                   │
  │                 │                   │                   │
  │                 │ Send to LLM ─────────────────────► │
  │                 │                   │                   │
  │                 │◄─ Receive response ──────────────────│
  │                 │                   │                   │
  │                 │ Process response  │                   │
  │                 │ Format output     │                   │
  │                 │                   │                   │
  │◄─ Display answer + sources ────────────────────────────│
  │                 │                   │                   │
```

---

## 6️⃣ DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM DATA FLOW                         │
└─────────────────────────────────────────────────────────────┘

                          [Users]
                            ↓
                   ┌────────────────┐
                   │ Authentication │
                   │   (JWT/OAuth)  │
                   └────────────────┘
                            ↓
              ┌─────────────────────────────┐
              │                             │
              ↓                             ↓
        [Upload Documents]         [Query/Chat]
              ↓                             ↓
    ┌──────────────────┐         ┌─────────────────┐
    │ Text Extraction  │         │ Query Embedding │
    │ (PDF/DOCX/OCR)   │         │ (384-dim)       │
    └──────────────────┘         └─────────────────┘
              ↓                             ↓
    ┌──────────────────┐         ┌─────────────────┐
    │ Text Chunking    │         │ Semantic Search │
    │ (Sentences)      │         │ (ChromaDB)      │
    └──────────────────┘         └─────────────────┘
              ↓                             ↓
    ┌──────────────────┐         ┌─────────────────┐
    │ Embedding Gen    │         │ Context Builder │
    │ (SentenceXFormer)│         │ (Retrieved docs │
    └──────────────────┘         │  + History)     │
              ↓                   └─────────────────┘
    ┌──────────────────┐                 ↓
    │ Vector Storage   │         ┌─────────────────┐
    │ (ChromaDB+Meta)  │         │ OpenAI LLM      │
    └──────────────────┘         │ (GPT-3.5/4)     │
              ↓                   └─────────────────┘
    ┌──────────────────┐                 ↓
    │ User-Isolated    │         ┌─────────────────┐
    │ Collections      │         │ Response        │
    └──────────────────┘         │ Formatter       │
                                 └─────────────────┘
                                        ↓
                                   [User Response]
```

---

## 7️⃣ SYSTEM CONTEXT DIAGRAM

```
┌──────────────────────────────────────────────────────────────┐
│                      EXTERNAL WORLD                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  OpenAI API  │  │ Google OAuth │  │ Storage Service  │ │
│  │  (GPT-3.5/4) │  │   (Auth)     │  │ (Files/Embeddings│ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
│         ▲                  ▲                   ▲            │
│         │                  │                   │            │
└─────────┼──────────────────┼───────────────────┼────────────┘
          │                  │                   │
          │                  │                   │
    ┌─────▼──────────────────▼───────────────────▼────┐
    │                                                  │
    │         ADVANCED RAG SYSTEM                      │
    │                                                  │
    │  ┌────────────────────────────────────────┐    │
    │  │  FastAPI Backend                       │    │
    │  │  - 35+ REST API Endpoints              │    │
    │  │  - Auth System                         │    │
    │  │  - RAG Pipeline                        │    │
    │  │  - Admin Dashboard                     │    │
    │  └────────────────────────────────────────┘    │
    │              ↑              ↑                    │
    │              │              │                    │
    │  ┌───────────┴──┐  ┌────────┴──────────────┐   │
    │  │ SQLite DB    │  │ ChromaDB Vector Store │   │
    │  │ - Users      │  │ - User collections    │   │
    │  │ - Documents  │  │ - Embeddings          │   │
    │  │ - Sessions   │  │ - Metadata            │   │
    │  │ - Audit Logs │  └───────────────────────┘   │
    │  └──────────────┘                              │
    │                                                  │
    └──────────────────────────────────────────────────┘
              ▲                          ▲
              │                          │
    ┌─────────┴──────┐          ┌────────┴──────────┐
    │ Streamlit UI   │          │ Admin Dashboard   │
    │ - Chat Page    │          │ - User Mgmt       │
    │ - Upload Page  │          │ - Monitoring      │
    │ - Quiz Page    │          │ - Audit Logs      │
    │ - Analytics    │          └───────────────────┘
    └────────────────┘
          ▲
          │
    [Regular Users]
```

---

## 8️⃣ STATE DIAGRAMS

### **User Account State Diagram**

```
┌─────────────┐
│   Created   │◄─── Register with email
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │◄─── Login successful
└──────┬──────┘
       │
       ├─► Disable ──────────┐
       │                      ▼
       │                 ┌──────────────┐
       │                 │   Disabled   │
       │                 └──────────────┘
       │
       ├─► Delete ───────────┐
       │                     ▼
       │                ┌──────────────┐
       │                │   Deleted    │
       │                └──────────────┘
       │
       └─► Change Password
                │
                └─► Active (unchanged)
```

### **Document Processing State Diagram**

```
┌──────────────┐
│   Created    │◄── User uploads file
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Extracting  │◄── Text extraction started
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Chunking    │◄── Text split into chunks
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Embedding   │◄── Generating embeddings
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Indexed    │◄── Stored in ChromaDB
└──────┬───────┘
       │
       ├─► Delete ────── [Deleted State]
       │
       └─► Ready for queries
```

---

## 🎯 SUMMARY

This Advanced RAG System covers **9+ primary use cases** with **multiple actors**, **data flows**, and **enterprise-grade interactions**. The system is designed for:

✅ **Regular Users**: Upload, query, and learn from documents  
✅ **Administrators**: Manage users and monitor system health  
✅ **External Systems**: Integrate with OpenAI, Google OAuth, storage  

All use cases include proper **preconditions**, **main flows**, **alternate flows**, and **postconditions** for comprehensive system understanding.
