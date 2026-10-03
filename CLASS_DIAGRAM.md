# LearnAgent v2.0 — Class & Component Diagram

## High-Level Component Architecture

```mermaid
classDiagram
    class LearnAgentApp {
        -string title
        -ReactNode[] components
        +render()
    }

    class Sidebar {
        -DocRecord[] documents
        -string selectedPanel
        +handleUpload(): void
        +handleDelete(id): void
        +switchPanel(panel): void
        +renderDocList(): ReactNode
    }

    class ChatPanel {
        -Message[] messages
        -string inputValue
        -boolean isLoading
        +sendMessage(query): void
        +handleStream(): void
        +saveToHistory(): void
        +renderMessages(): ReactNode
    }

    class QuizPanel {
        -Question[] questions
        -number currentIndex
        -Answer[] userAnswers
        -boolean showResults
        +generateQuiz(): void
        +selectAnswer(answer): void
        +evaluateAnswers(): Score
        +renderQuestion(): ReactNode
    }

    class StudyPlanPanel {
        -StudyPlan plan
        -Milestone[] milestones
        -number progress
        +generatePlan(preferences): void
        +updateProgress(): void
        +renderTimeline(): ReactNode
    }

    class DocStore {
        -Map~string, DocRecord~ docs
        -string storeFilePath
        +add(record): void
        +delete(id): void
        +get(id): DocRecord
        +getAll(): DocRecord[]
        +loadFromDisk(): void
        +saveToDisk(): void
    }

    class Document {
        -string id
        -string name
        -string content
        -number size
        -string uploadedAt
        -string filePath
        +extractText(): string
        +getMetadata(): DocumentMetadata
    }

    class AIClient {
        -string apiKey
        -string modelName
        -string apiEndpoint
        +ollamaCall(messages): Promise~string~
        +ollamaStream(messages): Promise~Response~
        +constructPrompt(context, query): string
    }

    class ChatAPI {
        -DocStore docStore
        -AIClient aiClient
        +POST(request): Response
        -findRelevantDocs(query): DocRecord[]
        -constructRAGPrompt(context, query): string
        -stripAISources(text): string
    }

    class QuizAPI {
        -DocStore docStore
        -AIClient aiClient
        +POST(request): Response
        -generateQuestions(content): Question[]
        -parseQuizJSON(response): Quiz
    }

    class StudyPlanAPI {
        -DocStore docStore
        -AIClient aiClient
        +POST(request): Response
        -constructStudyPlanPrompt(prefs): string
        -parseStudyPlan(response): StudyPlan
    }

    class UploadAPI {
        -DocStore docStore
        -FileParser fileParser
        +POST(request): Response
        -parseFile(buffer, type): string
        -validateFile(file): boolean
        -storeDocument(record): void
    }

    class FileParser {
        +parsePDF(buffer): string
        +parseTXT(buffer): string
        +parseCSV(buffer): string
        +parseJSON(buffer): string
        +parseImage(buffer): string
        +detectFormat(filename): string
    }

    class Message {
        -string role
        -string content
        -string timestamp
    }

    class Question {
        -string id
        -string text
        -string type
        -string[] options
        -string correctAnswer
        -string explanation
    }

    class Quiz {
        -string docId
        -Question[] questions
        -number totalScore
        +evaluateAnswer(questionId, answer): boolean
    }

    class StudyPlan {
        -string goal
        -number durationDays
        -Milestone[] milestones
        -string[] resources
        +getProgress(): number
        +updateMilestone(id): void
    }

    class Milestone {
        -string id
        -string title
        -string date
        -string status
        -number progress
    }

    %% Relationships
    LearnAgentApp -->|contains| Sidebar
    LearnAgentApp -->|contains| ChatPanel
    LearnAgentApp -->|contains| QuizPanel
    LearnAgentApp -->|contains| StudyPlanPanel

    Sidebar -->|manages| DocStore
    ChatPanel -->|uses| ChatAPI
    ChatPanel -->|stores| Message
    QuizPanel -->|uses| QuizAPI
    QuizPanel -->|stores| Question
    QuizPanel -->|contains| Quiz
    StudyPlanPanel -->|uses| StudyPlanAPI
    StudyPlanPanel -->|contains| StudyPlan
    StudyPlanPanel -->|stores| Milestone

    ChatAPI -->|queries| DocStore
    ChatAPI -->|calls| AIClient
    QuizAPI -->|queries| DocStore
    QuizAPI -->|calls| AIClient
    StudyPlanAPI -->|queries| DocStore
    StudyPlanAPI -->|calls| AIClient
    UploadAPI -->|stores in| DocStore
    UploadAPI -->|uses| FileParser

    DocStore -->|manages| Document
    AIClient -->|calls| Groq["External: Groq API"]
```

---

