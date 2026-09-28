"""SQLAlchemy ORM models for FitBuddy application."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


def utc_now():
    """Return current UTC datetime (timezone-naive for SQLite compatibility)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserPlan(Base):
    """Stores user information, generated 7-day plans, nutrition tips, and revised plans."""

    __tablename__ = "user_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)  # in kg
    goal = Column(String(50), nullable=False)  # Weight Loss, Muscle Gain, General Wellness, Flexibility
    intensity = Column(String(20), nullable=False)  # Low, Medium, High
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text, nullable=True)
    nutrition_tip = Column(Text, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<UserPlan id={self.id} user_id='{self.user_id}' username='{self.username}' goal='{self.goal}'>"

    def to_dict(self) -> dict:
        """Serializes model instance into a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "age": self.age,
            "weight": self.weight,
            "goal": self.goal,
            "intensity": self.intensity,
            "original_plan": self.original_plan,
            "updated_plan": self.updated_plan,
            "nutrition_tip": self.nutrition_tip,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
