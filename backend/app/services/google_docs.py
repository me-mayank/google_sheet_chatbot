import re
import httpx
from app.core.exceptions import DocumentUnavailableError, EmptyDocumentError

async def fetch_google_doc_text(url: str) -> str:
    """
    Extracts the document ID from the Google Docs URL and fetches the plain text export.
    """
    match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise DocumentUnavailableError("Invalid Google Docs URL format.")
    
    doc_id = match.group(1)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(export_url, timeout=10.0)
        except httpx.RequestError as e:
            raise DocumentUnavailableError(f"Network error while fetching document: {str(e)}")
            
        if response.status_code in (401, 403, 404):
            raise DocumentUnavailableError("Unable to access the source document. Please check the document's public access settings.")
        
        response.raise_for_status()
        
        text = response.text
        if not text.strip():
            raise EmptyDocumentError("No usable ICPC information was found in the document.")
            
        return text
