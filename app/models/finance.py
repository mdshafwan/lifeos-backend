"""
Financial models:
- FinancialAccount: Bank accounts, cash, credit cards, investments
- Transaction: Income/expense entries with categories
"""

from sqlalchemy import Column, String, Text, Integer, Float, Date, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    LOAN = "loan"
    CRYPTO = "crypto"
    OTHER = "other"


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    INVESTMENT = "investment"


class TransactionCategory(str, enum.Enum):
    # Income
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    INVESTMENT_RETURN = "investment_return"
    GIFT = "gift"
    REFUND = "refund"

    # Expenses
    FOOD = "food"
    GROCERIES = "groceries"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SUBSCRIPTIONS = "subscriptions"
    INSURANCE = "insurance"
    TRAVEL = "travel"
    PERSONAL_CARE = "personal_care"
    SAVINGS = "savings"
    DEBT_PAYMENT = "debt_payment"
    TAXES = "taxes"
    CHARITY = "charity"
    OTHER = "other"


class FinancialAccount(BaseModel):
    __tablename__ = "financial_accounts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    name = Column(String(200), nullable=False)
    account_type = Column(Enum(AccountType), default=AccountType.CHECKING, nullable=False)
    institution = Column(String(200), nullable=True)

    # ── Balance ───────────────────────────────────────
    balance = Column(Float, default=0, nullable=False)
    initial_balance = Column(Float, default=0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ── Credit-specific ───────────────────────────────
    credit_limit = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)

    # ── Visual ────────────────────────────────────────
    color = Column(String(20), default="#10b981", nullable=False)
    icon = Column(String(50), nullable=True)

    # ── Flags ─────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    include_in_total = Column(Boolean, default=True, nullable=False)

    # ── Notes ─────────────────────────────────────────
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="financial_accounts")
    
    # 🔧 FIX: Specify foreign_keys explicitly because Transaction has TWO FKs to this table
    transactions = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="[Transaction.account_id]",   # ← Use this FK, not transfer_account_id
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<FinancialAccount(id={self.id}, name='{self.name}', balance={self.balance})>"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("financial_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    category = Column(Enum(TransactionCategory), default=TransactionCategory.OTHER, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # ── Details ───────────────────────────────────────
    description = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)
    merchant = Column(String(200), nullable=True)

    # ── Date ──────────────────────────────────────────
    transaction_date = Column(Date, nullable=False, index=True)

    # ── Tags ──────────────────────────────────────────
    tags = Column(JSON, default=list, nullable=False)

    # ── Recurring ─────────────────────────────────────
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(String(50), nullable=True)

    # ── Receipt ───────────────────────────────────────
    receipt_url = Column(String(500), nullable=True)

    # ── Transfer-specific (links to the "other side") ─
    transfer_account_id = Column(Integer, ForeignKey("financial_accounts.id", ondelete="SET NULL"), nullable=True)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="transactions")
    
    # 🔧 FIX: Specify which foreign_key this relationship uses
    account = relationship(
        "FinancialAccount",
        back_populates="transactions",
        foreign_keys=[account_id]   # ← Explicitly use account_id, not transfer_account_id
    )
    
    # Optional: relationship for the transfer destination account
    transfer_account = relationship(
        "FinancialAccount",
        foreign_keys=[transfer_account_id],
        post_update=True  # Avoid circular dependency issues
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', amount={self.amount})>"