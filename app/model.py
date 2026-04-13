from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatHistory(BaseModel):
    session_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)