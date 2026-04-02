"""Pydantic models for microblog messages."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SortField(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class MessageCreate(BaseModel):
    author_first_name: str = Field(..., min_length=1, max_length=120)
    author_last_name: str = Field(..., min_length=1, max_length=120)
    author_email: EmailStr
    text: str = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class MessageUpdate(BaseModel):
    author_first_name: str | None = Field(default=None, min_length=1, max_length=120)
    author_last_name: str | None = Field(default=None, min_length=1, max_length=120)
    author_email: EmailStr | None = None
    text: str | None = Field(default=None, min_length=1, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator(
        "author_first_name",
        "author_last_name",
        "author_email",
        "text",
        mode="before",
    )
    @classmethod
    def empty_means_omit(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            return None
        return v


class MessagePublic(BaseModel):
    id: str
    author_first_name: str
    author_last_name: str
    author_email: EmailStr
    text: str = Field(..., max_length=255)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    items: list[MessagePublic]
    total: int
    skip: int
    limit: int
