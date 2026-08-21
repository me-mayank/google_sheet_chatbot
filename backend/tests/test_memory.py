import pytest
import asyncio
from app.core.memory import ConversationMemory

@pytest.mark.asyncio
async def test_conversation_memory_add_and_get():
    memory = ConversationMemory(max_turns=2)
    conv_id = "test_conv_1"
    
    await memory.add_turn(conv_id, "Hello", "Hi there")
    history = await memory.get_history(conv_id)
    
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there"

@pytest.mark.asyncio
async def test_conversation_memory_truncation():
    memory = ConversationMemory(max_turns=2) # 2 turns = 4 messages max
    conv_id = "test_conv_2"
    
    await memory.add_turn(conv_id, "Q1", "A1")
    await memory.add_turn(conv_id, "Q2", "A2")
    await memory.add_turn(conv_id, "Q3", "A3")
    
    history = await memory.get_history(conv_id)
    
    assert len(history) == 4
    # The oldest (Q1, A1) should be evicted
    assert history[0]["content"] == "Q2"
    assert history[1]["content"] == "A2"
    assert history[2]["content"] == "Q3"
    assert history[3]["content"] == "A3"

@pytest.mark.asyncio
async def test_conversation_memory_ttl():
    memory = ConversationMemory(ttl_seconds=0.1)
    conv_id = "test_conv_3"
    
    await memory.add_turn(conv_id, "Q", "A")
    await asyncio.sleep(0.2) # Wait for TTL to expire
    
    history = await memory.get_history(conv_id)
    assert len(history) == 0
