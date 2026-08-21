# Context-Driven Document Assistant — Implementation Plan
### Prepared for execution in Antigravity (agentic build environment)

**Source:** Context-Driven Document Assistant PRD v1.0 (21 August 2026)
**Plan version:** 1.0
**Plan date:** 21 August 2026

---

## How to use this plan in Antigravity

This plan is written as a sequence of **milestones**, each with a scoped task list, file targets, and acceptance criteria. Each milestone is sized to be handed to Antigravity as a single agentic task ("build milestone 2", "implement `google_docs.py` per milestone 1 spec", etc.), with enough detail that the agent doesn't need to re-derive architecture decisions already made here. Where a decision is ambiguous in the PRD, this plan makes the call explicitly so the agent has one source of truth instead of improvising mid-build.

---

## 1. Requirements Review Summary

The PRD is a single-tenant, single-document Q&A chatbot with three defining constraints:

- **No vector DB in the MVP** — the whole document is expected to fit in an LLM context window.
- **Context is backend-configurable and decoupled from the frontend** — the frontend never knows what "kind" of assistant it is.
- **Grounding is non-negotiable** — the system must refuse to guess rather than hallucinate.

Everything else (sync status, suggested questions, source references, conversation memory) is in service of those three constraints. The plan below treats the **context-injection mechanism** and the **retrieval-free grounding pipeline** as the architectural core, and treats UI polish as secondary.

---

## 2. Ambiguities and Technical Risks

| # | Ambiguity / Risk | Resolution Taken in This Plan |
|---|---|---|
| 1 | "Publicly accessible Google Doc" — fetch via export endpoint vs. Google Docs API + OAuth? | Use the anonymous **export endpoint** (`/export?format=txt`) for MVP. No OAuth, no service account. Documented as a hard requirement: doc must be shared "Anyone with the link — Viewer." Fallback to Docs API v1 read-only with a service account is the Phase 2 path if formatting fidelity (tables, headings) proves insufficient. |
| 2 | Doc size vs. context window — PRD assumes it "fits," but doesn't define a limit. | Enforce a soft limit (~40K tokens of doc text) with a `document too large` warning surfaced via `/api/document/status`. Above that, fall back to the simple keyword/date filtering described in §23 of the PRD rather than silently truncating. |
| 3 | Context storage medium (env var vs. file vs. DB vs. admin endpoint) | JSON config file (`backend/app/core/contexts/*.json`) loaded at startup, hot-reloadable via a `POST /api/admin/context/reload` endpoint. No DB required; no UI required. Simplest thing that satisfies "change context without touching frontend or core logic." |
| 4 | Conversation history growth (§18) — "avoid sending unnecessarily large history" | Cap at last 6 turns (3 user + 3 assistant), stored in-memory per `conversation_id` with a TTL (e.g., 2 hours), not persisted to disk. No DB needed for MVP. |
| 5 | Multi-context support (§38.24) — how would one Google Doc serve multiple contexts? | Design `context_id` as a first-class request parameter now (defaulting to a single configured context), even though the frontend only ever sends one value in MVP. This avoids an API-breaking change later. |
| 6 | LLM provider lock-in | Abstract behind `LLMService` interface (PRD §25). Default provider is the **Groq API (free tier)** — chosen for zero cost and very low latency; keep an adapter pattern so other providers can be swapped via `MODEL_PROVIDER` env var. |
| 10 | Groq free-tier rate limits could throttle a live demo | Groq's free tier caps requests/min, requests/day, and tokens/min per model (limits vary by model and change over time — verify current values at console.groq.com before launch). Plan mitigates this at the design level: single retry with backoff on 429 (§8), a short in-process request queue is NOT built (adds complexity disproportionate to MVP traffic), and the doc/token budget (§6) keeps each call's token usage minimal so the tokens/min ceiling is the more likely limiter than requests/min for this low-QPS single-tenant use case. |
| 7 | Source citation granularity (§17) | MVP cites at date+section granularity only, extracted via lightweight regex over the LLM's own structured output (see §9 below), not via post-hoc string matching against the doc (fragile) or a second LLM call (costly). |
| 8 | Rate limiting / auth (§28) | Optional for MVP per PRD, but plan includes a stub (`slowapi` middleware) wired in but permissive by default, so turning it on later is a config flip, not a rebuild. |
| 9 | Doc refresh cadence (§8) | Cache with a 5-minute TTL + refresh-on-new-session + manual refresh endpoint. No background scheduler/cron in MVP — refresh is lazy (triggered by requests), which avoids needing a task queue. |

