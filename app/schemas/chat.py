from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.llm.prompts import DocumentSource, WeatherSource


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User question or weather query")
    conversation_id: int | None = Field(default=None, description="Optional existing conversation ID to continue")

    @field_validator("message")
    @classmethod
    def strip_and_validate_message(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message content cannot be blank or contain only whitespace.")
        return cleaned


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    message_id: int
    answer: str
    confidence: Literal["low", "medium", "high"] = "medium"
    routing_decision: str
    location: str | None = None
    weather_sources: list[WeatherSource] = Field(default_factory=list)
    document_sources: list[DocumentSource] = Field(default_factory=list)
    latency_ms: int = 0


class MessageHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    answer: str
    created_at: datetime


class ConversationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    message_count: int


class PaginatedConversations(BaseModel):
    items: list[ConversationListItem]
    total: int
    limit: int
    offset: int


class ConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    title: str
    created_at: datetime
    messages: list[MessageHistoryItem]


class FeedbackCreate(BaseModel):
    message_id: int = Field(..., description="ID of the message being evaluated")
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating from 1 (poor) to 5 (excellent)")
    comments: str | None = Field(default=None, max_length=500, description="Optional user commentary")


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    rating: int
    comments: str | None
    status: str = "recorded"
