import uuid

from pydantic import BaseModel, ConfigDict, Field

from datetime import datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
    limit: int = Field(default=5, ge=1, le=20)


class ChatCitation(BaseModel):
    source_element_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]


class ChatSessionRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCitationRead(BaseModel):
    source_element_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    citation_index: int
    snippet: str

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID
    role: str
    content: str
    message_index: int
    created_at: datetime
    citations: list[ChatMessageCitationRead]
