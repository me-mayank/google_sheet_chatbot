# Context-Driven Document Assistant

## Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 21 August 2026
**Status:** MVP Specification

---

# 1. Product Overview

## 1.1 Product Name

**Context-Driven Document Assistant**

## 1.2 Purpose

Context-Driven Document Assistant is a general-purpose AI chatbot that answers questions using a publicly accessible Google Doc as its source of truth. The application is intentionally generic: the behavior, purpose, and domain-specific instructions are controlled by a backend-configured context prompt, while the Google Doc supplies the actual knowledge.

The system will use a **publicly accessible Google Doc as the primary source of truth**.

Team members will maintain the Google Doc with structured daily updates containing:

* Dates
* Contests conducted
* Contest results
* Team/member progress
* Topics practiced
* Problems encountered
* Important observations
* Upcoming activities
* Decisions and action items

Users can ask natural-language questions through a simple web interface. To reuse the system for another purpose, the maintainer should only need to change the context prompt and Google Doc URL rather than modify the frontend or core application logic.

Examples:

* "What happened this week?"
* "What did the teams do yesterday?"
* "What is the current official status?"
* "What has happened so far?"
* "What contests have been conducted?"
* "What is planned for next week?"
* "Give me a summary of the ICPC preparation so far."

The assistant should answer using information available in the Google Doc and clearly indicate when the requested information cannot be found.

---

# 2. Problem Statement

Many useful workflows already have information maintained in a Google Doc, but users have to manually read and search the document to answer questions. The system should turn that document into a conversational knowledge source.

The document may contain:

* Daily messages
* Team discussions
* Contest results
* Preparation updates
* Google Docs
* Informal communication

This creates several problems:

1. The official representative has to manually read through historical information.
2. Important process updates can be missed.
3. It is difficult to quickly understand the current official status.
4. Historical information is difficult to search conversationally.
5. A concise process summary has to be prepared manually.

The proposed system provides a conversational interface over the team's structured Google Doc.

---

# 3. Product Goals

## Primary Goals

### G1 — Single Source of Truth

The configured Google Doc should act as the primary source of truth for the application's knowledge.

### G2 — Natural Language Access

The coach should be able to ask questions naturally instead of manually searching the document.

### G3 — Accurate Grounded Answers

The assistant should answer based on information contained in the source document and avoid inventing facts.

### G4 — Context-Driven Answers

The backend should allow the project maintainer to change the **application context/instructions** without changing the frontend or core application logic. The context tells the LLM what the document represents, what to focus on, how to answer, and what constraints to follow.

For example, the same application could be configured with contexts such as:

* ICPC process assistant
* Project documentation assistant
* Event operations assistant
* Study material assistant
* Internal knowledge assistant

The LLM should read the configured Google Doc together with the configured context and answer the user's question accordingly.

### G5 — Historical Queries

The system should support questions involving dates and historical events.

Examples:

* "What happened between August 15 and August 20?"
* "What was the first contest?"
* "How has Team A performed over the last month?"

### G6 — Summarization

The assistant should be capable of summarizing:

* Daily progress
* Weekly progress
* Monthly progress
* Overall preparation status

### G7 — Minimal Maintenance

The system should require minimal technical maintenance after deployment.

Updating the Google Doc should be sufficient for adding new information.

---

# 4. Non-Goals

The MVP will NOT attempt to:

* Automatically edit the Google Doc.
* Automatically collect information from WhatsApp/Telegram.
* Automatically track Codeforces accounts.
* Automatically judge team performance without source data.
* Replace the team's existing documentation process.
* Implement complex autonomous agents.
* Require a vector database from day one.
* Support multiple organizations in the MVP.
* Build a complex admin dashboard.

These can be considered future enhancements.

---

# 5. Target Users

## Primary User

### Official ICPC Representative / Coach

The official representative wants quick answers about:

* Current preparation status
* Official process status
* Activities completed
* Activities currently in progress
* Upcoming activities
* Actions requiring her involvement or permission
* Historical events

She is not the operational owner of the team's daily preparation. The application should therefore focus on **information access**, not team management or coaching.

The representative is assumed to be non-technical.

Therefore, the UI should be extremely simple.

---

## Secondary User

### ICPC Team / Organizers

Team members or organizers maintain the Google Doc and configure/update the backend context when needed.

They may also use the chatbot to verify information.

---

# 6. Core User Journey

```text
Team members / organizers
     |
     | Update Google Doc
     ↓
Google Doc
     |
     | Fetch / Sync
     ↓
Backend
     |
     | Process document
     ↓
     Context + Document
     |
     | LLM reads source using selected context
     ↓
    LLM
     |
     ↓
React Chat Interface
     |
     ↓
 Official Representative
```

---

# 7. Functional Requirements

## FR-1: Google Doc Connection

The system must allow the application to connect to a publicly accessible Google Doc.

The initial MVP should support a Google Docs URL such as:

```text
https://docs.google.com/document/d/<DOCUMENT_ID>/edit
```

The backend should extract the document ID.

The system should validate that the document can be accessed.

---

# 8. Document Retrieval

The backend should retrieve the latest content of the Google Doc.

The implementation should avoid unnecessary requests to Google.

Possible strategies:

* Cache document content.
* Refresh periodically.
* Refresh when a user starts a new chat session.
* Provide a manual refresh mechanism.

The exact strategy should be decided during implementation planning.

---

# 9. Document Processing

The backend should convert the Google Doc into clean text.

The system should preserve useful structure such as:

* Headings
* Dates
* Sections
* Lists
* Tables where practical

Example source:

```text
## 21 August 2026

### Contest

Contest #1 conducted.

### Results

Team A - 4 solved
Team B - 3 solved
Team C - 2 solved

### Topics

Graphs
Greedy
Binary Search

### Observations

Team A performed strongly.
Team C struggled with implementation.

### Next Steps

Graph practice tomorrow.
```

The processed representation should retain the date and section hierarchy.

---

# 10. Structured Document Format

The project should encourage the team to maintain a consistent format.

Recommended structure:

```text
# ICPC 2026 — IET Lucknow

## Current Status

Last Updated:
Teams:
Current Focus:
Major Concerns:
Upcoming Activities:

---

## 21 August 2026

### Contest

...

### Results

...

### Topics Covered

...

### Important Observations

...

### Problems / Issues

...

### Decisions

...

### Next Steps

...

---

## 22 August 2026

...
```

The system should not strictly depend on every section being present.

---

# 11. Chat Interface

The React frontend should provide a simple conversational interface.

The UI should contain:

* Application title
* Chat history
* User messages
* Assistant responses
* Input field
* Send button
* Loading state
* Error state
* Document sync status

Example:

```text
┌─────────────────────────────────────────────┐
│ ICPC Coach Assistant                        │
│ ● Source synced: 2 minutes ago              │
├─────────────────────────────────────────────┤
│                                             │
│ Coach                                       │
│ What happened this week?                    │
│                                             │
│ Assistant                                   │
│ This week the teams conducted 3 contests... │
│                                             │
├─────────────────────────────────────────────┤
│ Ask anything about ICPC preparation...  ➤   │
└─────────────────────────────────────────────┘
```

---

# 12. Suggested Questions

The frontend should display suggested questions when the chat is empty.

Examples:

```text
What happened this week?

Give me the current ICPC status.

How are the teams performing?

What are the major problems right now?

What is planned next?

Summarize the preparation so far.
```

These should be clickable.

---

# 13. Question Answering

The backend should accept natural-language questions.

Example API request:

```json
{
  "question": "What happened this week?"
}
```

The backend should:

1. Receive the question.
2. Load the currently configured application context.
3. Retrieve or prepare the Google Doc content required by that context.
4. Construct a grounded prompt containing the context, document content, and question.
5. Send the prompt to the LLM.
6. Generate an answer.
7. Return the answer to the frontend.

The frontend should not need to know or manage the context. Context configuration is a backend concern.

---

# 13A. Backend-Configurable Context

The application must support changing the assistant's context from the backend without requiring frontend changes.

The context should be treated as a configurable instruction layer between the document and the LLM.

Conceptually:

