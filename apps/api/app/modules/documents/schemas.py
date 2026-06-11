import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: Literal["text", "markdown"]


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
