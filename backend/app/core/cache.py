import asyncio
from typing import Optional
from datetime import datetime, timezone
from app.models.document import ParsedDocument
from app.core.config import settings

class DocumentCache:
    def __init__(self):
        self._document: Optional[ParsedDocument] = None
        self._lock = asyncio.Lock()
        self._is_syncing = False
        self._last_error: Optional[str] = None

    async def get(self) -> Optional[ParsedDocument]:
        async with self._lock:
            # Check TTL
            if self._document:
                age = (datetime.now(timezone.utc) - self._document.fetched_at).total_seconds()
                if age > settings.DOCUMENT_CACHE_TTL_SECONDS:
                    return None
            return self._document

    async def set(self, document: ParsedDocument):
        async with self._lock:
            self._document = document
            self._last_error = None
            self._is_syncing = False

    async def set_error(self, error: str):
        async with self._lock:
            self._last_error = error
            self._is_syncing = False

    async def set_syncing(self, status: bool):
        async with self._lock:
            self._is_syncing = status

    @property
    def is_syncing(self) -> bool:
        return self._is_syncing

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

document_cache = DocumentCache()
