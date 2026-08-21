from pydantic import BaseModel

class ContextConfig(BaseModel):
    context_id: str
    name: str
    instructions: str