## Detailed Class Specifications

### 1. Frontend Components (React)

#### LearnAgentApp (Root)
```typescript
class LearnAgentApp {
  private components: {
    sidebar: Sidebar,
    chatPanel: ChatPanel,
    quizPanel: QuizPanel,
    studyPlanPanel: StudyPlanPanel
  }
  
  private state: {
    activePanel: 'chat' | 'quiz' | 'plan'
    documents: DocRecord[]
  }
  
  render(): JSX.Element
  switchPanel(panel: string): void
}
```

#### Sidebar
```typescript
class Sidebar extends React.Component {
  state: {
    documents: DocRecord[],
    isUploading: boolean,
    uploadProgress: number
  }
  
  handleUpload(file: File): void
  handleDelete(docId: string): void
  handleSearch(query: string): DocRecord[]
  renderDocumentList(): JSX.Element
  renderUploadButton(): JSX.Element
}
```

#### ChatPanel
```typescript
class ChatPanel extends React.Component {
  state: {
    messages: Message[],
    inputValue: string,
    isLoading: boolean,
    selectedDocIds: string[]
  }
  
  sendMessage(query: string): Promise<void>
  handleStreamResponse(response: Response): AsyncIterable<string>
  renderMessages(): JSX.Element
  renderInputField(): JSX.Element
  saveMessageToHistory(msg: Message): void
}
```

#### QuizPanel
```typescript
class QuizPanel extends React.Component {
  state: {
    quiz: Quiz,
    currentQuestionIndex: number,
    userAnswers: string[],
    showResults: boolean,
    score: number
  }
  
  generateQuiz(docId: string): Promise<void>
  selectAnswer(answer: string): void
  evaluateAnswers(): Score
  renderQuestion(): JSX.Element
  renderResults(): JSX.Element
}
```

#### StudyPlanPanel
```typescript
class StudyPlanPanel extends React.Component {
  state: {
    studyPlan: StudyPlan,
    preferences: StudyPreferences,
    progress: number
  }
  
  generateStudyPlan(prefs: StudyPreferences): Promise<void>
  updateProgress(milestoneId: string): void
  renderTimeline(): JSX.Element
  renderMilestones(): JSX.Element
}
```

---

### 2. Backend Services (Node.js/TypeScript)

#### DocStore
```typescript
class DocStore {
  private docs: Map<string, DocRecord>
  private storeFilePath: string = '.doc_store.json'
  private uploadsDir: string = 'uploaded_docs'
  
  constructor()
  add(record: DocRecord): void
  delete(id: string): boolean
  get(id: string): DocRecord | undefined
  getAll(): DocRecord[]
  loadFromDisk(): Map<string, DocRecord>
  saveToDisk(): void
  getStats(): { count: number, totalSize: number }
}
```

#### Document (Data Model)
```typescript
interface DocRecord {
  id: string              // UUID
  name: string            // Filename
  content: string         // Extracted text
  size: number            // Bytes
  uploadedAt: string      // ISO timestamp
  filePath: string        // Disk path
}
```

#### AIClient (Groq Integration)
```typescript
class AIClient {
  private apiKey: string
  private model: string = 'llama-3.3-70b-versatile'
  private baseUrl: string = 'https://api.groq.com/openai/v1/chat/completions'
  
  constructor(apiKey: string)
  
  async ollamaCall(messages: Message[]): Promise<string>
  async ollamaStream(messages: Message[]): Promise<Response>
  
  private headers(): Record<string, string>
  private buildRequestBody(messages, stream): object
  private validateResponse(response): void
}
```

#### Message (Data Model)
```typescript
interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
  timestamp?: string
}
```

---

### 3. API Route Handlers

#### ChatAPI (/api/chat)
```typescript
class ChatAPI {
  private docStore: DocStore
  private aiClient: AIClient
  
  async POST(request: NextRequest): Promise<Response>
  
  private findRelevantDocs(query: string): DocRecord[]
  private constructRAGPrompt(
    context: DocRecord[],
    query: string
  ): Message[]
  
  private stripAISources(text: string): string
  private filterRelevantText(doc: DocRecord, query: string): string
}
```

#### QuizAPI (/api/quiz)
```typescript
class QuizAPI {
  private docStore: DocStore
  private aiClient: AIClient
  
  async POST(request: NextRequest): Promise<Response>
  
  private generateQuestions(content: string): Question[]
  private parseQuizJSON(response: string): Quiz
  private validateAnswers(quiz: Quiz, answers: string[]): Score
}
```

#### StudyPlanAPI (/api/studyplan)
```typescript
class StudyPlanAPI {
  private docStore: DocStore
  private aiClient: AIClient
  
  async POST(request: NextRequest): Promise<Response>
  
  private constructStudyPlanPrompt(prefs: StudyPreferences): string
  private parseStudyPlan(response: string): StudyPlan
  private generateMilestones(weeks: number): Milestone[]
}
```

