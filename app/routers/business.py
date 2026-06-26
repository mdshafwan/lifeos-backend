"""
Business module routers — Business, Client, Invoice, Expense.

This file exposes 4 sub-routers under different prefixes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional, List
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.business import Business, Client, Invoice, BusinessExpense
from app.schemas.business import (
    # Business
    BusinessCreate, BusinessUpdate, BusinessResponse,
    # Client
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    # Invoice
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    # Expense
    BusinessExpenseCreate, BusinessExpenseUpdate, BusinessExpenseResponse, BusinessExpenseListResponse,
)
from app.core.dependencies import get_current_user


# ══════════════════════════════════════════════
#  BUSINESS VENTURE ROUTER (existing - kept as-is)
# ══════════════════════════════════════════════

router = APIRouter()  # main business router


@router.post("/", response_model=BusinessResponse, status_code=201)
async def create_business(
    data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    biz = Business(user_id=current_user.id, **data.model_dump())
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


@router.get("/", response_model=List[BusinessResponse])
async def list_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Business).filter(
        Business.user_id == current_user.id
    ).order_by(desc(Business.created_at)).all()


@router.get("/{biz_id}", response_model=BusinessResponse)
async def get_business(
    biz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    biz = db.query(Business).filter(
        Business.id == biz_id,
        Business.user_id == current_user.id,
    ).first()
    if not biz:
        raise HTTPException(404, "Not found")
    return biz


@router.put("/{biz_id}", response_model=BusinessResponse)
async def update_business(
    biz_id: int,
    data: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    biz = db.query(Business).filter(
        Business.id == biz_id,
        Business.user_id == current_user.id,
    ).first()
    if not biz:
        raise HTTPException(404, "Not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(biz, field, value)
    biz.profit = biz.revenue - biz.expenses
    db.commit()
    db.refresh(biz)
    return biz


@router.delete("/{biz_id}", status_code=204)
async def delete_business(
    biz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    biz = db.query(Business).filter(
        Business.id == biz_id,
        Business.user_id == current_user.id,
    ).first()
    if not biz:
        raise HTTPException(404, "Not found")
    db.delete(biz)
    db.commit()
    return None


# ══════════════════════════════════════════════
#  CLIENT ROUTER
# ══════════════════════════════════════════════

clients_router = APIRouter()


@clients_router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(user_id=current_user.id, **data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@clients_router.get("/", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Client).filter(Client.user_id == current_user.id)

    if status:
        query = query.filter(Client.status == status)
    if search:
        from sqlalchemy import or_
        s = f"%{search}%"
        query = query.filter(
            or_(
                Client.name.ilike(s),
                Client.company.ilike(s),
                Client.email.ilike(s),
            )
        )

    query = query.order_by(desc(Client.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ClientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@clients_router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id,
    ).first()
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@clients_router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id,
    ).first()
    if not client:
        raise HTTPException(404, "Client not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@clients_router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id,
    ).first()
    if not client:
        raise HTTPException(404, "Client not found")
    db.delete(client)
    db.commit()
    return None


# ══════════════════════════════════════════════
#  INVOICE ROUTER
# ══════════════════════════════════════════════

invoices_router = APIRouter()


def _calc_invoice_totals(items: list, tax_rate: float) -> dict:
    """Helper to calculate invoice totals from line items."""
    subtotal = sum(
        (item.get("quantity", 0) or 0) * (item.get("rate", 0) or 0)
        for item in items
    )
    tax_amount = subtotal * (tax_rate / 100) if tax_rate else 0
    total = subtotal + tax_amount
    return {"subtotal": subtotal, "tax_amount": tax_amount, "total": total}


@invoices_router.post("/", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.user_id == current_user.id,
    ).first()
    if not client:
        raise HTTPException(400, "Client not found or doesn't belong to you")

    payload = data.model_dump()

    # Auto-calculate totals
    totals = _calc_invoice_totals(payload["items"], payload["tax_rate"])
    payload["subtotal"] = totals["subtotal"]
    payload["tax_amount"] = totals["tax_amount"]
    payload["total"] = totals["total"]

    invoice = Invoice(user_id=current_user.id, **payload)
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@invoices_router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Invoice).filter(Invoice.user_id == current_user.id)

    if status:
        query = query.filter(Invoice.status == status)
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    if search:
        query = query.filter(Invoice.number.ilike(f"%{search}%"))

    query = query.order_by(desc(Invoice.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return InvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@invoices_router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id,
    ).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice


@invoices_router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id,
    ).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    # Verify new client_id if changing
    update_data = data.model_dump(exclude_unset=True)
    if "client_id" in update_data:
        client = db.query(Client).filter(
            Client.id == update_data["client_id"],
            Client.user_id == current_user.id,
        ).first()
        if not client:
            raise HTTPException(400, "Client not found or doesn't belong to you")

    for field, value in update_data.items():
        setattr(invoice, field, value)

    # Recalculate totals if items or tax_rate changed
    if "items" in update_data or "tax_rate" in update_data:
        totals = _calc_invoice_totals(invoice.items, invoice.tax_rate)
        invoice.subtotal = totals["subtotal"]
        invoice.tax_amount = totals["tax_amount"]
        invoice.total = totals["total"]

    # Auto-set paid_at if status changed to paid
    if update_data.get("status") == "paid" and not invoice.paid_at:
        invoice.paid_at = date.today()

    db.commit()
    db.refresh(invoice)
    return invoice


@invoices_router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == current_user.id,
    ).first()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    db.delete(invoice)
    db.commit()
    return None


# ══════════════════════════════════════════════
#  BUSINESS EXPENSE ROUTER
# ══════════════════════════════════════════════

expenses_router = APIRouter()


@expenses_router.post("/", response_model=BusinessExpenseResponse, status_code=201)
async def create_expense(
    data: BusinessExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = BusinessExpense(user_id=current_user.id, **data.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@expenses_router.get("/", response_model=BusinessExpenseListResponse)
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BusinessExpense).filter(
        BusinessExpense.user_id == current_user.id
    )

    if category:
        query = query.filter(BusinessExpense.category == category)
    if start_date:
        query = query.filter(BusinessExpense.date >= start_date)
    if end_date:
        query = query.filter(BusinessExpense.date <= end_date)

    query = query.order_by(desc(BusinessExpense.date))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return BusinessExpenseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@expenses_router.get("/{expense_id}", response_model=BusinessExpenseResponse)
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(BusinessExpense).filter(
        BusinessExpense.id == expense_id,
        BusinessExpense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(404, "Expense not found")
    return expense


@expenses_router.put("/{expense_id}", response_model=BusinessExpenseResponse)
async def update_expense(
    expense_id: int,
    data: BusinessExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(BusinessExpense).filter(
        BusinessExpense.id == expense_id,
        BusinessExpense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(404, "Expense not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@expenses_router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = db.query(BusinessExpense).filter(
        BusinessExpense.id == expense_id,
        BusinessExpense.user_id == current_user.id,
    ).first()
    if not expense:
        raise HTTPException(404, "Expense not found")
    db.delete(expense)
    db.commit()
    return None