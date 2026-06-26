"""Notes API."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=NoteResponse, status_code=201, summary="Create note")
async def create_note(
    data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_note = Note(user_id=current_user.id, **data.model_dump())
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@router.get("/", response_model=NoteListResponse, summary="List notes")
async def list_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    folder: Optional[str] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(False),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Note).filter(Note.user_id == current_user.id)

    if folder:
        query = query.filter(Note.folder == folder)
    if is_pinned is not None:
        query = query.filter(Note.is_pinned == is_pinned)
    if is_favorite is not None:
        query = query.filter(Note.is_favorite == is_favorite)
    if is_archived is not None:
        query = query.filter(Note.is_archived == is_archived)
    if search:
        query = query.filter(or_(
            Note.title.ilike(f"%{search}%"),
            Note.content.ilike(f"%{search}%"),
        ))

    # Pinned first, then by updated
    query = query.order_by(desc(Note.is_pinned), desc(Note.updated_at))

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return NoteListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )


@router.get("/{note_id}", response_model=NoteResponse, summary="Get note")
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(
        Note.id == note_id, Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=NoteResponse, summary="Update note")
async def update_note(
    note_id: int,
    data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(
        Note.id == note_id, Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


@router.post("/{note_id}/pin", response_model=NoteResponse, summary="Toggle pin")
async def toggle_pin(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(
        Note.id == note_id, Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.is_pinned = not note.is_pinned
    db.commit()
    db.refresh(note)
    return note


@router.post("/{note_id}/favorite", response_model=NoteResponse, summary="Toggle favorite")
async def toggle_favorite(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(
        Note.id == note_id, Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.is_favorite = not note.is_favorite
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204, summary="Delete note")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Note).filter(
        Note.id == note_id, Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return None