---

## 3. Recommended Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Backend framework | **FastAPI** (Python 3.11+) | Matches PRD §21; async-friendly for LLM/HTTP calls; auto OpenAPI docs. |
| Backend server | Uvicorn | Standard FastAPI pairing. |
| HTTP client | `httpx` (async) | For Google Docs export fetch and LLM API calls. |
| LLM SDK | `groq` Python SDK (OpenAI-compatible) | Default provider — free tier; swappable via adapter. |
| Config | `pydantic-settings` | Typed env var loading; validates `.env` at startup. |
| Caching | In-process (Python dict + `asyncio.Lock`) — no Redis | Single-instance MVP; document is small; avoids infra. |
| Rate limiting (stub) | `slowapi` | Lightweight, optional-by-default. |
| Testing | `pytest`, `pytest-asyncio`, `respx` (HTTP mocking) | Standard, fast. |
| Frontend framework | **React 18 + Vite** | Matches PRD §22. |
| Styling | **Tailwind CSS** | Matches PRD §22; fast to build a clean minimal UI. |
| Frontend HTTP | `fetch` via a thin `apiClient.ts` wrapper | Avoids an axios dependency for a 4-endpoint API. |
| Deployment (frontend) | Vercel | Zero-config for Vite React apps. |
| Deployment (backend) | Render (Web Service, free/starter tier) | Simple Python deploys, no Docker required (though a Dockerfile is provided for portability). |

No database, no vector store, no message queue — consistent with PRD §30 and §23.

---

## 4. Google Docs Integration Approach

**MVP approach — anonymous export, no auth:**

1. Accept a Google Docs URL of the form `https://docs.google.com/document/d/<DOCUMENT_ID>/edit...`.
2. Extract `<DOCUMENT_ID>` via regex: `r"/document/d/([a-zA-Z0-9_-]+)"`.
3. Fetch plain text via: `https://docs.google.com/document/d/<DOCUMENT_ID>/export?format=txt`.
4. Validate: HTTP 200 and non-empty body. A non-200 (e.g., 401/403) means the doc isn't shared publicly → surface the exact "check sharing settings" error from PRD §20.
5. Store `raw_text`, `fetched_at`, and a `content_hash` (SHA-256) in the in-process cache. The hash lets `/api/document/status` report "changed since last sync" without re-parsing.

**Why not the Google Docs API v1:** it requires either OAuth consent or a service account granted access to the doc, which is friction the PRD explicitly wants to avoid ("publicly accessible" is the whole premise). The export endpoint keeps zero-credential access to public docs. This is called out as a **Phase 2 upgrade path** if the team later needs tables/formatting fidelity the export endpoint doesn't preserve well (Google's txt export flattens tables into tab-separated lines, which is usually acceptable but not perfect).

---

## 5. Document Parsing Strategy

Input: raw text from the export endpoint (headings arrive as plain lines, since `.txt` export strips Markdown-style `#` — Google Docs headings become plain text lines with no marker). Two supported authoring patterns:

