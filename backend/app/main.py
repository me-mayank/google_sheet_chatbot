from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .api import health, document, admin, chat
from app.core.exceptions import DocumentUnavailableError, LLMServiceError, EmptyDocumentError
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(title="Context-Driven Document Assistant API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(DocumentUnavailableError)
async def document_unavailable_handler(request: Request, exc: DocumentUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Unable to access the source document. Please check the document's public access settings."}
    )

@app.exception_handler(LLMServiceError)
async def llm_service_handler(request: Request, exc: LLMServiceError):
    return JSONResponse(
        status_code=502,
        content={"detail": "The assistant is temporarily unavailable. Please try again."}
    )

@app.exception_handler(EmptyDocumentError)
async def empty_document_handler(request: Request, exc: EmptyDocumentError):
    # Returns 200 with the error string as the assistant's answer
    return JSONResponse(
        status_code=200,
        content={
            "answer": "No usable ICPC information was found in the document.",
            "sources": [],
            "conversation_id": "error-conv"
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."}
    )

# Setup CORS (to be configured from environment in the future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to ALLOWED_ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(document.router)
app.include_router(admin.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Context-Driven Document Assistant API"}
