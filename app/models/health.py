"""
HealthLog model — track all health metrics in one flexible table.

Each log entry has a 'metric_type' (weight, steps, sleep, etc.)
and stores the value with appropriate units.
"""

from sqlalchemy import Column, String, Text, Integer, Float, Date, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class MetricType(str, enum.Enum):
    # Body Metrics
    WEIGHT = "weight"
    BODY_FAT = "body_fat"
    MUSCLE_MASS = "muscle_mass"
    BMI = "bmi"
    BLOOD_PRESSURE = "blood_pressure"
    HEART_RATE = "heart_rate"
    BLOOD_SUGAR = "blood_sugar"

    # Activity
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES_BURNED = "calories_burned"
    EXERCISE_MINUTES = "exercise_minutes"
    WORKOUT = "workout"

    # Nutrition
    WATER = "water"
    CALORIES_CONSUMED = "calories_consumed"
    PROTEIN = "protein"
    CARBS = "carbs"
    FATS = "fats"
    MEAL = "meal"

    # Sleep & Recovery
    SLEEP_HOURS = "sleep_hours"
    SLEEP_QUALITY = "sleep_quality"

    # Wellness
    MOOD = "mood"
    ENERGY = "energy"
    STRESS = "stress"
    MEDITATION_MINUTES = "meditation_minutes"

    # Medical
    MEDICATION = "medication"
    SYMPTOM = "symptom"

    OTHER = "other"


class HealthLog(BaseModel):
    __tablename__ = "health_logs"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Core Fields ───────────────────────────────────
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    log_date = Column(Date, nullable=False, index=True)

    # ── Value Storage (flexible) ──────────────────────
    value = Column(Float, nullable=True)              # 70.5 (kg, steps, hours)
    value_text = Column(String(500), nullable=True)   # "Headache", "Chest workout"
    unit = Column(String(50), nullable=True)          # "kg", "steps", "hours"

    # ── Extra Data (JSON for flexibility) ─────────────
    # e.g., for workout: {"type": "running", "duration": 30, "intensity": "high"}
    # e.g., for meal: {"name": "Breakfast", "items": ["eggs", "toast"]}
    extra_data = Column(JSON, default=dict, nullable=False)

    # ── Notes ─────────────────────────────────────────
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────
    user = relationship("User", backref="health_logs")

    def __repr__(self):
        return f"<HealthLog(id={self.id}, type='{self.metric_type}', value={self.value})>"