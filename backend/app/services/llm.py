import asyncio
import json
from groq import AsyncGroq, APIStatusError
from app.core.config import settings
from app.core.exceptions import LLMServiceError

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def generate_answer(self, system_prompt: str, messages: list[dict]) -> str:
        api_messages = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            return await self._call_groq_with_retry(api_messages)
        except Exception as e:
            raise LLMServiceError(f"The assistant is temporarily unavailable. Details: {e}")

    async def _call_groq_with_retry(self, messages: list[dict], retries: int = 1) -> str:
        for attempt in range(retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    messages=messages,
                    model=settings.MODEL_NAME,
                    temperature=0.1, # Low temp for factual grounding
                    max_tokens=1500,
                )
                return response.choices[0].message.content
            except APIStatusError as e:
                if e.status_code == 429 and attempt < retries:
                    # Very simple backoff based on 429 status
                    retry_after = e.response.headers.get("retry-after", "2")
                    try:
                        wait_time = float(retry_after)
                    except ValueError:
                        wait_time = 2.0
                    await asyncio.sleep(wait_time)
                    continue
                raise e

llm_service = LLMService()
