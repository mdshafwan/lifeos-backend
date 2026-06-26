"""
Business module schemas — Business, Client, Invoice, Expense.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from app.models.business import BusinessStage, BusinessType


# ══════════════════════════════════════════════
#  BUSINESS SCHEMAS (existing - unchanged)
# ══════════════════════════════════════════════

class BusinessBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    tagline: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    business_type: BusinessType = BusinessType.STARTUP
    stage: BusinessStage = BusinessStage.IDEA
    revenue: float = 0
    expenses: float = 0
    profit: float = 0
    currency: str = "USD"
    customers: int = 0
    employees: int = 0
    mrr: float = 0
    vision: Optional[str] = None
    mission: Optional[str] = None
    target_market: Optional[str] = None
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    founded_date: Optional[date] = None
    tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_favorite: bool = False


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[BusinessStage] = None
    revenue: Optional[float] = None
    expenses: Optional[float] = None
    customers: Optional[int] = None
    mrr: Optional[float] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None


class BusinessResponse(BusinessBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════
#  CLIENT SCHEMAS (NEW)
# ══════════════════════════════════════════════

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    status: str = "lead"  # active, inactive, lead, archived
    hourly_rate: Optional[float] = None
    color: str = "#6366f1"
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    hourly_rate: Optional[float] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ══════════════════════════════════════════════
#  INVOICE SCHEMAS (NEW)
# ══════════════════════════════════════════════

class InvoiceItem(BaseModel):
    id: str
    description: str = ""
    quantity: float = 1
    rate: float = 0


class InvoiceBase(BaseModel):
    number: str = Field(..., min_length=1, max_length=50)
    client_id: int
    status: str = "draft"  # draft, sent, paid, overdue, cancelled

    issue_date: date
    due_date: date
    paid_at: Optional[date] = None

    items: List[Dict[str, Any]] = Field(default_factory=list)

    tax_rate: float = 0
    subtotal: float = 0
    tax_amount: float = 0
    total: float = 0
    currency: str = "USD"

    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    number: Optional[str] = None
    client_id: Optional[int] = None
    status: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    paid_at: Optional[date] = None
    items: Optional[List[Dict[str, Any]]] = None
    tax_rate: Optional[float] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ══════════════════════════════════════════════
#  BUSINESS EXPENSE SCHEMAS (NEW)
# ══════════════════════════════════════════════

class BusinessExpenseBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=300)
    amount: float = Field(..., ge=0)
    currency: str = "USD"

    category: str = "other"  # software, marketing, office, travel, contractor, other

    vendor: Optional[str] = None
    date: date
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

    is_tax_deductible: bool = True
    is_recurring: bool = False


class BusinessExpenseCreate(BusinessExpenseBase):
    pass


class BusinessExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[date] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    is_tax_deductible: Optional[bool] = None
    is_recurring: Optional[bool] = None


class BusinessExpenseResponse(BusinessExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BusinessExpenseListResponse(BaseModel):
    items: List[BusinessExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool