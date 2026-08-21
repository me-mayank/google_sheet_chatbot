import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.cache import document_cache
from app.schemas.chat import ChatRequest
from unittest.mock import patch, AsyncMock
from app.core.exceptions import DocumentUnavailableError, LLMServiceError, EmptyDocumentError
from app.models.document import ParsedDocument
from datetime import datetime, timezone

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture
def mock_document():
    return ParsedDocument(
        current_status=None,
        day_sections=[],
        fetched_at=datetime.now(timezone.utc),
        content_hash="hash",
        token_estimate=10
    )

@pytest.mark.asyncio
async def test_document_unavailable_error():
    # Simulate doc fetch throwing DocumentUnavailableError
    with patch('app.services.chat.document_cache.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        # We need to simulate the state where we haven't synced but have no doc
        document_cache._last_error = None
        
        response = client.post("/api/chat", json={"question": "Test?"})
        assert response.status_code == 503
        assert response.json()["detail"] == "Unable to access the source document. Please check the document's public access settings."

@pytest.mark.asyncio
async def test_empty_document_error():
    # Simulate doc fetch throwing EmptyDocumentError
    with patch('app.services.chat.document_cache.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        # We need to simulate the state where we synced but it resulted in EmptyDocumentError
        document_cache._last_error = "Error"
        
        response = client.post("/api/chat", json={"question": "Test?"})
        assert response.status_code == 200
        assert response.json()["answer"] == "No usable ICPC information was found in the document."

@pytest.mark.asyncio
async def test_llm_service_error(mock_document):
    with patch('app.services.chat.document_cache.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_document
        
        with patch('app.services.chat.llm_service.generate_answer', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = LLMServiceError("Mocked LLM Error")
            
            response = client.post("/api/chat", json={"question": "Test?"})
            assert response.status_code == 502
            assert response.json()["detail"] == "The assistant is temporarily unavailable. Please try again."

@pytest.mark.asyncio
async def test_unhandled_exception(mock_document):
    with patch('app.services.chat.document_cache.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_document
        
        with patch('app.services.chat.llm_service.generate_answer', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("Unknown Error")
            
            response = client.post("/api/chat", json={"question": "Test?"})
            assert response.status_code == 500
            assert response.json()["detail"] == "Something went wrong. Please try again."

@pytest.mark.asyncio
async def test_rate_limiting():
    # Hit refresh endpoint multiple times. Limit is 1/minute
    res = []
    for _ in range(3):
        res.append(client.post("/api/document/refresh"))
        
    assert any(r.status_code == 429 for r in res)
