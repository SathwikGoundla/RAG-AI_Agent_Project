# LearnAgent v2.0 — System Flow & Architecture

## Overview
LearnAgent is a **RAG-based Intelligent Learning Assistant** that leverages Groq AI API to provide intelligent tutoring, quiz generation, and personalized study planning from user-uploaded documents.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER (Browser)                      │
├─────────────────────────────────────────────────────────────────────┤
│  • React Components (ChatPanel, QuizPanel, StudyPlanPanel)          │
│  • Sidebar Navigation                                                │
│  • Session State Management (localStorage)                           │
└────────────────┬──────────────────────────────────────────────┬─────┘
                 │                                              │
                 ├──────────────────┬──────────────────────┬───┘
                 │                  │                      │
        ┌────────▼────────┐  ┌──────▼──────┐  ┌───────────▼────────┐
        │   /api/chat     │  │  /api/quiz  │  │ /api/studyplan     │
        │   (Streaming)   │  │  (Polling)  │  │   (Polling)        │
        └────────┬────────┘  └──────┬──────┘  └───────────┬────────┘
                 │                  │                      │
        ┌────────▼──────────────────▼──────────────────────▼────────┐
        │           API ROUTES LAYER (Next.js)                      │
        └────────────────┬──────────────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────────────────────────────┐
        │          BUSINESS LOGIC LAYER                             │
        ├──────────────────────────────────────────────────────────┤
        │  • Context Retrieval (findRelevantDocs)                  │
        │  • Message Processing                                    │
        │  • Prompt Construction                                   │
        │  • Response Generation                                   │
        └────────────────┬──────────────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────────────────────────────┐
        │          DATA ACCESS LAYER                                │
        ├──────────────────────────────────────────────────────────┤
        │  • DocStore (In-Memory + Disk Persistence)               │
        │  • .doc_store.json (Index)                               │
        │  • /uploaded_docs/ (File Storage)                        │
        └────────────────┬──────────────────────────────────────────┘
                         │
        ┌────────────────▼──────────────────────────────────────────┐
        │          EXTERNAL SERVICES                                │
        ├──────────────────────────────────────────────────────────┤
        │  • Groq AI API (llama-3.3-70b-versatile)                │
        │  • File Processing (pdf-parse, JSON, etc.)               │
        └──────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Document Upload Flow
```
User uploads file
    ↓
Client → /api/upload
    ↓
Server: Parse file (PDF, TXT, CSV, JSON, Images)
    ↓
Extract text content
    ↓
Store in DocStore
    ↓
Save to /uploaded_docs/ folder
    ↓
Persist index to .doc_store.json
    ↓
Update UI document list
```

### 2. Chat Flow (Streaming)
```
User submits query
    ↓
Client → /api/chat (POST with message + context)
    ↓
Server: Retrieve relevant docs using findRelevantDocs()
    ↓
Build RAG prompt (system + context + user query)
    ↓
Send to Groq API with stream: true
    ↓
Stream tokens back to client
    ↓
Client displays real-time output
    ↓
Save to localStorage session history
```

### 3. Quiz Generation Flow
```
User requests quiz from specific doc(s)
    ↓
Client → /api/quiz (POST with selected document)
    ↓
Server: Retrieve relevant document content
    ↓
Build prompt: "Generate MCQ, True/False, Short Answer questions"
    ↓
Send to Groq API (non-streaming)
    ↓
Parse JSON response into quiz structure
    ↓
Return formatted quiz to client
    ↓
Client displays questions (MCQ selector, True/False toggle, Text input)
    ↓
Client evaluates answers locally using ground truth
```

### 4. Study Plan Generation Flow
```
User requests personalized study plan
    ↓
Client → /api/studyplan (POST with preferences)
    ↓
Server: Retrieve all uploaded documents
    ↓
Build prompt with learning goals, time availability, difficulty
    ↓
Send to Groq API (non-streaming)
    ↓
Parse response into structured study schedule
    ↓
Return plan with timeline + milestones
    ↓
Client displays interactive study plan
```

---

## Component Interactions

### Frontend Components

| Component | Purpose | Features |
|-----------|---------|----------|
| **ChatPanel** | Real-time Q&A interface | Streaming responses, message history, document-based answers |
| **QuizPanel** | Interactive assessment | MCQ, T/F, Short Answer with instant feedback |
| **StudyPlanPanel** | Learning roadmap | Timeline, milestones, progress tracking |
| **Sidebar** | Navigation & docs | Document upload, session management, panel switching |

