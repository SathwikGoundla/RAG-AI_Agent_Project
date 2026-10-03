# LearnAgent v2.0 — Sequence Diagrams

## 1. Document Upload Sequence

```mermaid
sequenceDiagram
    actor User
    participant Browser as Browser/Client
    participant Sidebar as Sidebar Component
    participant UploadAPI as /api/upload
    participant FileParser as FileParser
    participant DocStore as DocStore
    participant FileSystem as File System
    participant Browser2 as localStorage
    
    User->>Browser: Click "Upload Document"
    User->>Browser: Select file (PDF/TXT/CSV/JSON/IMG)
    
    Browser->>Sidebar: File input event
    Sidebar->>UploadAPI: POST (file buffer, filename)
    
    UploadAPI->>FileParser: parseFile(buffer, mimeType)
    FileParser->>FileParser: detectFormat(filename)
    FileParser->>FileParser: parse based on type
    FileParser-->>UploadAPI: extracted content (string)
    
    UploadAPI->>DocStore: add(DocRecord)
    DocStore->>FileSystem: Write to /uploaded_docs/{uuid}_{filename}
    FileSystem-->>DocStore: File written ✓
    
    DocStore->>FileSystem: saveToDisk() → .doc_store.json
    FileSystem-->>DocStore: Metadata persisted ✓
    DocStore-->>UploadAPI: Record added ✓
    
    UploadAPI-->>Sidebar: 200 OK { docId, name, size }
    Sidebar->>Browser2: Save upload confirmation
    Sidebar->>Sidebar: Refresh document list
    Sidebar-->>User: Show "Document uploaded" + count
```

---

## 2. Chat (RAG-based Q&A) Sequence

```mermaid
sequenceDiagram
    actor User
    participant Browser as ChatPanel
    participant ChatAPI as /api/chat (Streaming)
    participant DocStore as DocStore
    participant AIClient as AIClient
    participant GroqAPI as Groq API
    participant Browser2 as localStorage
    
    User->>Browser: Type question + Click Send
    Browser->>Browser: Validate input (not empty)
    Browser->>ChatAPI: POST { query, selectedDocIds }
    
    ChatAPI->>DocStore: getAll()
    DocStore-->>ChatAPI: [DocRecord...]
    
    ChatAPI->>ChatAPI: findRelevantDocs(query)
    Note over ChatAPI: • Extract keywords<br/>• Filter stop words<br/>• Score each doc<br/>• Sort by relevance
    ChatAPI-->>ChatAPI: [Relevant DocRecord...]
    
    ChatAPI->>ChatAPI: constructRAGPrompt(docs, query)
    Note over ChatAPI: system: "You are RAG assistant.<br/>Answer ONLY from context."<br/><br/>context: [Top 3 doc excerpts]<br/><br/>user: query
    
    ChatAPI->>AIClient: ollamaStream(messages)
    AIClient->>GroqAPI: POST { model, messages, stream: true }
    
    loop Token Streaming (every 50-100ms)
        GroqAPI-->>AIClient: token chunk
        AIClient-->>ChatAPI: token chunk
        ChatAPI-->>Browser: token chunk (Server-Sent Events)
    end
    
    Browser->>Browser: Display tokens real-time
    Browser->>Browser: Accumulate full response
    
    ChatAPI->>ChatAPI: stripAISources(fullResponse)
    ChatAPI-->>Browser: 200 OK (stream complete)
    
    Browser->>Browser2: Save { role: 'user', content: query }
    Browser->>Browser2: Save { role: 'assistant', content: fullResponse }
    Browser->>Browser: Render formatted markdown (images, code, tables)
    Browser-->>User: Display complete answer + chat history
```

---

## 3. Quiz Generation Sequence

