from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class VisionBoardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    affirmation: Optional[str] = None
    image_url: Optional[str] = None
    color: str = "#e879f9"

    # Type & display (plain strings now)
    item_type: str = "image"
    size: str = "medium"

    # Categorization
    category: str = "other"
    tags: List[str] = Field(default_factory=list)

    # Dates
    target_date: Optional[date] = None

    # Position
    position_x: int = 0
    position_y: int = 0
    order_index: int = 0

    # Flags
    is_favorite: bool = False

    # Letter-specific
    mood: Optional[str] = None
    delivery_date: Optional[date] = None
    is_sealed: bool = False

    # Goal-specific
    progress: int = Field(default=0, ge=0, le=100)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)

    # Image-specific
    image_source: Optional[str] = None


class VisionBoardCreate(VisionBoardBase):
    pass


class VisionBoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    affirmation: Optional[str] = None
    image_url: Optional[str] = None
    color: Optional[str] = None
    item_type: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    target_date: Optional[date] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    order_index: Optional[int] = None
    is_favorite: Optional[bool] = None
    is_achieved: Optional[bool] = None
    is_archived: Optional[bool] = None
    mood: Optional[str] = None
    delivery_date: Optional[date] = None
    is_sealed: Optional[bool] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    milestones: Optional[List[Dict[str, Any]]] = None
    image_source: Optional[str] = None


class VisionBoardResponse(VisionBoardBase):
    id: int
    user_id: int
    is_achieved: bool
    achieved_at: Optional[date] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VisionBoardListResponse(BaseModel):
    items: List[VisionBoardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool