"""
Business module models — Business ventures, Clients, Invoices, Expenses.

Contains 4 models:
- Business         → existing model for tracking business ventures
- Client           → freelance clients
- Invoice          → invoicing with line items
- BusinessExpense  → tax-deductible business expenses
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, Date, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


# ══════════════════════════════════════════════
#  ENUMS
# ══════════════════════════════════════════════

class BusinessStage(str, enum.Enum):
    IDEA = "idea"
    PLANNING = "planning"
    LAUNCHING = "launching"
    OPERATING = "operating"
    SCALING = "scaling"
    EXITING = "exiting"
    CLOSED = "closed"


class BusinessType(str, enum.Enum):
    STARTUP = "startup"
    FREELANCE = "freelance"
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    CONSULTING = "consulting"
    AGENCY = "agency"
    CONTENT = "content"
    OTHER = "other"


# ══════════════════════════════════════════════
#  BUSINESS MODEL (existing - unchanged)
# ══════════════════════════════════════════════

class Business(BaseModel):
    __tablename__ = "businesses"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core ──
    name = Column(String(300), nullable=False)
    tagline = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)

    # ── Categorization ──
    business_type = Column(Enum(BusinessType), default=BusinessType.STARTUP, nullable=False)
    stage = Column(Enum(BusinessStage), default=BusinessStage.IDEA, nullable=False)

    # ── Financial Metrics ──
    revenue = Column(Float, default=0, nullable=False)
    expenses = Column(Float, default=0, nullable=False)
    profit = Column(Float, default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ── Growth Metrics ──
    customers = Column(Integer, default=0, nullable=False)
    employees = Column(Integer, default=0, nullable=False)
    mrr = Column(Float, default=0, nullable=False)

    # ── Goals & Strategy ──
    vision = Column(Text, nullable=True)
    mission = Column(Text, nullable=True)
    target_market = Column(Text, nullable=True)
    key_metrics = Column(JSON, default=dict, nullable=False)

    # ── Dates ──
    founded_date = Column(Date, nullable=True)

    # ── Tags ──
    tags = Column(JSON, default=list, nullable=False)

    # ── Flags ──
    is_active = Column(Boolean, default=True, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)

    # ── Relationships ──
    user = relationship("User", backref="businesses")

    def __repr__(self):
        return f"<Business(id={self.id}, name='{self.name}', stage='{self.stage}')>"


# ══════════════════════════════════════════════
#  CLIENT MODEL (NEW)
# ══════════════════════════════════════════════

class Client(BaseModel):
    __tablename__ = "clients"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core ──
    name = Column(String(200), nullable=False)
    company = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)

    # ── Status (string to avoid PG enum hell) ──
    status = Column(String(20), default="lead", nullable=False, index=True)
    # values: active, inactive, lead, archived

    # ── Billing ──
    hourly_rate = Column(Float, nullable=True)

    # ── Display ──
    color = Column(String(20), default="#6366f1", nullable=False)

    # ── Categorization ──
    tags = Column(JSON, default=list, nullable=False)

    # ── Notes ──
    notes = Column(Text, nullable=True)

    # ── Relationships ──
    user = relationship("User", backref="clients")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', status='{self.status}')>"


# ══════════════════════════════════════════════
#  INVOICE MODEL (NEW)
# ══════════════════════════════════════════════

class Invoice(BaseModel):
    __tablename__ = "invoices"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core ──
    number = Column(String(50), nullable=False, index=True)  # INV-001
    status = Column(String(20), default="draft", nullable=False, index=True)
    # values: draft, sent, paid, overdue, cancelled

    # ── Dates ──
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_at = Column(Date, nullable=True)

    # ── Line Items (stored as JSON array) ──
    # [{id, description, quantity, rate}]
    items = Column(JSON, default=list, nullable=False)

    # ── Money ──
    tax_rate = Column(Float, default=0, nullable=False)  # percentage
    subtotal = Column(Float, default=0, nullable=False)
    tax_amount = Column(Float, default=0, nullable=False)
    total = Column(Float, default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ── Notes ──
    notes = Column(Text, nullable=True)

    # ── Relationships ──
    user = relationship("User", backref="invoices")
    client = relationship("Client", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.number}', total={self.total})>"


# ══════════════════════════════════════════════
#  BUSINESS EXPENSE MODEL (NEW)
# ══════════════════════════════════════════════

class BusinessExpense(BaseModel):
    __tablename__ = "business_expenses"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core ──
    description = Column(String(300), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ── Category (string, not enum) ──
    category = Column(String(50), default="other", nullable=False, index=True)
    # values: software, marketing, office, travel, contractor, other

    # ── Details ──
    vendor = Column(String(200), nullable=True)
    date = Column(Date, nullable=False, index=True)
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # ── Flags ──
    is_tax_deductible = Column(Boolean, default=True, nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)

    # ── Relationships ──
    user = relationship("User", backref="business_expenses")

    def __repr__(self):
        return f"<BusinessExpense(id={self.id}, desc='{self.description}', amount={self.amount})>"