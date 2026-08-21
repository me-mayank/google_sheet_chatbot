from fastapi import APIRouter, BackgroundTasks, Request
from app.schemas.document import DocumentStatusResponse
from app.core.cache import document_cache
from app.core.rate_limit import limiter
from app.core.config import settings
from app.services.google_docs import fetch_google_doc_text
from app.services.document_processor import process_document
from app.core.exceptions import DocumentUnavailableError, EmptyDocumentError

router = APIRouter(prefix="/api/document", tags=["Document"])

@router.get("/status", response_model=DocumentStatusResponse)
async def get_status():
    if document_cache.is_syncing:
        return DocumentStatusResponse(status="syncing")
    
    doc = await document_cache.get()
    
    if doc:
        return DocumentStatusResponse(
            status="synced",
            last_synced_at=doc.fetched_at,
            document_too_large=doc.token_estimate > 40000,
            error=None
        )
    
    error = document_cache.last_error
    if error:
        return DocumentStatusResponse(status="sync_failed", error=error)
        
    return DocumentStatusResponse(status="never_synced")


async def sync_document_task():
    try:
        raw_text = await fetch_google_doc_text(settings.GOOGLE_DOC_URL)
        parsed_doc = process_document(raw_text)
        await document_cache.set(parsed_doc)
    except (DocumentUnavailableError, EmptyDocumentError) as e:
        await document_cache.set_error(str(e))
    except Exception as e:
        await document_cache.set_error("An unexpected error occurred during sync.")
    finally:
        await document_cache.set_syncing(False)


@router.post("/refresh")
@limiter.limit("1/minute")
async def refresh_document(request: Request, background_tasks: BackgroundTasks):
    if document_cache.is_syncing:
        return {"message": "Sync already in progress."}
    
    await document_cache.set_syncing(True)
    background_tasks.add_task(sync_document_task)
    
    return {"message": "Sync started."}