```text
Google Doc
     +
Selected Backend Context
     +
User Question
     ↓
    LLM
     ↓
Context-aware answer
```

Example context:

```text
You are an assistant helping the official ICPC representative
understand the current official process of IET Lucknow's ICPC
participation.

Read the supplied Google Doc as the source of truth.
Focus on completed activities, current status, upcoming actions,
permissions, applications and other official process information.
Do not assume that the user is asking about team coaching or
competitive performance unless the document and question require it.
```

The backend should make it straightforward to replace this context with another context later.

The implementation plan should recommend whether the context should be stored in environment configuration, a backend configuration file, a database, or an admin/configuration endpoint. For the MVP, the simplest maintainable option should be preferred.

---

# 14. Grounding Rules

The assistant must prioritize factual accuracy.

The system prompt should enforce:

1. Answer using the supplied ICPC documentation.
2. Do not invent events, results, people, dates, or statistics.
3. If information is unavailable, explicitly say so.
4. Distinguish between documented facts and reasonable interpretation.
5. Do not present assumptions as facts.

Example:

User:

```text
What was Team A's score on August 10?
```

If the document contains no such information:

```text
I couldn't find Team A's score for August 10 in the ICPC documentation.
```

The model should NOT guess.

---

# 15. Temporal Queries

The system should support date-aware questions.

Examples:

```text
What happened yesterday?

What happened this week?

What happened between August 10 and August 20?

What was our first contest?

What did the teams work on last weekend?

How has Team A progressed since August 1?
```

The backend should provide date information to the retrieval layer when useful.

---

# 16. Summary Queries

The assistant should support summaries such as:

### Daily

```text
Give me today's update.
```

### Weekly

```text
Give me this week's progress.
```

### Monthly

```text
Summarize August.
```

### Overall

```text
Give me an overall ICPC preparation report.
```

The response should prioritize:

* Major achievements
* Contest performance
* Current preparation
* Problems
* Upcoming activities

---

# 17. Source References

Where practical, assistant responses should identify where information came from.

For example:

```text
According to the update from 21 August:

Team A solved 4 problems...
```

A future version may provide clickable references to the relevant document section.

For MVP, source references can simply include the date/section.

---

# 18. Conversation Context

The chatbot should maintain conversation context within a chat session.

Example:

User:

```text
What happened in Contest #3?
```

Assistant:

```text
Team A solved 5 problems...
```

User:

```text
What was their main weakness?
```

The assistant should understand that "their" refers to the relevant team/context from the previous message.

The system should avoid sending an unnecessarily large conversation history to the LLM.

---

# 19. Document Sync

The frontend should display the document's synchronization state.

Example:

```text
● Synced 3 minutes ago
```

Possible states:

```text
Synced
Syncing...
Sync failed
```

The application should provide a way to manually trigger synchronization if required.

---

# 20. Error Handling

The application should gracefully handle:

### Google Doc unavailable

```text
Unable to access the source document.
Please check the document's public access settings.
```

### LLM failure

```text
The assistant is temporarily unavailable.
Please try again.
```

### Empty document

```text
No usable ICPC information was found in the document.
```

### Network failure

Display a user-friendly error rather than a raw backend exception.

---

# 21. Backend Architecture

Recommended initial stack:

```text
Python
    |
FastAPI
    |
Document Service
    |
Retrieval Service
    |
LLM Service
    |
Cache / Storage
```

Suggested logical modules:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   │   ├── google_docs.py
│   │   ├── document_processor.py
│   │   ├── retrieval.py
│   │   ├── llm.py
│   │   └── chat.py
│   ├── models/
│   ├── schemas/
│   ├── core/
│   └── utils/
├── tests/
├── requirements.txt
└── .env
```

The exact architecture should be finalized during implementation planning.

---

# 22. Frontend Architecture

Recommended stack:

* React
* Vite
* Tailwind CSS
* Fetch/Axios for API communication

Possible structure:

```text
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWindow
│   │   ├── Message
│   │   ├── InputBox
│   │   ├── SuggestedQuestions
│   │   └── SyncStatus
│   ├── pages/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   └── App.jsx
```

Keep the frontend simple.

The primary interaction should be:

```text
Open website
      ↓
