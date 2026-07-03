"""API request/response models."""
import json

from pydantic import BaseModel, Field, field_validator

from .message_store import VALID_TYPES


class MessageIn(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    type: str
    title: str = Field(min_length=1, max_length=48)
    message: str | None = Field(default=None, max_length=500)
    pinned: bool = False
    priority: int = Field(default=5, ge=1, le=10)
    category: str | None = Field(default=None, max_length=32)
    metadata: dict | None = None

    @field_validator("type")
    @classmethod
    def _type_ok(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("metadata")
    @classmethod
    def _meta_size(cls, v):
        if v is not None and len(json.dumps(v)) > 4096:
            raise ValueError("metadata exceeds 4096 chars when serialized")
        return v


class TokenIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
