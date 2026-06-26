from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.health import MetricType


class HealthLogBase(BaseModel):
    metric_type: MetricType
    log_date: date
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class HealthLogCreate(HealthLogBase):
    pass


class HealthLogUpdate(BaseModel):
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class HealthLogResponse(HealthLogBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class HealthLogListResponse(BaseModel):
    items: List[HealthLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool