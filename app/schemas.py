"""Pydantic schemas for request validation, error reporting, and API responses."""

import re
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Allowed choices
FITNESS_GOALS = ("Weight Loss", "Muscle Gain", "General Wellness", "Flexibility")
WORKOUT_INTENSITIES = ("Low", "Medium", "High")

FitnessGoal = Literal["Weight Loss", "Muscle Gain", "General Wellness", "Flexibility"]
WorkoutIntensity = Literal["Low", "Medium", "High"]


class WorkoutPlanInput(BaseModel):
    """Schema validating initial workout plan generation form and API payloads."""

    username: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="User's full or preferred name",
    )
    user_id: str = Field(
        ...,
        min_length=3,
        max_length=40,
        description="Unique alphanumeric identifier (letters, numbers, hyphens, underscores)",
    )
    age: int = Field(
        ...,
        ge=14,
        le=100,
        description="Age in years (14 - 100)",
    )
    weight: float = Field(
        ...,
        ge=30.0,
        le=300.0,
        description="Weight in kilograms (30.0 - 300.0 kg)",
    )
    goal: FitnessGoal = Field(
        ...,
        description="Fitness objective",
    )
    intensity: WorkoutIntensity = Field(
        ...,
        description="Desired workout intensity level",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return cleaned

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.match(r"^[a-zA-Z0-9_\-]+$", cleaned):
            raise ValueError("User ID may only contain letters, numbers, underscores, and hyphens.")
        if len(cleaned) < 3:
            raise ValueError("User ID must be at least 3 characters.")
        return cleaned

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        if v not in FITNESS_GOALS:
            raise ValueError(f"Invalid fitness goal. Must be one of: {', '.join(FITNESS_GOALS)}")
        return v

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, v: str) -> str:
        if v not in WORKOUT_INTENSITIES:
            raise ValueError(f"Invalid intensity. Must be one of: {', '.join(WORKOUT_INTENSITIES)}")
        return v


class FeedbackInput(BaseModel):
    """Schema validating user modification feedback submission."""

    user_id: str = Field(
        ...,
        min_length=3,
        max_length=40,
        description="User ID whose plan is being revised",
    )
    feedback: str = Field(
        ...,
        min_length=3,
        max_length=1500,
        description="Detailed modification request (e.g., 'Add more cardio', 'Include more rest days')",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("User ID cannot be empty.")
        return cleaned

    @field_validator("feedback")
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("Please provide at least 3 characters of constructive feedback.")
        return cleaned


class UserPlanOut(BaseModel):
    """Response schema for returning user plan records."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    username: str
    age: int
    weight: float
    goal: str
    intensity: str
    original_plan: str
    updated_plan: Optional[str] = None
    nutrition_tip: str
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkoutPlanResultResponse(BaseModel):
    """API response model for generated workout plan."""

    success: bool
    is_mock: bool
    user: UserPlanOut
    message: str
