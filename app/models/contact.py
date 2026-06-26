"""
Contact module models — Personal CRM with interaction tracking.

Contains 2 models:
- Contact       → people in your network
- Interaction   → touchpoints (calls/messages/meetings/coffees)
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Date, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


# ══════════════════════════════════════════════
#  ENUMS
# ══════════════════════════════════════════════

class ContactCategory(str, enum.Enum):
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    CLIENT = "client"
    MENTOR = "mentor"
    MENTEE = "mentee"
    BUSINESS = "business"
    ACQUAINTANCE = "acquaintance"
    OTHER = "other"


class RelationshipStrength(str, enum.Enum):
    CLOSE = "close"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    DISTANT = "distant"


# ══════════════════════════════════════════════
#  CONTACT MODEL (existing — unchanged)
# ══════════════════════════════════════════════

class Contact(BaseModel):
    __tablename__ = "contacts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Personal Info ──
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # ── Contact Info ──
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)

    # ── Address ──
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # ── Social ──
    linkedin = Column(String(500), nullable=True)
    twitter = Column(String(500), nullable=True)
    instagram = Column(String(500), nullable=True)
    facebook = Column(String(500), nullable=True)

    # ── Work ──
    company = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=True)

    # ── Relationship ──
    category = Column(Enum(ContactCategory), default=ContactCategory.ACQUAINTANCE, nullable=False, index=True)
    relationship_strength = Column(Enum(RelationshipStrength), default=RelationshipStrength.MODERATE, nullable=False)
    how_we_met = Column(Text, nullable=True)

    # ── Important Dates ──
    birthday = Column(Date, nullable=True)
    anniversary = Column(Date, nullable=True)

    # ── Interaction Tracking ──
    last_contacted = Column(Date, nullable=True)
    contact_frequency_days = Column(Integer, nullable=True)
    next_followup = Column(Date, nullable=True)

    # ── Notes & Tags ──
    notes = Column(Text, nullable=True)
    interests = Column(JSON, default=list, nullable=False)
    tags = Column(JSON, default=list, nullable=False)

    # ── Flags ──
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # ── Relationships ──
    user = relationship("User", backref="contacts")
    interactions = relationship(
        "Interaction",
        back_populates="contact",
        cascade="all, delete-orphan",
        order_by="desc(Interaction.date)",
    )

    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.first_name} {self.last_name}')>"


# ══════════════════════════════════════════════
#  INTERACTION MODEL (NEW)
# ══════════════════════════════════════════════

class Interaction(BaseModel):
    __tablename__ = "interactions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Type (string, not enum to avoid PG drama) ──
    # values: call, message, meeting, email, coffee, video, gift, note, other
    interaction_type = Column(String(20), nullable=False, default="note", index=True)

    # ── When ──
    date = Column(Date, nullable=False, index=True)

    # ── Details ──
    notes = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # for calls/meetings/coffees
    location = Column(String(300), nullable=True)

    # ── Relationships ──
    user = relationship("User", backref="user_interactions")
    contact = relationship("Contact", back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(id={self.id}, contact_id={self.contact_id}, type='{self.interaction_type}')>"