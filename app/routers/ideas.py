from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.idea import Idea, IdeaCategory, IdeaStatus
from app.schemas.idea import IdeaCreate, IdeaUpdate, IdeaResponse, IdeaListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=IdeaResponse, status_code=201)
async def create_idea(data: IdeaCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    idea_data = data.model_dump()
    # Auto-calc priority score (impact/effort * 10)
    idea_data["priority_score"] = int((data.impact_score / data.effort_score) * 10) if data.effort_score > 0 else 0
    idea = Idea(user_id=current_user.id, **idea_data)
    db.add(idea); db.commit(); db.refresh(idea)
    return idea


@router.get("/", response_model=IdeaListResponse)
async def list_ideas(
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    category: Optional[IdeaCategory] = Query(None),
    status_filter: Optional[IdeaStatus] = Query(None, alias="status"),
    is_favorite: Optional[bool] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(Idea).filter(Idea.user_id == current_user.id)
    if category: query = query.filter(Idea.category == category)
    if status_filter: query = query.filter(Idea.status == status_filter)
    if is_favorite is not None: query = query.filter(Idea.is_favorite == is_favorite)
    query = query.order_by(desc(Idea.priority_score), desc(Idea.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return IdeaListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(idea_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == current_user.id).first()
    if not idea: raise HTTPException(404, "Idea not found")
    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(idea_id: int, data: IdeaUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == current_user.id).first()
    if not idea: raise HTTPException(404, "Idea not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(idea, field, value)
    # Recalc priority score
    if idea.effort_score > 0:
        idea.priority_score = int((idea.impact_score / idea.effort_score) * 10)
    db.commit(); db.refresh(idea)
    return idea


@router.delete("/{idea_id}", status_code=204)
async def delete_idea(idea_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == current_user.id).first()
    if not idea: raise HTTPException(404, "Idea not found")
    db.delete(idea); db.commit()
    return None