```mermaid
sequenceDiagram
    actor User
    participant Browser as QuizPanel
    participant QuizAPI as /api/quiz
    participant DocStore as DocStore
    participant AIClient as AIClient
    participant GroqAPI as Groq API
    
    User->>Browser: Select document + Click "Generate Quiz"
    Browser->>Browser: Validate selection (doc exists)
    Browser->>QuizAPI: POST { docId }
    
    QuizAPI->>DocStore: get(docId)
    DocStore-->>QuizAPI: DocRecord { name, content, ... }
    
    QuizAPI->>QuizAPI: Truncate content (if > 4000 tokens)
    
    QuizAPI->>QuizAPI: constructPrompt(docContent)
    Note over QuizAPI: "Generate 5 questions:<br/>- 2 MCQ (4 options)<br/>- 2 True/False<br/>- 1 Short Answer<br/>Return JSON only."
    
    QuizAPI->>AIClient: ollamaCall(messages)
    Note over AIClient: Non-streaming request<br/>(temperature: 0.2, max_tokens: 2048)
    
    AIClient->>GroqAPI: POST { model, messages, stream: false }
    GroqAPI-->>AIClient: { choices[0].message.content }
    
    AIClient-->>QuizAPI: JSON string with questions
    
    QuizAPI->>QuizAPI: parseQuizJSON(response)
    Note over QuizAPI: Extract:<br/>- questions: []<br/>- correctAnswers: []<br/>- explanations: []
    
    QuizAPI-->>Browser: 200 OK { questions, totalQuestions }
    
    Browser->>Browser: Render Question[0]
    Browser->>Browser: Show question text + options (MCQ/T/F/TextInput)
    Browser-->>User: Display interactive quiz
    
    User->>Browser: Select/Enter answer
    Browser->>Browser: Button click → selectAnswer(answer)
    
    Browser->>Browser: Move to next question
    Browser->>Browser: Repeat for all questions
    
    User->>Browser: Click "Submit Quiz"
    Browser->>Browser: evaluateAnswers()
    Note over Browser: Compare userAnswers<br/>vs correctAnswers<br/>Calculate score (%)
    
    Browser->>Browser: renderResults()
    Browser-->>User: Display Score + Explanations
```

---

## 4. Study Plan Generation Sequence

```mermaid
sequenceDiagram
    actor User
    participant Browser as StudyPlanPanel
    participant PrefForm as Preference Form
    participant PlanAPI as /api/studyplan
    participant DocStore as DocStore
    participant AIClient as AIClient
    participant GroqAPI as Groq API
    
    User->>Browser: Click "Generate Study Plan"
    Browser->>PrefForm: Show form (goal, days, difficulty)
    
    User->>PrefForm: Select Goal: "Learn Machine Learning"
    User->>PrefForm: Select Duration: 14 days
    User->>PrefForm: Select Difficulty: Intermediate
    User->>PrefForm: Click "Generate"
    
    PrefForm->>PlanAPI: POST { goal, durationDays, difficulty }
    
    PlanAPI->>DocStore: getAll()
    DocStore-->>PlanAPI: [All DocRecord...]
    
    PlanAPI->>PlanAPI: constructStudyPlanPrompt(prefs, docs)
    Note over PlanAPI: "Create a 14-day study plan for:<br/>Goal: Learn Machine Learning<br/>Difficulty: Intermediate<br/>Resources: [doc1, doc2, ...]<br/>Return: JSON with milestones"
    
    PlanAPI->>AIClient: ollamaCall(messages)
    Note over AIClient: Non-streaming request<br/>(temperature: 0.2)
    
    AIClient->>GroqAPI: POST { model, messages, stream: false }
    GroqAPI-->>AIClient: Complete response
    
    AIClient-->>PlanAPI: Study plan JSON
    
    PlanAPI->>PlanAPI: parseStudyPlan(response)
    Note over PlanAPI: Extract:<br/>- milestones: []<br/>- dailyTopics: []<br/>- resources: []<br/>- timeline: {}
    
    PlanAPI-->>Browser: 200 OK { studyPlan, milestones }
    
    Browser->>Browser: renderTimeline()
    Note over Browser: Day 1-3: Fundamentals<br/>Day 4-7: Core Concepts<br/>Day 8-12: Projects<br/>Day 13-14: Review
    
    Browser->>Browser: renderMilestones()
    Note over Browser: ✓ Understanding basics<br/>⏳ Implementing algorithms<br/>⭕ Review & Assessment
    
    Browser-->>User: Display interactive study plan
    Browser-->>User: Optional: Click milestone to expand details
```

