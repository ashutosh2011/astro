"""Pydantic schemas for chat endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Schema for sending a chat message."""
    profile_id: int
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    """Schema for a chat message response."""
    message_id: int
    role: str
    content: str
    llm_model: Optional[str] = None
    created_at: str


class ChatHistoryItem(BaseModel):
    """Schema for a chat history item."""
    id: int
    role: str
    content: str
    created_at: str


class ChatHistoryResponse(BaseModel):
    """Schema for chat history response."""
    messages: List[ChatHistoryItem]
    total: int


