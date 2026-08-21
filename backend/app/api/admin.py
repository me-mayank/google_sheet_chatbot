from fastapi import APIRouter
from app.services.context_loader import context_loader

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/context/reload")
def reload_contexts():
    # In the future, require X-Admin-Token header for this endpoint.
    context_loader.load_contexts()
    return {"message": f"Successfully reloaded {len(context_loader.contexts)} contexts."}