---

## 5. Document Search & Relevance Scoring Sequence

```mermaid
sequenceDiagram
    participant ChatAPI
    participant Query as Query Input
    participant StopWords as Stop Words Filter
    participant Scoring as Scoring Engine
    participant DocStore as DocStore
    participant Results as Ranked Results
    
    ChatAPI->>ChatAPI: query = "What is machine learning?"
    
    ChatAPI->>Query: toLowerCase() + remove special chars
    Query-->>ChatAPI: "what is machine learning"
    
    ChatAPI->>Query: split by whitespace
    Query-->>ChatAPI: ["what", "is", "machine", "learning"]
    
    ChatAPI->>StopWords: Filter out: what, is
    StopWords-->>ChatAPI: ["machine", "learning"]
    
    ChatAPI->>Scoring: Begin scoring each document
    
    loop For each document
        Scoring->>DocStore: Get document content
        DocStore-->>Scoring: { name, content, ... }
        
        Scoring->>Scoring: For each keyword:
        Note over Scoring: score += count("machine" in content)<br/>score += count("learning" in content)<br/>cap each keyword at 5 hits
        
        Scoring->>Scoring: Filename bonus:
        Note over Scoring: if "machine" in docname → score += 10<br/>if "learning" in docname → score += 10
        
        Scoring-->>Results: { docId, score, name }
    end
    
    Results->>Results: Sort by score DESC
    Results-->>ChatAPI: Top 3 documents by relevance
    
    ChatAPI-->>ChatAPI: Construct RAG prompt with context
```

---

## 6. System Initialization Sequence

```mermaid
sequenceDiagram
    participant User as User
    participant Browser as Browser
    participant App as Next.js App
    participant DocStore as DocStore
    participant FileSystem as File System
    participant localStorage as localStorage
    
    User->>Browser: Open http://localhost:3000
    Browser->>App: Request page.tsx
    
    App->>DocStore: new DocStore()
    DocStore->>FileSystem: Check .doc_store.json exists?
    
    alt File exists
        FileSystem-->>DocStore: File data
        DocStore->>DocStore: loadFromDisk()
        DocStore->>DocStore: Filter by actual file existence
        Note over DocStore: Remove deleted doc entries
    else File doesn't exist
        DocStore->>DocStore: Initialize empty Map
    end
    
    DocStore-->>App: ✓ Loaded N documents
    
    App->>localStorage: Get 'chatSessions'
    localStorage-->>App: Previous chat history
    
    App->>App: Render LearnAgentApp
    App->>App: Render Sidebar + ChatPanel
    
    App-->>Browser: Render complete UI
    Browser-->>User: Display LearnAgent with:
         Note over Browser: ✓ Document list loaded<br/>✓ Chat history restored<br/>✓ Ready to use (if API key set)
```

---

## 7. Error Handling: Missing API Key Sequence

```mermaid
sequenceDiagram
    actor User
    participant Browser as ChatPanel
    participant ChatAPI as /api/chat
    participant AIClient as AIClient
    
    User->>Browser: Type question + Click Send
    Browser->>ChatAPI: POST request
    
    ChatAPI->>AIClient: ollamaStream(messages)
    
    AIClient->>AIClient: Check GROQ_API_KEY environment variable
    
    alt API Key Missing
        AIClient-->>ChatAPI: Error: "GROQ_API_KEY not set"
        ChatAPI-->>Browser: 400 Error { error: "❌ GROQ_API_KEY not set..." }
        Browser->>Browser: Render error banner
        Browser-->>User: Display: "Configure API key in .env.local"
    else API Key Present but Invalid
        AIClient->>GroqAPI: POST with invalid key
        GroqAPI-->>AIClient: 401 Unauthorized
        AIClient-->>ChatAPI: Error: "Groq error 401"
        ChatAPI-->>Browser: 401 Error
        Browser-->>User: Display: "Invalid API key"
    end
```

---

## 8. File Upload Error Flow

