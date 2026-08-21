from fastapi import APIRouter, Request
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import process_chat_request
from app.core.rate_limit import limiter
from app.services.chat import process_chat_request

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat_endpoint(request: Request, body: ChatRequest):
    return await process_chat_request(body)
