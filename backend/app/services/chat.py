import re
import json
import uuid
from app.schemas.chat import ChatRequest, ChatResponse, SourceRef
from app.services.context_loader import context_loader
from app.core.cache import document_cache
from app.core.memory import conversation_memory
from app.services.llm import llm_service
from app.core.config import settings
from app.core.exceptions import EmptyDocumentError, DocumentUnavailableError

GROUNDING_RULES = """
GROUNDING RULES:
1. Answer ONLY using the supplied documentation.
2. Do not invent events, results, people, dates, or statistics.
3. If information is unavailable, explicitly say so (e.g. "I couldn't find...").
4. Distinguish between documented facts and reasonable interpretation.
5. Do not present assumptions as facts.

Your answer must end with a machine-parseable sources block in the following JSON format:
<sources>
[{"date": "YYYY-MM-DD", "section": "Section Name"}]
</sources>
If you did not use any sources, output an empty list:
<sources>
[]
</sources>
"""

async def process_chat_request(request: ChatRequest) -> ChatResponse:
    context_id = request.context_id or settings.DEFAULT_CONTEXT_ID
    context_config = context_loader.get_context(context_id)
    
    if not context_config:
        # Fallback to default if somehow missing
        context_config = context_loader.get_context(settings.DEFAULT_CONTEXT_ID)
        
    doc = await document_cache.get()
    if not doc:
        # Check if we never synced
        if not document_cache.last_error:
            raise DocumentUnavailableError("Document not synced yet.")
        raise EmptyDocumentError("No usable ICPC information was found in the document.")

    # Format document
    doc_text = []
    if doc.current_status:
        doc_text.append("Current Status:")
        for k, v in doc.current_status.items():
            doc_text.append(f"{k}: {v}")
        doc_text.append("")

    for day in doc.day_sections:
        doc_text.append(f"## {day.raw_date_label} ({day.date.isoformat()})")
        for sub in day.subsections:
            doc_text.append(f"### {sub.title}")
            doc_text.append(sub.content)
            doc_text.append("")

    doc_str = "\n".join(doc_text)

    system_prompt = f"""{context_config.instructions}

{GROUNDING_RULES}

--- DOCUMENT CONTENT ---
{doc_str}
------------------------
"""
    
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    # Load history
    history = await conversation_memory.get_history(conv_id)
    messages = history + [{"role": "user", "content": request.question}]
    
    raw_answer = await llm_service.generate_answer(system_prompt, messages)
    
    # Parse sources
    sources = []
    clean_answer = raw_answer
    
    sources_match = re.search(r"<sources>\s*(\[.*?\])\s*</sources>", raw_answer, re.DOTALL)
    if sources_match:
        try:
            sources_list = json.loads(sources_match.group(1))
            for s in sources_list:
                sources.append(SourceRef(date=s.get("date", ""), section=s.get("section", "")))
        except json.JSONDecodeError:
            pass # Gracefully ignore if LLM output invalid JSON
        
        # Remove the sources block from the clean answer
        clean_answer = re.sub(r"<sources>.*?</sources>", "", raw_answer, flags=re.DOTALL).strip()

    # Save to history
    await conversation_memory.add_turn(conv_id, request.question, clean_answer)

    return ChatResponse(
        answer=clean_answer,
        sources=sources,
        conversation_id=conv_id
    )