1. **Markdown-style source** (if the team pastes/writes the doc using `#`/`##`/`###` conventions as shown in PRD §10) — parser looks for lines starting with `#` first.
2. **Google-native headings** (if the team uses Google Docs' actual Heading 1/2/3 styles) — the plain-text export loses style info, so the parser falls back to a **heuristic date-line detector**: a line matching a date pattern (`\d{1,2}\s+\w+\s+\d{4}`, `\w+\s+\d{1,2},?\s+\d{4}`, or `\d{4}-\d{2}-\d{2}`) on its own line is treated as a new day-section boundary; short standalone lines matching a known section-name whitelist (`Contest`, `Results`, `Topics`, `Topics Covered`, `Observations`, `Important Observations`, `Problems`, `Problems / Issues`, `Decisions`, `Next Steps`, `Current Status`) are treated as subsection boundaries.

**Recommendation to the team:** encourage the `#`/`##`/`###` Markdown convention from PRD §10 even though the doc lives in Google Docs — it survives the txt export losslessly and makes parsing trivial and robust. This is a one-line note for the README rather than a hard requirement, since PRD §10 already says the system "should not strictly depend on every section being present."

**Output data model** (see §12 for schema): a list of `DaySection` objects, each with `date`, an ordered list of `Subsection{title, content}`, plus a special `CurrentStatus` block if present at the top of the doc (per PRD §10's "Current Status" preamble).

This structure feeds directly into §9's grounded-prompt construction and into §17's source citation.

---

## 6. Context-Driven Document-to-LLM Flow (No Vector Embeddings)

This is the architectural core of the MVP, directly implementing PRD §13A and §23.

```
1. Request arrives: { question, conversation_id?, context_id? }
2. Load ContextConfig (from JSON config, keyed by context_id, default if omitted)
3. Get cached ParsedDocument (refresh if stale per §8 policy)
4. If ParsedDocument text is under the token budget:
       full_document_text -> prompt
   else:
       apply date/section/keyword filter (see §7 below) -> filtered_document_text -> prompt
5. Build system prompt:
       [ContextConfig.instructions]
       + [Grounding Rules block — fixed, not configurable]
       + [Document content block, clearly delimited]
6. Build user turn: last N conversation turns + current question
7. Call LLMService.generate_answer(system_prompt, turns)
8. Parse LLM output for an embedded citation marker (see §9)
9. Return { answer, sources[] }
```

The **Grounding Rules block is fixed and appended by the backend regardless of which context is active** — this is deliberate: PRD §14's grounding rules ("do not invent facts," "say so if unavailable") are a product-wide invariant, not something a context author should be able to accidentally omit. `ContextConfig.instructions` supplies only the *domain framing* (what the doc represents, what to focus on), never the grounding behavior itself.

---

## 7. Fallback Filtering Strategy (only if document exceeds token budget)

Not built in Milestone 1–4; stubbed as a clear extension point so it can be added without touching the API contract.

- **Date filtering:** if the question contains date language ("yesterday," "this week," "August 10–20"), resolve to a date range server-side (using the server's current date) and only include `DaySection`s whose date falls in range.
- **Keyword filtering:** fallback — score each `DaySection` by naive keyword overlap with the question, take the top-K sections by score.
- Both are pure Python, no external service, no embeddings — consistent with PRD §23's explicit instruction to avoid requiring vector search for the MVP.

---

## 8. Recommended LLM Integration

- `LLMService` interface with two methods per PRD §25: `generate_answer(system_prompt, messages) -> AnswerResult` and `summarize(system_prompt, document_text, summary_type) -> AnswerResult`.
- Default provider: **Groq API (free tier)**, called via the `groq` Python SDK, which exposes an OpenAI-compatible `chat.completions` interface — this makes the `GroqAdapter` implementation nearly identical in shape to a would-be OpenAI adapter, and keeps `LLMService` itself provider-agnostic.
- **Model selection on Groq:** recommend a currently-hosted Llama 3.x/4 instruct model (e.g., the `llama-3.3-70b-versatile` class) as the default — good instruction-following for grounding constraints and a large enough context window for the MVP's "whole doc in context" approach. Groq's model lineup changes over time; the exact model string should be verified against `https://console.groq.com/docs/models` at build time and set via `MODEL_NAME`, not hardcoded. Groq also hosts `openai/gpt-oss-*` models, which are a reasonable fallback if instruction-following on the grounding rules needs to be stricter.
- Provider selection via `MODEL_PROVIDER=groq|anthropic|openai` env var; only the Groq adapter is implemented in MVP, but the interface makes a second adapter a same-shape addition.
- **Cost:** effectively $0 on the free tier for this workload's expected volume (single representative, a handful of queries/day). No budget-tracking logic is needed in MVP, but the rate-limit handling below should not be skipped.
- **Rate limit handling (Groq-specific):** on a `429` response, the adapter should read the `retry-after` header/body Groq returns and honor it (rather than a blind fixed backoff), retry once, and on a second failure surface the PRD §20 "temporarily unavailable" message. This is a slightly more specific version of the generic timeout/retry policy, because free-tier 429s are the most likely real-world failure mode here — more likely than a genuine outage.
- Timeout + single retry (exponential backoff, max 1 retry) on transient/5xx errors; on failure, return the PRD §20 "assistant is temporarily unavailable" message rather than propagating a raw exception.

---

## 9. Grounded Answer + Source Citation Format

To get structured citations without a second LLM call or fragile string-matching, the system prompt instructs the model to end its answer with a hidden, machine-parseable block:

```
<answer>
...natural language answer...
</answer>
<sources>
[{"date": "2026-08-21", "section": "Results"}, ...]
</sources>
```

The backend strips the `<sources>` block before returning `answer` to the frontend, and parses it (with a `try/except` — if parsing fails, `sources` is returned as an empty list rather than erroring the whole request) into the `sources` field of the API response. This satisfies PRD §17 without needing a vector store or a second retrieval pass, and keeps citation granularity honest — it can only ever cite date/section pairs that genuinely exist in the `ParsedDocument`, because the model was only shown material tagged with those labels.

---

## 10. FastAPI Backend Architecture

```
backend/
├── app/
│   ├── main.py                  # app init, CORS, router mounting
│   ├── api/
│   │   ├── health.py            # GET /health
│   │   ├── document.py          # GET /api/document/status, POST /api/document/refresh
│   │   ├── chat.py              # POST /api/chat
│   │   └── admin.py             # POST /api/admin/context/reload (unauthenticated stub, MVP)
│   ├── services/
│   │   ├── google_docs.py       # fetch + doc-id extraction + validation
│   │   ├── document_processor.py# parse raw text -> ParsedDocument
│   │   ├── retrieval.py         # token-budget check + date/keyword filtering (§7)
│   │   ├── context_loader.py    # load/hot-reload ContextConfig from JSON
│   │   ├── llm.py               # LLMService interface + Anthropic adapter
│   │   └── chat.py              # orchestrates §6 flow end-to-end
│   ├── models/
│   │   └── document.py          # ParsedDocument, DaySection, Subsection dataclasses
│   ├── schemas/
│   │   ├── chat.py              # ChatRequest, ChatResponse (Pydantic)
│   │   └── document.py          # DocumentStatusResponse
│   ├── core/
│   │   ├── config.py            # pydantic-settings Settings
│   │   ├── contexts/
│   │   │   └── icpc_default.json
│   │   └── cache.py             # in-process TTL cache
│   └── utils/
│       └── dates.py             # relative-date resolution ("this week" -> range)
├── tests/
│   ├── test_google_docs.py
│   ├── test_document_processor.py
│   ├── test_chat_flow.py
│   └── test_api.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

**Key design decision:** `services/chat.py` is the only module that knows the full §6 pipeline order. `api/chat.py` stays a thin HTTP adapter. This keeps the orchestration testable without spinning up FastAPI.

---

## 11. React Frontend Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWindow.jsx        # scrollable message list
│   │   ├── Message.jsx           # single bubble, renders sources chip if present
│   │   ├── InputBox.jsx          # textarea + send button, Enter-to-send
│   │   ├── SuggestedQuestions.jsx# shown only when chat history is empty
│   │   ├── SyncStatus.jsx        # polls /api/document/status every 60s
│   │   └── ErrorBanner.jsx       # renders PRD §20 error copy
│   ├── pages/
│   │   └── ChatPage.jsx          # composes the above; owns conversation_id + history state
│   ├── services/
│   │   └── apiClient.js          # fetch wrappers for the 4 endpoints
│   ├── hooks/
│   │   └── useChat.js            # message state, send(), loading/error state
│   ├── types/
│   │   └── chat.d.ts             # (if TS) shared shapes
│   └── App.jsx
├── index.html
├── tailwind.config.js
├── vite.config.js
└── package.json
```

`useChat.js` owns the `conversation_id` (generated client-side as a UUID on first message, per PRD §18) and trims what it sends — though history trimming is ultimately enforced server-side too, so a buggy client can't blow the context budget.

---

## 12. Data Models

```python
# models/document.py
@dataclass
class Subsection:
    title: str          # e.g. "Results"
    content: str

@dataclass
class DaySection:
    date: date           # parsed ISO date
    raw_date_label: str   # original text, e.g. "21 August 2026"
    subsections: list[Subsection]

@dataclass
class ParsedDocument:
    current_status: Optional[dict]   # free-form key/values from the "Current Status" block
    day_sections: list[DaySection]
    fetched_at: datetime
    content_hash: str
    token_estimate: int

# schemas/chat.py (Pydantic)
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    context_id: Optional[str] = None   # defaults to configured default context

class SourceRef(BaseModel):
    date: str
    section: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef] = []
    conversation_id: str

# schemas/document.py
class DocumentStatusResponse(BaseModel):
    status: Literal["synced", "syncing", "sync_failed", "never_synced"]
    last_synced_at: Optional[datetime]
    document_too_large: bool
    error: Optional[str] = None
```

No persistent database models in MVP — `ParsedDocument` and conversation history live in the in-process cache described in §3/§9.

---

## 13. Error Handling

Centralized in a FastAPI exception-handler layer, mapping internal exceptions to the exact user-facing copy from PRD §20:

| Internal exception | HTTP status | User-facing message |
|---|---|---|
| `DocumentUnavailableError` | 503 | "Unable to access the source document. Please check the document's public access settings." |
| `LLMServiceError` | 502 | "The assistant is temporarily unavailable. Please try again." |
| `EmptyDocumentError` | 200 (chat still "succeeds" but answers this way) | "No usable ICPC information was found in the document." |
| Any unhandled exception | 500 | Generic "Something went wrong. Please try again." — **never** the raw stack trace (PRD §20, §28). |
| Network timeout to Google/LLM | 504 | Mapped into the relevant message above depending on which upstream failed. |

All exceptions are logged server-side with full detail (see §14) before being converted to the sanitized user-facing response.

---

## 14. Security Considerations

- **No API keys in the frontend** — `GOOGLE_DOC_URL`, `ANTHROPIC_API_KEY` etc. live only in backend env vars; frontend only ever talks to the backend's own `/api/*` routes.
- **CORS** restricted to the deployed frontend origin (configurable via `ALLOWED_ORIGINS` env var; wildcard only in local dev).
- **Input validation** via Pydantic on every request body; `question` length-capped (e.g., 2,000 chars) to bound prompt-injection surface and cost.
- **Basic prompt-injection awareness:** the document content block in the system prompt is clearly delimited and the system prompt explicitly instructs the model to treat document content as data, not instructions — mitigates (not eliminates) the case where someone edits the public doc to include adversarial text aimed at the assistant.
- **Rate limiting stub** wired via `slowapi`, default limits generous (e.g., 60 req/min/IP) — effectively a safety net, not an MVP requirement, per PRD §28's "optional for MVP."
- **Logging hygiene:** never log full document text or full LLM prompts at `INFO` level (only at `DEBUG`, which is off in production); never log API keys (enforced by not passing `Settings` objects wholesale into log statements).
- **Auth:** explicitly out of scope for MVP (PRD §28) but the admin reload endpoint (§10) should at minimum be excluded from public deployment or protected by a shared-secret header (`X-Admin-Token`) — small enough to include now rather than retrofit.

---

## 15. Testing Strategy

| Layer | Approach |
|---|---|
| `google_docs.py` | Unit tests with `respx`-mocked HTTP responses: valid doc, 403 (private doc), timeout, malformed URL. |
| `document_processor.py` | Unit tests against fixture text files covering: full PRD §10 structure, missing sections, non-Markdown heading style, empty document. |
| `retrieval.py` | Unit tests for date-range resolution ("this week," "yesterday," explicit ranges) against a fixed "now." |
| `chat.py` (orchestration) | Integration-style tests with a fake `LLMService` (deterministic canned responses) to verify the full §6 pipeline wiring, citation parsing, and history trimming — without real API calls. |
| `context_loader.py` | Test hot-reload picks up a changed JSON file without a process restart. |
| API layer | `pytest` + FastAPI `TestClient` for all 4 endpoints, including each PRD §20 error path. |
| Frontend | Component tests (React Testing Library) for `Message`, `SyncStatus`, `SuggestedQuestions`; one end-to-end smoke test (Playwright, optional) covering "ask a question → see an answer" against a mocked backend. |
| Manual acceptance | The PRD §37 example questions run against a real seeded test doc before each milestone sign-off. |

No load/performance test suite in MVP — single-tenant, low-QPS use case (PRD §36 "Fast" only requires "a few seconds," not high throughput).

---

## 16. Local Development Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, GOOGLE_DOC_URL
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

`.env.example` (backend):
```
GROQ_API_KEY=
GOOGLE_DOC_URL=
MODEL_NAME=llama-3.3-70b-versatile
MODEL_PROVIDER=groq
ALLOWED_ORIGINS=http://localhost:5173
DOCUMENT_CACHE_TTL_SECONDS=300
DEFAULT_CONTEXT_ID=icpc_default
```

README should include: how to make a Google Doc "Anyone with the link — Viewer," how to author it in the §10 format, and how to add a new context JSON file.

---

## 17. Deployment Architecture

```
User Browser
     ↓ HTTPS
Vercel (React static build)
     ↓ HTTPS (fetch to backend)
Render Web Service (FastAPI, Uvicorn)
     ↓ HTTPS
   ┌───────────────┬──────────────────┐
   ↓                                  ↓
Google Docs export endpoint      Groq API
```

- Backend: single Render Web Service, `Dockerfile`-based build (portable to Fly.io/Railway without changes). Health check wired to `GET /health`.
- Frontend: Vercel project pointed at `frontend/`, env var `VITE_API_BASE_URL` set to the deployed Render URL.
- No background workers, no cron, no separate cache/DB service — matches the "minimal infra" mandate.
- Secrets (`GROQ_API_KEY`) set via Render's environment variable dashboard, never committed.

---

## 18. Milestones and Acceptance Criteria

### Milestone 0 — Project Scaffolding
**Scope:** repo structure (§10, §11), FastAPI app boots, React app boots, `.env.example` files, README skeleton, `Dockerfile`.
**Acceptance:** `GET /health` returns 200; `npm run dev` renders an empty chat shell; no hardcoded secrets in repo.

### Milestone 1 — Google Doc Ingestion
**Scope:** `google_docs.py`, `document_processor.py`, `models/document.py`, `/api/document/status`, `/api/document/refresh`.
**Acceptance:** Given a real public test Google Doc authored per PRD §10, `/api/document/refresh` succeeds and `/api/document/status` reports `synced`; a private doc returns the exact PRD §20 error message; all Milestone 1 unit tests pass.

### Milestone 2 — Context Layer
**Scope:** `context_loader.py`, one seeded `icpc_default.json` context (using the example context text from PRD §13A), admin reload endpoint.
**Acceptance:** Editing the JSON file and hitting the reload endpoint changes assistant behavior on the next `/api/chat` call, with zero frontend or `chat.py` orchestration changes required — this is the direct acceptance test for PRD Goal G4.

### Milestone 3 — Grounded Chat Pipeline
**Scope:** `llm.py` (Groq adapter), `chat.py` orchestration, `/api/chat`, citation parsing (§9), grounding rules block (§6).
**Acceptance:** All PRD §37 example questions, run against the seeded test doc, return factually correct answers; a question about a genuinely absent fact (e.g., a score for a date not in the doc) returns an explicit "couldn't find" response, never a fabricated one; each answer citing document content includes at least one `sources` entry that is verifiably present in the doc.

### Milestone 4 — Conversation Memory
**Scope:** in-process history cache keyed by `conversation_id`, TTL eviction, server-side turn-count cap (§18).
**Acceptance:** The PRD §18 "their main weakness" example resolves the pronoun correctly across two turns; history longer than the cap is truncated server-side even if the client sends more.

### Milestone 5 — Frontend Chat Experience
**Scope:** all components in §11, suggested questions (PRD §12), sync status polling (PRD §19), loading/error states.
**Acceptance:** A non-technical user can open the app, click a suggested question, and receive a rendered answer with no console errors; simulating a backend 503 shows the PRD §20 copy in the UI, not a raw error.

### Milestone 6 — Error Handling & Resilience Hardening
**Scope:** centralized exception handling (§13), LLM timeout/retry, empty-document path.
**Acceptance:** All four PRD §20 error scenarios are reproducible via test fixtures and each renders the specified copy end-to-end (backend response → frontend display).

### Milestone 7 — Security & Deployment Pass
**Scope:** CORS lockdown, input validation caps, rate-limit stub, `Dockerfile`, Render + Vercel deployment, admin-token protection on reload endpoint.
**Acceptance:** Deployed URLs are reachable publicly; frontend and backend on different origins communicate correctly under real CORS; no secret is present in any client-side bundle (verified by grepping the built `dist/` output).

### Milestone 8 — Documentation & Handover
**Scope:** README with setup, doc-authoring guide, context-authoring guide; PRD §32 checklist verified item-by-item.
**Acceptance:** A team member unfamiliar with the codebase can follow the README alone to add a second context (e.g., "Project documentation assistant") pointed at a different public doc, without editing frontend code — this is the direct acceptance test for PRD Goal G7 and the multi-context extensibility called out in §38.24.

---

## 19. Multi-Context Support — Future Path (PRD §38.24)

The MVP already carries the seams needed for this:

- `ChatRequest.context_id` exists in the schema from Milestone 3 onward, even though only one context is configured initially.
- `context_loader.py` loads *all* JSON files in `core/contexts/`, not just one — adding a context is "drop a new JSON file in, no code change."
- The only genuinely new work for true multi-context (e.g., a dropdown letting the user pick "ICPC assistant" vs. "Project docs assistant" against *different* Google Docs) is: (a) extending `ContextConfig` with its own `google_doc_url` field instead of relying on a single global `GOOGLE_DOC_URL`, and (b) a trivial frontend context-picker component. Neither requires touching the retrieval/grounding pipeline, which is the point of designing the seam now.

---

## 20. Dependencies and Risks Summary

| Risk | Likelihood | Mitigation |
|---|---|---|
| Team doesn't follow the recommended doc structure, parsing degrades | Medium | Heuristic date/section-line fallback (§5) + README guidance; parser is tested against "messy" fixtures, not just the ideal case. |
| Document grows beyond context window over the season | Medium (ICPC prep runs months) | Token budget check + graceful fallback filtering (§7) is designed in from Milestone 1, not bolted on later. |
| Google changes/restricts the anonymous export endpoint | Low-Medium | Abstracted behind `google_docs.py`; swapping to the authenticated Docs API is a single-module change, not a rewrite. |
| LLM provider outage or free-tier rate-limit throttling | Low-Medium (rate limits are the more realistic risk on a free tier) | Timeout + single retry honoring Groq's `retry-after` on 429s + clean user-facing degradation (§13), no cascading failure into the frontend. If usage grows beyond the free tier's daily/per-minute caps, upgrading to Groq's paid tier is a billing change only — no code change, since the adapter and `MODEL_PROVIDER=groq` config stay identical. |
| Public doc accidentally made private mid-demo | Medium (human error) | Explicit, friendly error message (§13) rather than a silent failure; `/api/document/status` surfaces it proactively. |

---

## 21. MVP vs. Future Enhancements (Explicit Split)

**In MVP (this plan builds):** everything in PRD §32's checklist — FastAPI backend, React chat UI, public Doc integration, parsing, date/section-aware fallback filtering, LLM integration, grounding, conversation memory, suggested questions, sync status, manual refresh, error handling, basic logging, env config, deployment config, README.

**Explicitly deferred (PRD §33–35, confirmed out of scope here):** vector embeddings / semantic or hybrid retrieval, document versioning, ICPC-specific analytics and dashboards, automated report generation/delivery (email, WhatsApp/Telegram), user accounts, persistent conversation history, multi-document/multi-org support, admin UI for context editing (JSON file editing is the MVP "admin UI").

---

## 22. Suggested Build Order for Antigravity Sessions

1. Milestone 0 (scaffolding) — one session.
2. Milestone 1 (Google Doc ingestion) — one session, needs a real seeded test doc created first.
3. Milestone 2 (context layer) — short session, mostly config + loader.
4. Milestone 3 (grounded chat pipeline) — the largest session; this is the product's core value and deserves the most review.
5. Milestone 4 (conversation memory) — short session, builds directly on Milestone 3.
6. Milestone 5 (frontend) — can start in parallel with Milestone 3/4 once API contracts from §12 are frozen.
7. Milestone 6 (error hardening) — short session, mostly test-writing against existing code paths.
8. Milestone 7 (security/deploy) — one session, plus a manual deployment verification pass.
9. Milestone 8 (docs/handover) — final pass, run the full PRD §37 acceptance list end-to-end.