Ask question
      ↓
Receive answer
```

---

# 23. Initial Retrieval Strategy

### IMPORTANT

The MVP should NOT require vector embeddings.

The primary design assumption is that the LLM can read the Google Doc content directly when the document is small enough to fit comfortably within the model's context window.

The implementation should begin with a simple retrieval strategy.

Possible initial approach:

```text
Google Doc
    ↓
Fetch / cache
    ↓
Clean document text
    ↓
Backend context + question
    ↓
LLM reads document
    ↓
Grounded answer
```

If the document becomes too large, the implementation plan may evaluate simple:

* date filtering
* section filtering
* keyword/full-text search
* chunk-based retrieval

is sufficient.

---

# 24. Future Vector/RAG Architecture

If the document becomes large, the system should be designed so that retrieval can be introduced without rewriting the frontend or the context/LLM layer.

Future architecture:

```text
Google Doc
    ↓
Document Parser
    ↓
Chunking
    ↓
Embeddings
    ↓
Vector Database
    ↓
Semantic Retrieval
    ↓
Relevant Context
    ↓
LLM
```

Potential technologies:

* Qdrant
* pgvector
* Chroma
* Pinecone

The implementation team should recommend the most appropriate option if/when this becomes necessary.

---

# 25. LLM Layer

The LLM layer should be abstracted behind a service interface.

For example:

```text
LLMService
    ├── generate_answer()
    └── summarize()
```

This prevents the rest of the application from being tightly coupled to one model provider.

The implementation plan should recommend an appropriate model based on:

* Cost
* Latency
* Context window
* Answer quality
* Availability

---

# 26. API Requirements

The MVP should expose APIs similar to:

### Health

```http
GET /health
```

### Document Status

```http
GET /api/document/status
```

### Refresh Document

```http
POST /api/document/refresh
```

### Chat

```http
POST /api/chat
```

Example:

```json
{
  "question": "What happened this week?",
  "conversation_id": "optional-id"
}
```

Example response:

```json
{
  "answer": "This week the teams conducted...",
  "sources": [
    {
      "date": "2026-08-21",
      "section": "Contest"
    }
  ]
}
```

The exact API design should be refined during implementation planning.

---

# 27. Configuration

The application should use environment variables.

Example:

```text
OPENAI_API_KEY=
GOOGLE_DOC_URL=
MODEL_NAME=
```

No secrets should be committed to Git.

A `.env.example` file should be included.

---

# 28. Security

Although the source document is public, the chatbot itself should not expose secrets.

Requirements:

* Never expose API keys to the frontend.
* LLM calls must happen on the backend.
* Validate API input.
* Apply basic rate limiting if publicly deployed.
* Avoid logging sensitive information.
* Do not expose internal errors to users.

Authentication is optional for MVP but should be considered before public deployment.

---

# 29. Deployment

The application should be deployable as:

```text
React Frontend
      ↓
FastAPI Backend
      ↓
LLM API
      ↓
Google Docs
```

Potential hosting options:

### Frontend

* Vercel
* Netlify

### Backend

* Render
* Railway
* Fly.io
* Any suitable Python hosting platform

The implementation plan should recommend a deployment combination based on cost and simplicity.

---

# 30. Database Requirement

A traditional database is NOT mandatory for the first MVP if the system only needs:

* One Google Doc
* Cached document content
* Temporary conversation context

However, the architecture should allow a database to be introduced later.

Potential future uses:

* User accounts
* Conversation history
* Document versions
* Team statistics
* Contest records
* Analytics
* Vector embeddings

---

# 31. MVP Scope

The MVP is complete when the following workflow works:

```text
1. Public Google Doc exists.
       ↓
2. Backend fetches it.
       ↓
3. Backend processes its content.
       ↓
4. User opens React frontend.
       ↓
5. User asks a question.
       ↓
6. Backend retrieves relevant information.
       ↓
7. LLM answers using that information.
       ↓
