from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    context_id: Optional[str] = None

class SourceRef(BaseModel):
    date: str
    section: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef] = []
    conversation_id: str
