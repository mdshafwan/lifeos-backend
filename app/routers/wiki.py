from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional
from math import ceil

from app.database import get_db
from app.models.user import User
from app.models.wiki import Wiki
from app.schemas.wiki import WikiCreate, WikiUpdate, WikiResponse, WikiListResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/", response_model=WikiResponse, status_code=201)
async def create_wiki(data: WikiCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wiki_data = data.model_dump()
    wiki_data["word_count"] = len(data.content.split())
    wiki = Wiki(user_id=current_user.id, **wiki_data)
    db.add(wiki); db.commit(); db.refresh(wiki)
    return wiki


@router.get("/", response_model=WikiListResponse)
async def list_wikis(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(Wiki).filter(Wiki.user_id == current_user.id)
    if category: query = query.filter(Wiki.category == category)
    if search: query = query.filter(or_(Wiki.title.ilike(f"%{search}%"), Wiki.content.ilike(f"%{search}%")))
    query = query.order_by(desc(Wiki.updated_at))
    total = query.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return WikiListResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)


@router.get("/{wiki_id}", response_model=WikiResponse)
async def get_wiki(wiki_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id, Wiki.user_id == current_user.id).first()
    if not wiki: raise HTTPException(404, "Wiki not found")
    wiki.view_count += 1
    db.commit(); db.refresh(wiki)
    return wiki


@router.put("/{wiki_id}", response_model=WikiResponse)
async def update_wiki(wiki_id: int, data: WikiUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id, Wiki.user_id == current_user.id).first()
    if not wiki: raise HTTPException(404, "Wiki not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wiki, field, value)
    if "content" in update_data:
        wiki.word_count = len(update_data["content"].split())
    db.commit(); db.refresh(wiki)
    return wiki


@router.delete("/{wiki_id}", status_code=204)
async def delete_wiki(wiki_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    wiki = db.query(Wiki).filter(Wiki.id == wiki_id, Wiki.user_id == current_user.id).first()
    if not wiki: raise HTTPException(404, "Wiki not found")
    db.delete(wiki); db.commit()
    return None