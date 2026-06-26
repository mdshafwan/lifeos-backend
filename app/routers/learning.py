from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.learning import Learning, LearningStatus, LearningType
from app.schemas.learning import LearningCreate, LearningUpdate, LearningResponse, LearningListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=LearningResponse, status_code=201)
async def create_learning(data: LearningCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    learning = Learning(user_id=current_user.id, **data.model_dump())
    db.add(learning); db.commit(); db.refresh(learning)
    return learning


@router.get("/", response_model=LearningListResponse)
async def list_learning(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[LearningStatus] = Query(None, alias="status"),
    learning_type: Optional[LearningType] = Query(None),
    search: Optional[str] = Query(None),  # 🆕 NEW
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Learning).filter(Learning.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Learning.status == status_filter)
    if learning_type:
        query = query.filter(Learning.learning_type == learning_type)
    if search:  # 🆕 NEW
        from sqlalchemy import or_
        s = f"%{search}%"
        query = query.filter(
            or_(
                Learning.title.ilike(s),
                Learning.instructor.ilike(s),
                Learning.provider.ilike(s),
            )
        )
    
    query = query.order_by(desc(Learning.created_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return LearningListResponse(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1,
    )

@router.get("/{learning_id}", response_model=LearningResponse)
async def get_learning(learning_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    learning = db.query(Learning).filter(Learning.id == learning_id, Learning.user_id == current_user.id).first()
    if not learning: raise HTTPException(404, "Not found")
    return learning


@router.put("/{learning_id}", response_model=LearningResponse)
async def update_learning(learning_id: int, data: LearningUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    learning = db.query(Learning).filter(Learning.id == learning_id, Learning.user_id == current_user.id).first()
    if not learning: raise HTTPException(404, "Not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(learning, field, value)
    db.commit(); db.refresh(learning)
    return learning


@router.delete("/{learning_id}", status_code=204)
async def delete_learning(learning_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    learning = db.query(Learning).filter(Learning.id == learning_id, Learning.user_id == current_user.id).first()
    if not learning: raise HTTPException(404, "Not found")
    db.delete(learning); db.commit()
    return None