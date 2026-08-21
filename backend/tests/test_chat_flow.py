import pytest
import datetime
from app.schemas.chat import ChatRequest
from app.services.chat import process_chat_request
from app.models.document import ParsedDocument, DaySection, Subsection
from app.core.cache import document_cache
from app.core.exceptions import EmptyDocumentError, DocumentUnavailableError
from unittest.mock import patch, AsyncMock

@pytest.fixture
def mock_document():
    return ParsedDocument(
        current_status={"Teams": "3"},
        day_sections=[
            DaySection(
                date=datetime.date(2026, 8, 21),
                raw_date_label="21 August 2026",
                subsections=[
                    Subsection(title="Contest", content="Contest #1 completed.")
                ]
            )
        ],
        fetched_at=datetime.datetime.now(datetime.timezone.utc),
        content_hash="hash",
        token_estimate=100
    )

@pytest.mark.asyncio
async def test_process_chat_request_success(mock_document):
    await document_cache.set(mock_document)
    
    mock_llm_response = """This is the answer.
<sources>
[{"date": "2026-08-21", "section": "Contest"}]
</sources>"""
    
    with patch('app.services.chat.llm_service.generate_answer', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_llm_response
        
        request = ChatRequest(question="What happened?")
        response = await process_chat_request(request)
        
        assert response.answer == "This is the answer."
        assert len(response.sources) == 1
        assert response.sources[0].date == "2026-08-21"
        assert response.sources[0].section == "Contest"
        assert response.conversation_id is not None
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_process_chat_request_no_doc():
    await document_cache.set_error("Not found") # Sets error and clears doc if we used a reset, but wait
    # Manually clear document cache for test
    document_cache._document = None
    document_cache._last_error = "Error"
    
    request = ChatRequest(question="What happened?")
    
    with pytest.raises(EmptyDocumentError):
        await process_chat_request(request)