### Backend Services

| Module | Responsibility | Key Functions |
|--------|-----------------|----------------|
| **ollama.ts** | AI Integration | `ollamaCall()`, `ollamaStream()` |
| **store.ts** | Document Management | DocStore class (CRUD + persistence) |
| **route.ts** | API Endpoints | Chat, Quiz, StudyPlan, Upload handlers |

---

## Key Features & Flows

### 🔐 Retrieval-Augmented Generation (RAG)
- **Keyword-based relevance scoring** on server-side
- **Stops words filtering** to find meaningful terms
- **File name bonus scoring** for precise results
- **Ensures strict factuality**: AI answers ONLY from documents

### 💾 Persistent Document Store
- **In-memory cache** for fast access
- **Disk persistence** via `.doc_store.json`
- **Survives server restarts**
- **Maps file paths** for document recovery

### ⚡ Streaming & Polling
- **Chat API**: Real-time streaming for UX responsiveness
- **Quiz & Study Plan APIs**: Non-blocking polling
- **Client-side buffering**: Handles both request/response patterns

### 📄 Multi-format File Support
- **PDF, TXT, MD, CSV, JSON**: Text extraction
- **Images (PNG, JPG)**: Future OCR support
- **Automatic format detection** by file extension

---

## Error Handling & Validation

### API Errors
- ❌ Missing `GROQ_API_KEY`: Clear error message
- ❌ File upload failures: Validation on file type & size
- ❌ Groq API errors: HTTP status + message propagation
- ❌ DocStore errors: Graceful degradation, logging

### Client-Side Safeguards
- Empty query validation
- Document availability checks
- Session storage fallbacks
- Network error recovery

---

## Performance Considerations

| Aspect | Strategy |
|--------|----------|
| **Latency** | Groq API ~2-3s (vs 5-10s for local Ollama) |
| **Streaming Speed** | Word-by-word for perceived responsiveness |
| **Token Limits** | max_tokens: 2048 (Quiz/Plan balance) |
| **Temperature** | 0.2 (factual) for Chat/Quiz/Plan |
| **Caching** | DocStore in-memory + disk index |

---

## Technology Stack

### Frontend
- **Framework**: Next.js 15.1.7
- **UI Library**: React 18, Tailwind CSS
- **Markdown**: react-markdown + remark-gfm
- **Icons**: lucide-react

### Backend
- **Runtime**: Node.js (Next.js API Routes)
- **File Processing**: pdf-parse
- **AI**: Groq API (llama-3.3-70b-versatile)
- **Storage**: Filesystem (.doc_store.json + /uploaded_docs/)

### Development
- **Language**: TypeScript
- **Package Manager**: npm
- **Build Tool**: Next.js built-in

---

## Environment Configuration

### Required
```env
GROQ_API_KEY=your_key_here  # Get from https://console.groq.com
```

### Optional
- `NEXT_PUBLIC_*` variables: Exposed to browser
- Temperature/token limits: Configurable in ollama.ts

---

## File Structure Reference

```
learnagent/
├── app/
│   ├── api/
│   │   ├── chat/route.ts       # Streaming RAG chat
│   │   ├── quiz/route.ts       # Quiz generation
│   │   ├── studyplan/route.ts  # Study plan generation
│   │   └── upload/route.ts     # Document upload handler
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page UI
│   └── globals.css             # Global styles
├── components/
│   ├── ChatPanel.tsx           # Chat interface
│   ├── QuizPanel.tsx           # Quiz interface
│   ├── StudyPlanPanel.tsx      # Study plan interface
│   └── Sidebar.tsx             # Navigation & uploads
├── lib/
│   ├── ollama.ts               # Groq API client
│   └── store.ts                # Document storage
├── uploaded_docs/              # Uploaded files
├── .doc_store.json             # Document metadata index
└── package.json                # Dependencies

```

---

## Data Models

### DocRecord
```typescript
{
  id: string                    // UUID
  name: string                  // Original filename
  content: string               // Extracted text
  size: number                  // File size in bytes
  uploadedAt: string            // ISO timestamp
  filePath: string              // Disk location
}
```

### Message
```typescript
{
  role: 'user' | 'assistant' | 'system'
  content: string
}
```

---

## Future Enhancements
- OCR for images
- Multi-language support
- Advanced RAG (embeddings-based semantic search)
- Conversation memory management
- Export quiz results
- Collaborative sessions
