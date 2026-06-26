from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.finance import FinancialAccount, Transaction, TransactionType, TransactionCategory
from app.schemas.finance import (
    FinancialAccountCreate, FinancialAccountUpdate, FinancialAccountResponse,
    TransactionCreate, TransactionUpdate, TransactionResponse, TransactionListResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter()


# ── ACCOUNTS ──
@router.post("/accounts", response_model=FinancialAccountResponse, status_code=201)
async def create_account(data: FinancialAccountCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    acc = FinancialAccount(user_id=current_user.id, **data.model_dump())
    db.add(acc); db.commit(); db.refresh(acc)
    return acc


@router.get("/accounts", response_model=List[FinancialAccountResponse])
async def list_accounts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FinancialAccount).filter(FinancialAccount.user_id == current_user.id).order_by(desc(FinancialAccount.created_at)).all()


@router.get("/accounts/{account_id}", response_model=FinancialAccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    acc = db.query(FinancialAccount).filter(FinancialAccount.id == account_id, FinancialAccount.user_id == current_user.id).first()
    if not acc: raise HTTPException(404, "Account not found")
    return acc


@router.put("/accounts/{account_id}", response_model=FinancialAccountResponse)
async def update_account(account_id: int, data: FinancialAccountUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    acc = db.query(FinancialAccount).filter(FinancialAccount.id == account_id, FinancialAccount.user_id == current_user.id).first()
    if not acc: raise HTTPException(404, "Account not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(acc, field, value)
    db.commit(); db.refresh(acc)
    return acc


@router.delete("/accounts/{account_id}", status_code=204)
async def delete_account(account_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    acc = db.query(FinancialAccount).filter(FinancialAccount.id == account_id, FinancialAccount.user_id == current_user.id).first()
    if not acc: raise HTTPException(404, "Account not found")
    db.delete(acc); db.commit()
    return None


# ── TRANSACTIONS ──
@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify account ownership
    acc = db.query(FinancialAccount).filter(FinancialAccount.id == data.account_id, FinancialAccount.user_id == current_user.id).first()
    if not acc: raise HTTPException(404, "Account not found")
    
    txn = Transaction(user_id=current_user.id, **data.model_dump())
    db.add(txn)
    
    # Update account balance
    if data.transaction_type == TransactionType.INCOME:
        acc.balance += data.amount
    elif data.transaction_type == TransactionType.EXPENSE:
        acc.balance -= data.amount
    
    db.commit(); db.refresh(txn)
    return txn


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    account_id: Optional[int] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    category: Optional[TransactionCategory] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if account_id: query = query.filter(Transaction.account_id == account_id)
    if transaction_type: query = query.filter(Transaction.transaction_type == transaction_type)
    if category: query = query.filter(Transaction.category == category)
    if start_date: query = query.filter(Transaction.transaction_date >= start_date)
    if end_date: query = query.filter(Transaction.transaction_date <= end_date)
    query = query.order_by(desc(Transaction.transaction_date))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return TransactionListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)


@router.get("/transactions/{txn_id}", response_model=TransactionResponse)
async def get_transaction(txn_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn: raise HTTPException(404, "Transaction not found")
    return txn


@router.put("/transactions/{txn_id}", response_model=TransactionResponse)
async def update_transaction(txn_id: int, data: TransactionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn: raise HTTPException(404, "Transaction not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    db.commit(); db.refresh(txn)
    return txn


@router.delete("/transactions/{txn_id}", status_code=204)
async def delete_transaction(txn_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    txn = db.query(Transaction).filter(Transaction.id == txn_id, Transaction.user_id == current_user.id).first()
    if not txn: raise HTTPException(404, "Transaction not found")
    db.delete(txn); db.commit()
    return None


@router.get("/summary")
async def get_finance_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get overall finance summary."""
    accounts = db.query(FinancialAccount).filter(FinancialAccount.user_id == current_user.id, FinancialAccount.include_in_total == True).all()
    total_balance = sum(a.balance for a in accounts)
    
    income = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == current_user.id, Transaction.transaction_type == TransactionType.INCOME).scalar() or 0
    expenses = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == current_user.id, Transaction.transaction_type == TransactionType.EXPENSE).scalar() or 0
    
    return {
        "total_balance": total_balance,
        "total_income": income,
        "total_expenses": expenses,
        "net": income - expenses,
        "account_count": len(accounts),
    }