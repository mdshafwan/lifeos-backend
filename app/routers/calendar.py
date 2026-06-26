from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc
from typing import Optional
from datetime import datetime
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.calendar_event import CalendarEvent, EventType
from app.schemas.calendar_event import (
    CalendarEventCreate, CalendarEventUpdate,
    CalendarEventResponse, CalendarEventListResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=CalendarEventResponse, status_code=201)
async def create_event(data: CalendarEventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = CalendarEvent(user_id=current_user.id, **data.model_dump())
    db.add(event); db.commit(); db.refresh(event)
    return event


@router.get("/", response_model=CalendarEventListResponse)
async def list_events(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    event_type: Optional[EventType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)
    if event_type: query = query.filter(CalendarEvent.event_type == event_type)
    if start_date: query = query.filter(CalendarEvent.start_time >= start_date)
    if end_date: query = query.filter(CalendarEvent.start_time <= end_date)
    query = query.order_by(asc(CalendarEvent.start_time))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return CalendarEventListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)


@router.get("/{event_id}", response_model=CalendarEventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()
    if not event: raise HTTPException(404, "Event not found")
    return event


@router.put("/{event_id}", response_model=CalendarEventResponse)
async def update_event(event_id: int, data: CalendarEventUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()
    if not event: raise HTTPException(404, "Event not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit(); db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id).first()
    if not event: raise HTTPException(404, "Event not found")
    db.delete(event); db.commit()
    return None