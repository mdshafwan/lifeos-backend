"""Pydantic schemas for Notes."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.note import NoteColor


class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    content: str = Field(default='')
    folder: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    color: NoteColor = NoteColor.DEFAULT
    is_pinned: bool = False
    is_favorite: bool = False
    is_archived: bool = False
    attachments: List[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    color: Optional[NoteColor] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    attachments: Optional[List[str]] = None


class NoteResponse(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteListResponse(BaseModel):
    items: List[NoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool