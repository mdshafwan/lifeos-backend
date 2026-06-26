from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
import os
import uuid
import aiofiles

from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentCategory
from app.schemas.document import DocumentResponse, DocumentUpdate
from app.core.dependencies import get_current_user
from app.config import settings

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: DocumentCategory = Form(DocumentCategory.OTHER),
    folder: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(413, f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB")

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    user_dir = os.path.join(settings.UPLOAD_DIR, "documents", str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, unique_name)

    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    # Create DB record
    doc = Document(
        user_id=current_user.id,
        name=name or file.filename,
        description=description,
        file_url=f"/uploads/documents/{current_user.id}/{unique_name}",
        file_path=file_path,
        file_size=len(contents),
        file_type=file.content_type or "application/octet-stream",
        file_extension=ext,
        category=category,
        folder=folder,
        tags=[],
    )
    db.add(doc); db.commit(); db.refresh(doc)
    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    category: Optional[DocumentCategory] = Query(None),
    folder: Optional[str] = Query(None),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if category: query = query.filter(Document.category == category)
    if folder: query = query.filter(Document.folder == folder)
    return query.order_by(desc(Document.created_at)).all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Document not found")
    return doc


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(doc_id: int, data: DocumentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Document not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit(); db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc: raise HTTPException(404, "Document not found")
    # Delete physical file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc); db.commit()
    return None