from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.document import DocumentCategory


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    file_url: str
    file_path: str
    file_size: int
    file_type: str
    file_extension: Optional[str] = None
    category: DocumentCategory
    folder: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_encrypted: bool
    is_confidential: bool
    expiry_date: Optional[str] = None
    is_favorite: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    is_confidential: Optional[bool] = None
    is_favorite: Optional[bool] = None