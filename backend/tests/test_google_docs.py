import pytest
import respx
import httpx
from app.services.google_docs import fetch_google_doc_text
from app.core.exceptions import DocumentUnavailableError, EmptyDocumentError

@pytest.mark.asyncio
@respx.mock
async def test_fetch_google_doc_text_success():
    url = "https://docs.google.com/document/d/12345ABCDE/edit"
    mock_url = "https://docs.google.com/document/d/12345ABCDE/export?format=txt"
    respx.get(mock_url).mock(return_value=httpx.Response(200, text="Some content"))
    
    result = await fetch_google_doc_text(url)
    assert result == "Some content"

@pytest.mark.asyncio
async def test_fetch_google_doc_text_invalid_url():
    url = "https://example.com/not-a-google-doc"
    with pytest.raises(DocumentUnavailableError, match="Invalid Google Docs URL format."):
        await fetch_google_doc_text(url)

@pytest.mark.asyncio
@respx.mock
async def test_fetch_google_doc_text_private_doc():
    url = "https://docs.google.com/document/d/12345ABCDE/edit"
    mock_url = "https://docs.google.com/document/d/12345ABCDE/export?format=txt"
    respx.get(mock_url).mock(return_value=httpx.Response(403))
    
    with pytest.raises(DocumentUnavailableError, match="Unable to access the source document"):
        await fetch_google_doc_text(url)

@pytest.mark.asyncio
@respx.mock
async def test_fetch_google_doc_text_empty_doc():
    url = "https://docs.google.com/document/d/12345ABCDE/edit"
    mock_url = "https://docs.google.com/document/d/12345ABCDE/export?format=txt"
    respx.get(mock_url).mock(return_value=httpx.Response(200, text="   \n   "))
    
    with pytest.raises(EmptyDocumentError, match="No usable ICPC information"):
        await fetch_google_doc_text(url)

@pytest.mark.asyncio
@respx.mock
async def test_fetch_google_doc_text_network_error():
    url = "https://docs.google.com/document/d/12345ABCDE/edit"
    mock_url = "https://docs.google.com/document/d/12345ABCDE/export?format=txt"
    respx.get(mock_url).mock(side_effect=httpx.ConnectError("Connection failed"))
    
    with pytest.raises(DocumentUnavailableError, match="Network error while fetching document"):
        await fetch_google_doc_text(url)
