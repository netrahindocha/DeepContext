import uuid

from pydantic import BaseModel, Field


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
