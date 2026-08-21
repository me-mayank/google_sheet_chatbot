from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class DocumentStatusResponse(BaseModel):
    status: Literal["synced", "syncing", "sync_failed", "never_synced"]
    last_synced_at: Optional[datetime] = None
    document_too_large: bool = False
    error: Optional[str] = None
