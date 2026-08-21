import time
import asyncio
from typing import Optional

class ConversationMemory:
    def __init__(self, ttl_seconds: int = 7200, max_turns: int = 6):
        self.ttl_seconds = ttl_seconds
        self.max_turns = max_turns
        self.memory = {}
        self._lock = asyncio.Lock()

    async def _evict_expired(self):
        now = time.time()
        expired = [k for k, v in self.memory.items() if now - v["last_accessed"] > self.ttl_seconds]
        for k in expired:
            del self.memory[k]

    async def get_history(self, conversation_id: str) -> list[dict]:
        async with self._lock:
            await self._evict_expired()
            if conversation_id in self.memory:
                self.memory[conversation_id]["last_accessed"] = time.time()
                return self.memory[conversation_id]["messages"]
            return []

    async def add_turn(self, conversation_id: str, user_message: str, assistant_message: str):
        async with self._lock:
            await self._evict_expired()
            if conversation_id not in self.memory:
                self.memory[conversation_id] = {
                    "last_accessed": time.time(),
                    "messages": []
                }
            
            history = self.memory[conversation_id]["messages"]
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": assistant_message})
            
            # Enforce max turns (each turn is 2 messages: user + assistant)
            max_messages = self.max_turns * 2
            if len(history) > max_messages:
                self.memory[conversation_id]["messages"] = history[-max_messages:]
                
            self.memory[conversation_id]["last_accessed"] = time.time()

conversation_memory = ConversationMemory()
