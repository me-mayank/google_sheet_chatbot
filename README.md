# ICPC Context-Driven Document Assistant

An advanced Retrieval-Augmented Generation (RAG) assistant designed for ICPC Coaches, built strictly to the specifications of the Product Requirements Document.

This application syncs directly with an evolving, unformatted public Google Doc without requiring Google API authentication, processes the unstructured text into a semantic date-based schema, and strictly grounds LLM responses to avoid hallucinations using a strict conversational pipeline.

## Features

- **Auth-less Google Doc Syncing:** Fetches public Google Docs natively.
- **Robust Parsing:** Uses Regex pattern matching to break down loose unstructured notes into strict chronological trees (`ParsedDocument`).
- **In-Memory Cache & TTL History:** Persists document context across the app and manages conversational history natively without a database.
- **Hot-Reloadable Application Context:** Administrators can swap out system instructions (e.g. `icpc_default.json`) on the fly via `/api/admin/context/reload` without restarting the application.
- **Grounded Chat Pipeline:** Rigorous LLM grounding rules intercept AI responses, sanitize them, and extract machine-parseable source citations linked directly back to specific document sections.
- **Security & Resilience:** Complete API Rate Limiting (via `slowapi`) and robust centralized error handling returning deterministic UI states for 503s, 502s, etc.

## Architecture Overview

```mermaid
graph TD
    A[Frontend UI - Vite/React] -->|POST /api/chat| B(FastAPI Backend)
    A -->|GET /api/document/status| B
    A -->|POST /api/document/refresh| B
    
    subsigned Context Layer
        B -->|Reads Context| C[core/contexts/*.json]
        C -->|Hot-Reloaded by| D[Admin Endpoint]
    end
    
    subgraph Data Pipeline
        B -->|Background Task| E[Google Docs Scraper]
        E -->|Parses via Regex| F[Document Processor]
        F -->|Writes to| G[(In-Memory Cache)]
    end
    
    subgraph LLM Pipeline
        B -->|Reads Cache + History| H[Chat Orchestrator]
        H -->|Generates Prompt| I[Groq API LLM]
        I -->|Returns Answer + XML Sources| H
        H -->|Strips XML, Formats Citations| A
    end
```

## Running the Application

### 1. Configure Environment

In the `backend` folder, create a `.env` file (you can copy `.env.example`):
```env
GROQ_API_KEY=gsk_...
GOOGLE_DOC_URL=https://docs.google.com/document/d/your_doc_id/edit?usp=sharing
DEFAULT_CONTEXT_ID=icpc_default
```

### 2. Run via Docker Compose (Production)

The quickest way to run the full stack is via Docker.
```bash
docker-compose up --build
```
- The **Frontend** will be available at `http://localhost:5173`
- The **Backend API** will be available at `http://localhost:8000`

### 3. Run Locally (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Hot-Reloading Contexts

The application's core logic and prompt behavior are controlled via JSON configuration files stored in `backend/app/core/contexts/`.

To change the assistant's behavior:
1. Edit or add a new JSON file in `backend/app/core/contexts/`.
2. Hit the admin endpoint to instantly reload the context across the application:
   ```bash
   curl -X POST http://localhost:8000/api/admin/context/reload
   ```
3. Future chat requests will immediately reflect the new instructions with zero downtime.