```mermaid
sequenceDiagram
    actor User
    participant Browser as Browser
    participant UploadAPI as /api/upload
    participant FileParser as FileParser
    
    User->>Browser: Select .exe file (unsupported)
    Browser->>UploadAPI: POST { file }
    
    UploadAPI->>FileParser: detectFormat("malware.exe")
    FileParser-->>UploadAPI: Format: "unknown"
    
    UploadAPI->>UploadAPI: validateFile(file)
    Note over UploadAPI: Check supported types:<br/>[.pdf, .txt, .md, .csv, .json, .png, .jpg]
    
    UploadAPI-->>Browser: 400 Error { error: "Unsupported file type" }
    Browser->>Browser: Display error toast
    Browser-->>User: "Only PDF, TXT, CSV, JSON, Images allowed"
```

---

## 9. Message Streaming Buffer Flow

```mermaid
sequenceDiagram
    participant GroqAPI as Groq API
    participant ChatAPI as /api/chat
    participant Browser as Browser Client
    participant UI as DOM/React
    
    GroqAPI-->>ChatAPI: token: "Hello"
    ChatAPI-->>Browser: "Hello"
    Browser->>Browser: buffer = "Hello"
    Browser->>UI: Render "Hello"
    
    GroqAPI-->>ChatAPI: token: " there"
    ChatAPI-->>Browser: " there"
    Browser->>Browser: buffer = "Hello there"
    Browser->>UI: Render "Hello there"
    
    GroqAPI-->>ChatAPI: token: ", I"
    ChatAPI-->>Browser: ", I"
    Browser->>Browser: buffer = "Hello there, I"
    Browser->>UI: Render "Hello there, I"
    
    GroqAPI-->>ChatAPI: token: " am"
    ChatAPI-->>Browser: " am"
    Browser->>Browser: buffer = "Hello there, I am"
    Browser->>UI: Render "Hello there, I am"
    
    Note over Browser: User sees real-time typing effect
    
    GroqAPI-->>ChatAPI: [END OF STREAM]
    ChatAPI-->>Browser: [Stream complete]
    Browser->>Browser: Save buffer to localStorage
    Browser-->>UI: Mark as "completed"
```

---

## 10. Complete User Session Lifecycle

```mermaid
sequenceDiagram
    actor User
    participant UI as LearnAgent UI
    participant API as Backend API
    participant Storage as Storage (Disk + Memory)
    participant AI as Groq AI
    
    %% Session Start
    User->>UI: Open application (Day 1)
    UI->>Storage: Load documents from .doc_store.json
    UI->>Storage: Load chat history from localStorage
    UI-->>User: Display interface
    
    %% First Action: Upload
    User->>UI: Upload "ML_Basics.pdf"
    UI->>API: /api/upload
    API->>Storage: Add to DocStore
    API->>Storage: Save to disk
    API-->>UI: Success
    
    %% Second Action: Chat
    User->>UI: Ask "What is supervised learning?"
    UI->>API: /api/chat
    API->>Storage: Find relevant docs
    API->>AI: Stream response from context
    AI-->>UI: Real-time tokens
    UI->>Storage: Save conversation
    UI-->>User: Display answer
    
    %% Third Action: Quiz
    User->>UI: Generate quiz
    UI->>API: /api/quiz
    API->>AI: Generate questions
    AI-->>UI: Quiz with 5 questions
    User->>UI: Answer all questions
    UI->>UI: Evaluate and show score
    
    %% Fourth Action: Study Plan
    User->>UI: Request study plan (7 days)
    UI->>API: /api/studyplan
    API->>AI: Generate personalized plan
    AI-->>UI: Timeline with milestones
    UI-->>User: Display interactive plan
    
    %% Session End
    User->>UI: Close browser
    UI->>Storage: Auto-save chat history to localStorage
    UI->>Storage: DocStore persisted to disk
    
    %% Session Resume (Day 2)
    User->>UI: Open application (Day 2)
    UI->>Storage: Load documents + history
    UI-->>User: Resume from where left off ✓
```

---

## Legend

| Symbol | Meaning |
|--------|---------|
| `→` | Synchronous request |
| `-->>` | Response/return |
| `loop` | Repeated sequence |
| `alt` | Conditional branch |
| `Note over` | Commentary/explanation |
| `X->>Y` | X calls Y |
| `Y-->>X` | Y returns to X |

