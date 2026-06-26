from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional
from datetime import date
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.vision_board import VisionBoard, VisionCategory, VisionItemType
from app.schemas.vision_board import (
    VisionBoardCreate,
    VisionBoardUpdate,
    VisionBoardResponse,
    VisionBoardListResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=VisionBoardResponse, status_code=201)
async def create_item(
    data: VisionBoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = VisionBoard(user_id=current_user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=VisionBoardListResponse)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    category: Optional[VisionCategory] = Query(None),
    item_type: Optional[VisionItemType] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    is_achieved: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List vision board items with pagination + filtering."""
    query = db.query(VisionBoard).filter(VisionBoard.user_id == current_user.id)

    if category:
        query = query.filter(VisionBoard.category == category)
    if item_type:
        query = query.filter(VisionBoard.item_type == item_type)
    if is_favorite is not None:
        query = query.filter(VisionBoard.is_favorite == is_favorite)
    if is_achieved is not None:
        query = query.filter(VisionBoard.is_achieved == is_achieved)

    # Sort: favorites first, then by order_index, then newest
    query = query.order_by(
        desc(VisionBoard.is_favorite),
        asc(VisionBoard.order_index),
        desc(VisionBoard.created_at),
    )

    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return VisionBoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/{item_id}", response_model=VisionBoardResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(VisionBoard).filter(
        VisionBoard.id == item_id,
        VisionBoard.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    return item


@router.put("/{item_id}", response_model=VisionBoardResponse)
async def update_item(
    item_id: int,
    data: VisionBoardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(VisionBoard).filter(
        VisionBoard.id == item_id,
        VisionBoard.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(404, "Not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    # Auto-set achieved_at when marking as achieved
    if update_data.get("is_achieved") and not item.achieved_at:
        item.achieved_at = date.today()

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(VisionBoard).filter(
        VisionBoard.id == item_id,
        VisionBoard.user_id == current_user.id,
    ).first()
    if not item:
        raise HTTPException(404, "Not found")
    db.delete(item)
    db.commit()
    return None