#### UploadAPI (/api/upload)
```typescript
class UploadAPI {
  private docStore: DocStore
  private fileParser: FileParser
  
  async POST(request: NextRequest): Promise<Response>
  
  private parseFile(buffer: Buffer, mimeType: string): string
  private validateFile(file: File): boolean
  private storeDocument(record: DocRecord): void
}
```

---

### 4. Utility Classes

#### FileParser
```typescript
class FileParser {
  parsePDF(buffer: Buffer): Promise<string>
  parseTXT(buffer: Buffer): string
  parseCSV(buffer: Buffer): string
  parseJSON(buffer: Buffer): string
  parseImage(buffer: Buffer): Promise<string>
  
  detectFormat(filename: string): 'pdf' | 'txt' | 'csv' | 'json' | 'image'
  extractMetadata(filename: string): FileMetadata
}
```

#### Question (Data Model)
```typescript
interface Question {
  id: string
  text: string
  type: 'mcq' | 'truefalse' | 'shortanswer'
  options: string[]           // For MCQ
  correctAnswer: string       // Ground truth
  explanation: string         // User feedback
  difficulty: 'easy' | 'medium' | 'hard'
}
```

#### Quiz (Data Model)
```typescript
interface Quiz {
  id: string
  docId: string
  questions: Question[]
  totalScore: number
  userAnswers: string[]
  completedAt: string
  
  evaluateAnswer(questionId: string, answer: string): boolean
  getScore(): Score
}
```

#### StudyPlan (Data Model)
```typescript
interface StudyPlan {
  id: string
  goal: string
  startDate: string
  durationDays: number
  milestones: Milestone[]
  resources: DocRecord[]
  progress: number
  
  updateMilestone(id: string): void
  getProgress(): number
}

interface Milestone {
  id: string
  title: string
  dueDate: string
  status: 'pending' | 'in-progress' | 'completed'
  progress: number
}
```

---

## Data Flow Between Classes

```
ChatPanel
  ↓ (sendMessage)
ChatAPI
  ↓ (findRelevantDocs)
DocStore (getAll + scoring)
  ↓ (returns relevant docs)
AIClient
  ↓ (ollamaStream)
Groq API
  ↓ (token stream)
ChatPanel (update UI in real-time)
```

```
UploadAPI
  ↓ (parseFile)
FileParser
  ↓ (returns extracted content)
DocStore (add + saveToDisk)
  ↓ (persists to .doc_store.json)
Sidebar (refreshes document list)
```

---

## Database/Storage Classes

### DocStore Table-like Structure
| Field | Type | Index | Notes |
|-------|------|-------|-------|
| id | UUID | ✓ Primary | Unique per document |
| name | String | | File name |
| content | Text | | Full text content |
| size | Number | | File size bytes |
| uploadedAt | DateTime | ✓ | Insertion timestamp |
| filePath | String | ✓ | Disk location |

---

## Inheritance & Polymorphism

### FileParser Polymorphism
```typescript
interface Parseable {
  parse(buffer: Buffer): Promise<string>
  validate(file: File): boolean
}

class PDFParser implements Parseable { ... }
class TextParser implements Parseable { ... }
class CSVParser implements Parseable { ... }
class JSONParser implements Parseable { ... }
```

---

## Design Patterns Used

| Pattern | Implementation | Purpose |
|---------|----------------|---------|
| **Singleton** | DocStore | Single instance manages all documents |
| **Factory** | FileParser | Creates parsers by file type |
| **Observer** | React State | Components react to data changes |
| **Strategy** | API Routes | Different handlers for different flows |
| **Adapter** | AIClient | Abstracts Groq API differences |

---

## Concurrency & Thread Safety

- **React State**: Automatic re-rendering on state changes
- **Streaming**: Non-blocking async/await
- **File I/O**: Node.js handles concurrent file operations
- **Disk Persistence**: Atomic writes to `.doc_store.json`

---

## Module Dependencies

```
Frontend (React)
  ├── Sidebar → (uses) → ChatPanel, QuizPanel, StudyPlanPanel
  ├── ChatPanel → (calls) → /api/chat
  ├── QuizPanel → (calls) → /api/quiz
  └── StudyPlanPanel → (calls) → /api/studyplan

Backend (Node.js)
  ├── /api/chat → (uses) → DocStore, AIClient
  ├── /api/quiz → (uses) → DocStore, AIClient
  ├── /api/studyplan → (uses) → DocStore, AIClient
  └── /api/upload → (uses) → DocStore, FileParser

Shared
  ├── DocStore → (persists to) → .doc_store.json, /uploaded_docs/
  └── AIClient → (calls) → Groq API
```

