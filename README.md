# LearnAgent

LearnAgent is a document-grounded AI learning assistant built with Next.js and TypeScript. It allows users to upload study material and interact with it through document-based chat, quiz generation, and study-plan generation.

The application uses the Groq API (specifically pointing to models like Llama 3.3 70B or `openai/gpt-oss-120b`) to provide fast, intelligent responses strictly based on the uploaded documents.

## Features

- **Document Upload**: Users can upload study materials (PDF, TXT, MD, CSV, JSON).
- **Document-Grounded Chat**: Ask questions and get answers strictly sourced from the uploaded documents. The application uses server-side keyword scoring to find relevant documents and constructs the context for the Groq LLM.
- **Quiz Generation**: Automatically generate quizzes based on your study topics or uploaded documents. Supports Multiple Choice, Multiple Select, Short Answer, and Fill-in-the-Blank formats.
- **Study Plan Generation**: Generate personalized study schedules based on your documents.
- **Session Handling**: Chat history is saved locally in the browser.
- **Streaming AI Responses**: Real-time word-by-word streaming of responses.

## Architecture & Workflow

The system relies on a server-side keyword-based relevance scoring mechanism (not vector embeddings). 

1. **User Query**: The user asks a question.
2. **Keyword Extraction**: The server extracts keywords from the query.
3. **Document Relevance Scoring**: The server scores uploaded documents based on exact keyword hits and filename matches.
4. **Relevant Document Selection**: The top relevant documents are selected.
5. **Context Construction**: The server constructs a context prompt from the selected documents.
6. **Groq LLM**: The prompt is sent to the Groq API.
7. **Streamed Answer**: The AI streams the response back to the Next.js Interface.
8. **Server-Controlled Source Citation**: The server automatically appends the primary source file used.

## Technology Stack

- **Next.js (v15)**: React framework for the interface and API routes.
- **TypeScript**: Static typing for robust code.
- **Tailwind CSS**: Utility-first CSS framework for styling.
- **Groq API**: High-speed LLM inference.
- **PDF-Parse**: Parsing uploaded PDF documents.
- **React Markdown**: Rendering AI responses.

## Project Structure

```
app/                 # Next.js App Router (Pages & Layouts)
  api/               # API Routes (/api/chat, /api/quiz, /api/upload, /api/studyplan)
components/          # React Components (ChatPanel, StudyPlanPanel, etc.)
lib/                 # Core logic, store, and Groq API wrappers (e.g., ollama.ts)
public/              # Static assets
package.json         # Dependencies and scripts
next.config.js       # Next.js configuration
tailwind.config.js   # Tailwind configuration
tsconfig.json        # TypeScript configuration
README.md            # This documentation
.env.example         # Example environment variables
```

*Note: The file `lib/ollama.ts` is kept for backward compatibility but actually wraps the Groq API under the hood.*

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SathwikGoundla/RAG-AI_Agent_Project.git
   cd RAG-AI_Agent_Project
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Environment Setup:**
   Copy the example environment file and add your Groq API key:
   ```bash
   cp .env.example .env.local
   ```
   Open `.env.local` and set your key (get a free key at [Groq Console](https://console.groq.com)):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

## Known Limitations
- The RAG system uses simple keyword-based matching rather than advanced vector embeddings, which may affect semantic retrieval accuracy.
- Requires a valid Groq API key; the application cannot run fully offline.

## Author
Developed by Sathwik Goundla.
