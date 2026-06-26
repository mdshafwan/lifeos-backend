"""
Contact module schemas — Contact + Interaction.
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.contact import ContactCategory, RelationshipStrength


# ══════════════════════════════════════════════
#  CONTACT SCHEMAS (existing — unchanged)
# ══════════════════════════════════════════════

class ContactBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    category: ContactCategory = ContactCategory.ACQUAINTANCE
    relationship_strength: RelationshipStrength = RelationshipStrength.MODERATE
    how_we_met: Optional[str] = None
    birthday: Optional[date] = None
    anniversary: Optional[date] = None
    last_contacted: Optional[date] = None
    contact_frequency_days: Optional[int] = None
    next_followup: Optional[date] = None
    notes: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_favorite: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    category: Optional[ContactCategory] = None
    relationship_strength: Optional[RelationshipStrength] = None
    how_we_met: Optional[str] = None
    birthday: Optional[date] = None
    anniversary: Optional[date] = None
    last_contacted: Optional[date] = None
    contact_frequency_days: Optional[int] = None
    next_followup: Optional[date] = None
    notes: Optional[str] = None
    interests: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class ContactResponse(ContactBase):
    id: int
    user_id: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    items: List[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ══════════════════════════════════════════════
#  INTERACTION SCHEMAS (NEW)
# ══════════════════════════════════════════════

class InteractionBase(BaseModel):
    contact_id: int
    interaction_type: str = "note"  # call/message/meeting/email/coffee/video/gift/note/other
    date: date
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None


class InteractionResponse(InteractionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InteractionListResponse(BaseModel):
    items: List[InteractionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool