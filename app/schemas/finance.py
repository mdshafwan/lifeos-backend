from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.models.finance import AccountType, TransactionType, TransactionCategory


class FinancialAccountBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    account_type: AccountType = AccountType.CHECKING
    institution: Optional[str] = None
    balance: float = 0
    initial_balance: float = 0
    currency: str = "USD"
    credit_limit: Optional[float] = None
    interest_rate: Optional[float] = None
    color: str = "#10b981"
    icon: Optional[str] = None
    is_active: bool = True
    include_in_total: bool = True
    notes: Optional[str] = None


class FinancialAccountCreate(FinancialAccountBase):
    pass


class FinancialAccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    institution: Optional[str] = None
    balance: Optional[float] = None
    credit_limit: Optional[float] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    include_in_total: Optional[bool] = None
    notes: Optional[str] = None


class FinancialAccountResponse(FinancialAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    account_id: int
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.OTHER
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    description: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = None
    merchant: Optional[str] = None
    transaction_date: date
    tags: List[str] = Field(default_factory=list)
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    transaction_type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    merchant: Optional[str] = None
    transaction_date: Optional[date] = None
    tags: Optional[List[str]] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool