"""
Contacts module routers — Contact + Interaction.

This file exposes 2 sub-routers under different prefixes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional
from datetime import date as date_type
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.contact import Contact, Interaction, ContactCategory
from app.schemas.contact import (
    # Contact
    ContactCreate, ContactUpdate, ContactResponse, ContactListResponse,
    # Interaction
    InteractionCreate, InteractionUpdate, InteractionResponse, InteractionListResponse,
)
from app.core.dependencies import get_current_user


# ══════════════════════════════════════════════
#  CONTACT ROUTER (existing — improved)
# ══════════════════════════════════════════════

router = APIRouter()  # main contacts router


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = Contact(user_id=current_user.id, **data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    category: Optional[ContactCategory] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Contact).filter(Contact.user_id == current_user.id)

    if category:
        query = query.filter(Contact.category == category)
    if is_favorite is not None:
        query = query.filter(Contact.is_favorite == is_favorite)
    if search:
        query = query.filter(or_(
            Contact.first_name.ilike(f"%{search}%"),
            Contact.last_name.ilike(f"%{search}%"),
            Contact.email.ilike(f"%{search}%"),
            Contact.company.ilike(f"%{search}%"),
        ))

    query = query.order_by(desc(Contact.is_favorite), Contact.first_name)
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ContactListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id,
    ).first()
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id,
    ).first()
    if not contact:
        raise HTTPException(404, "Contact not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.user_id == current_user.id,
    ).first()
    if not contact:
        raise HTTPException(404, "Contact not found")
    db.delete(contact)
    db.commit()
    return None


# ══════════════════════════════════════════════
#  INTERACTION ROUTER (NEW)
# ══════════════════════════════════════════════

interactions_router = APIRouter()


@interactions_router.post("/", response_model=InteractionResponse, status_code=201)
async def create_interaction(
    data: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify contact belongs to user
    contact = db.query(Contact).filter(
        Contact.id == data.contact_id,
        Contact.user_id == current_user.id,
    ).first()
    if not contact:
        raise HTTPException(400, "Contact not found or doesn't belong to you")

    interaction = Interaction(user_id=current_user.id, **data.model_dump())
    db.add(interaction)

    # Auto-update contact's last_contacted date
    if not contact.last_contacted or data.date > contact.last_contacted:
        contact.last_contacted = data.date

    db.commit()
    db.refresh(interaction)
    return interaction


@interactions_router.get("/", response_model=InteractionListResponse)
async def list_interactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
    contact_id: Optional[int] = Query(None),
    interaction_type: Optional[str] = Query(None),
    start_date: Optional[date_type] = Query(None),
    end_date: Optional[date_type] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Interaction).filter(Interaction.user_id == current_user.id)

    if contact_id:
        query = query.filter(Interaction.contact_id == contact_id)
    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type)
    if start_date:
        query = query.filter(Interaction.date >= start_date)
    if end_date:
        query = query.filter(Interaction.date <= end_date)

    query = query.order_by(desc(Interaction.date), desc(Interaction.created_at))

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return InteractionListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@interactions_router.get("/{interaction_id}", response_model=InteractionResponse)
async def get_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interaction = db.query(Interaction).filter(
        Interaction.id == interaction_id,
        Interaction.user_id == current_user.id,
    ).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return interaction


@interactions_router.put("/{interaction_id}", response_model=InteractionResponse)
async def update_interaction(
    interaction_id: int,
    data: InteractionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interaction = db.query(Interaction).filter(
        Interaction.id == interaction_id,
        Interaction.user_id == current_user.id,
    ).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


@interactions_router.delete("/{interaction_id}", status_code=204)
async def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interaction = db.query(Interaction).filter(
        Interaction.id == interaction_id,
        Interaction.user_id == current_user.id,
    ).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    db.delete(interaction)
    db.commit()
    return None