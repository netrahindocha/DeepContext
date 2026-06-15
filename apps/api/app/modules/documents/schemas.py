import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: Literal["text", "markdown"]
    content: str = Field(min_length=1, max_length=100_000)


class DocumentRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    source_type: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")


class SourceElementListRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    owner_id: uuid.UUID
    element_index: int
    modality: str
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceElementRead(SourceElementListRead):
    raw_content_text: str


class WorkspaceSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    limit: int = Field(default=5, ge=1, le=20)


class WorkspaceSearchResult(BaseModel):
    source_element_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    summary_text: str
    distance: float


class WorkspaceSearchResponse(BaseModel):
    results: list[WorkspaceSearchResult]