8. User receives a grounded answer.
```

---

# 32. MVP Feature **Checklist**

* [ ] FastAPI backend
* [ ] React chat interface
* [ ] Public Google Doc integration
* [ ] Document fetching
* [ ] Document parsing
* [ ] Date/section-aware retrieval
* [ ] LLM integration
* [ ] Grounded answer generation
* [ ] Conversation context
* [ ] Suggested questions
* [ ] Sync status
* [ ] Manual document refresh
* [ ] Error handling
* [ ] Basic logging
* [ ] Environment configuration
* [ ] Deployment configuration
* [ ] README with setup instructions

---

# 33. Future Features

## Phase 2 — Better Retrieval

* Vector embeddings
* Semantic search
* Hybrid keyword + vector retrieval
* Source citations
* Document versioning

## Phase 3 — ICPC Analytics

Track:

* Team performance
* Problems solved
* Contest scores
* Average problems solved
* Topic-wise performance
* Improvement over time

Example:

```text
Team A

August 1:
2.1 avg problems

August 15:
3.4 avg problems

August 30:
4.2 avg problems
```

---

# 34. Future Process Dashboard

A future dashboard could show:

```text
ICPC 2026 — IET Lucknow

Teams                4
Contests             12
Problems Solved      184

Current Focus
────────────────────
Graphs
Dynamic Programming
Number Theory

Team Performance
────────────────────
Team A     ██████████
Team B     ████████
Team C     ██████
Team D     █████

Upcoming
────────────────────
Contest #13
Graph Practice
Mock Contest
```

The chatbot would remain the primary interface.

---

# 35. Future Automated Reporting

The system could automatically generate:

### Daily Summary

```text
Today's ICPC Update
```

### Weekly Process Report

```text
Weekly ICPC Process Update

Achievements:
...

Concerns:
...

Team Performance:
...

Next Week:
...
```

The report could eventually be delivered through:

* Email
* WhatsApp/Telegram integration
* Dashboard
* PDF

---

# 36. Design Principles

## Simple

The official representative should not need technical knowledge and should not need to understand the underlying AI architecture.

## Grounded

The assistant should prefer "I don't know" over hallucination.

## Context-Driven

The behavior and purpose of the assistant should be changeable from the backend by changing its context, without requiring frontend changes.

## Maintainable

The Google Doc should remain the team's primary workflow.

## Extensible

The architecture should allow RAG, analytics and additional data sources later.

## Fast

Normal questions should receive answers within a few seconds.

## Transparent

The assistant should make it clear when an answer comes from documented information.

---

# 37. Success Criteria

The MVP will be considered successful if the official representative can use it without assistance and reliably ask questions such as:

```text
What happened this week?

What did we do yesterday?

What is the current official status?

What has happened so far?

What actions are coming up?

Is there anything that requires my approval or signature?

What is planned next?

Give me a summary of our ICPC preparation.
```

and receive useful, factually grounded answers.

---

# 38. Implementation Planning Request

The implementation plan generated from this PRD should:

1. Review the requirements.
2. Identify ambiguities and potential technical risks.
3. Recommend the final technology stack.
4. Recommend the Google Docs integration approach for a public document.
5. Design the FastAPI backend architecture.
6. Design the React frontend architecture.
7. Define API contracts.
8. Define the document parsing strategy.
9. Design the initial context-driven document-to-LLM flow WITHOUT requiring vector embeddings.
10. Explain how retrieval/vector RAG can be added later if the document grows.
11. Recommend the LLM integration approach.
12. Define data models where necessary.
13. Define error handling.
14. Define security considerations.
15. Define testing strategy.
16. Define local development setup.
17. Define deployment architecture.
18. Break implementation into logical milestones.
19. Identify dependencies and risks.
20. Provide a recommended project directory structure.
21. Provide acceptance criteria for each milestone.
22. Explicitly distinguish MVP requirements from future enhancements.
23. Design how backend-configurable contexts should be represented and changed.
24. Explain how the system can support multiple contexts over the same Google Doc in the future.

The implementation plan should prioritize **simplicity, reliability and maintainability** over unnecessary infrastructure.

The goal is to build a working MVP quickly and leave clean extension points for future RAG, analytics and automation features.
