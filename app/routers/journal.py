"""Journal API."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.journal import JournalEntry, MoodLevel
from app.schemas.journal import JournalCreate, JournalUpdate, JournalResponse, JournalListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=JournalResponse, status_code=201, summary="Create journal entry")
async def create_entry(
    data: JournalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_entry = JournalEntry(user_id=current_user.id, **data.model_dump())
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    
    # 🎮 GAMIFICATION
    from app.services.gamification_service import GamificationService
    from app.config import settings
    service = GamificationService(db, current_user)
    service.award_xp(settings.XP_JOURNAL_ENTRY, "Journal entry written")
    service.check_achievements()
    
    return new_entry


@router.get("/", response_model=JournalListResponse, summary="List journal entries")
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    mood: Optional[MoodLevel] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(JournalEntry).filter(JournalEntry.user_id == current_user.id)

    if mood:
        query = query.filter(JournalEntry.mood == mood)
    if start_date:
        query = query.filter(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(JournalEntry.entry_date <= end_date)
    if is_favorite is not None:
        query = query.filter(JournalEntry.is_favorite == is_favorite)

    query = query.order_by(desc(JournalEntry.entry_date))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return JournalListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{entry_id}", response_model=JournalResponse, summary="Get journal entry")
async def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.put("/{entry_id}", response_model=JournalResponse, summary="Update journal entry")
async def update_entry(
    entry_id: int,
    data: JournalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204, summary="Delete journal entry")
async def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return None