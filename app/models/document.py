"""
Document model — file vault for uploaded documents.
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class DocumentCategory(str, enum.Enum):
    PERSONAL = "personal"
    FINANCIAL = "financial"
    LEGAL = "legal"
    MEDICAL = "medical"
    WORK = "work"
    EDUCATION = "education"
    TRAVEL = "travel"
    INSURANCE = "insurance"
    TAX = "tax"
    OTHER = "other"


class Document(BaseModel):
    __tablename__ = "documents"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)

    # ── File Info ─────────────────────────────────────
    file_url = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)   # Server path
    file_size = Column(Integer, nullable=False)        # Bytes
    file_type = Column(String(100), nullable=False)    # MIME type
    file_extension = Column(String(20), nullable=True) # .pdf, .docx

    # ── Categorization ────────────────────────────────
    category = Column(Enum(DocumentCategory), default=DocumentCategory.OTHER, nullable=False, index=True)
    folder = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)

    # ── Security ──────────────────────────────────────
    is_encrypted = Column(Boolean, default=False, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)

    # ── Important Dates ───────────────────────────────
    expiry_date = Column(String(20), nullable=True)  # For passports, IDs, etc.

    # ── Flags ─────────────────────────────────────────
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', type='{self.file_type}')>"