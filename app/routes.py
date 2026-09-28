"""FastAPI application routes and endpoint handlers.

Implements all required HTML form views, feedback updates, and admin dashboard,
along with REST API endpoints for automated programmatic testing and documentation.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
import markdown as md_lib

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import ValidationError

from app.config import settings, BASE_DIR
from app.database import get_db
from app.models import UserPlan, utc_now
from app.schemas import (
    WorkoutPlanInput,
    FeedbackInput,
    UserPlanOut,
    WorkoutPlanResultResponse,
    FITNESS_GOALS,
    WORKOUT_INTENSITIES,
)
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import regenerate_workout_with_feedback

logger = logging.getLogger(__name__)

router = APIRouter()

# Jinja2 template setup
templates_dir = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def render_markdown(text: Optional[str]) -> str:
    """Jinja filter to convert Markdown to clean HTML."""
    if not text:
        return ""
    return md_lib.markdown(
        text,
        extensions=["extra", "nl2br", "tables", "sane_lists"],
        output_format="html5",
    )


# Register filter with Jinja2 environment
templates.env.filters["markdown"] = render_markdown


# ============================================================================
# HTML WEB INTERFACE ROUTES
# ============================================================================


@router.get("/", response_class=HTMLResponse, summary="FitBuddy Home Page")
async def home_page(request: Request, error: Optional[str] = None):
    """Renders the main FitBuddy index page with input form and feature overview."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "FitBuddy – AI Fitness Plan Generator",
            "goals": FITNESS_GOALS,
            "intensities": WORKOUT_INTENSITIES,
            "api_configured": settings.is_gemini_configured,
            "api_status": settings.api_status_label,
            "error": error,
            "form_data": {},
        },
    )


@router.post("/generate-workout", response_class=HTMLResponse, summary="Generate 7-Day Workout Plan")
async def generate_workout_form(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    """Accepts form submission, validates inputs, invokes AI generators, saves to DB, and renders results."""
    raw_data = {
        "username": username,
        "user_id": user_id,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity,
    }

    # Backend Pydantic validation
    try:
        validated = WorkoutPlanInput(**raw_data)
    except ValidationError as val_err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in val_err.errors()]
        error_msg = "Validation Error: " + "; ".join(errors)
        logger.warning("Form validation failed for %s: %s", user_id, error_msg)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FitBuddy – AI Fitness Plan Generator",
                "goals": FITNESS_GOALS,
                "intensities": WORKOUT_INTENSITIES,
                "api_configured": settings.is_gemini_configured,
                "api_status": settings.api_status_label,
                "error": error_msg,
                "form_data": raw_data,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    try:
        # Step 1: Generate 7-day workout plan using Gemini
        workout_plan, is_workout_mock = generate_workout_gemini(
            username=validated.username,
            user_id=validated.user_id,
            age=validated.age,
            weight=validated.weight,
            goal=validated.goal,
            intensity=validated.intensity,
        )

        # Step 2: Generate concise nutrition/recovery tip using Gemini Flash
        nutrition_tip, is_nutrition_mock = generate_nutrition_tip_with_flash(
            goal=validated.goal,
            age=validated.age,
            weight=validated.weight,
            intensity=validated.intensity,
        )

        # Step 3: Persist record in SQLite via SQLAlchemy
        existing_record = (
            db.query(UserPlan)
            .filter(UserPlan.user_id == validated.user_id)
            .order_by(UserPlan.id.desc())
            .first()
        )

        if existing_record:
            # Update existing user profile and overwrite with new initial plan
            existing_record.username = validated.username
            existing_record.age = validated.age
            existing_record.weight = validated.weight
            existing_record.goal = validated.goal
            existing_record.intensity = validated.intensity
            existing_record.original_plan = workout_plan
            existing_record.nutrition_tip = nutrition_tip
            existing_record.updated_plan = None
            existing_record.feedback = None
            existing_record.updated_at = utc_now()
            user_plan = existing_record
        else:
            user_plan = UserPlan(
                user_id=validated.user_id,
                username=validated.username,
                age=validated.age,
                weight=validated.weight,
                goal=validated.goal,
                intensity=validated.intensity,
                original_plan=workout_plan,
                nutrition_tip=nutrition_tip,
                updated_plan=None,
                feedback=None,
            )
            db.add(user_plan)

        db.commit()
        db.refresh(user_plan)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": f"FitBuddy Plan – {user_plan.username}",
                "user": user_plan,
                "is_mock": is_workout_mock or is_nutrition_mock,
                "is_updated": False,
                "status_message": "Your personalized 7-Day Workout Plan and Nutrition Protocol have been generated!",
                "api_status": settings.api_status_label,
            },
        )

    except Exception as exc:
        db.rollback()
        logger.error("Failed to generate or save workout plan: %s", exc, exc_info=True)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FitBuddy – AI Fitness Plan Generator",
                "goals": FITNESS_GOALS,
                "intensities": WORKOUT_INTENSITIES,
                "api_configured": settings.is_gemini_configured,
                "api_status": settings.api_status_label,
                "error": f"An error occurred while generating your plan: {str(exc)}",
                "form_data": raw_data,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/submit-feedback", response_class=HTMLResponse, summary="Submit Plan Feedback and Regenerate")
async def submit_feedback_form(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    """Receives feedback, fetches original plan, regenerates revised plan with Gemini, and saves update."""
    raw_data = {"user_id": user_id, "feedback": feedback}

    try:
        validated = FeedbackInput(**raw_data)
    except ValidationError as val_err:
        errors = [f"{e['loc'][0]}: {e['msg']}" for e in val_err.errors()]
        error_msg = "Feedback Error: " + "; ".join(errors)
        logger.warning("Feedback validation failed: %s", error_msg)

        # Retrieve user if possible to re-render result with error
        user_record = db.query(UserPlan).filter(UserPlan.user_id == user_id.strip()).order_by(UserPlan.id.desc()).first()
        if user_record:
            return templates.TemplateResponse(
                request=request,
                name="result.html",
                context={
                    "title": f"FitBuddy Plan – {user_record.username}",
                    "user": user_record,
                    "is_mock": not settings.is_gemini_configured,
                    "is_updated": bool(user_record.updated_plan),
                    "error": error_msg,
                    "api_status": settings.api_status_label,
                },
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )
        return RedirectResponse(url=f"/?error={error_msg}", status_code=status.HTTP_303_SEE_OTHER)

    user_record = (
        db.query(UserPlan)
        .filter(UserPlan.user_id == validated.user_id)
        .order_by(UserPlan.id.desc())
        .first()
    )

    if not user_record:
        logger.warning("Feedback submission for non-existent user_id: %s", validated.user_id)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": "FitBuddy – AI Fitness Plan Generator",
                "goals": FITNESS_GOALS,
                "intensities": WORKOUT_INTENSITIES,
                "api_configured": settings.is_gemini_configured,
                "api_status": settings.api_status_label,
                "error": f"User ID '{validated.user_id}' was not found in our database. Please generate an initial workout plan first.",
                "form_data": {},
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        # Regenerate revised plan with feedback preserved
        revised_plan, is_mock = regenerate_workout_with_feedback(
            original_plan=user_record.original_plan,
            feedback=validated.feedback,
            username=user_record.username,
            goal=user_record.goal,
            intensity=user_record.intensity,
            age=user_record.age,
            weight=user_record.weight,
        )

        user_record.updated_plan = revised_plan
        user_record.feedback = validated.feedback
        user_record.updated_at = utc_now()

        db.commit()
        db.refresh(user_record)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": f"FitBuddy Plan – {user_record.username} (Updated)",
                "user": user_record,
                "is_mock": is_mock,
                "is_updated": True,
                "status_message": "Success! Your workout plan has been revised and tailored to your feedback.",
                "api_status": settings.api_status_label,
            },
        )

    except Exception as exc:
        db.rollback()
        logger.error("Failed to update workout plan with feedback: %s", exc, exc_info=True)
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "title": f"FitBuddy Plan – {user_record.username}",
                "user": user_record,
                "is_mock": not settings.is_gemini_configured,
                "is_updated": bool(user_record.updated_plan),
                "error": f"Failed to regenerate plan with feedback: {str(exc)}",
                "api_status": settings.api_status_label,
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/view-all-users", response_class=HTMLResponse, summary="Admin Dashboard")
async def view_all_users(request: Request, db: Session = Depends(get_db)):
    """Admin dashboard presenting registered users, original plans, and updated plans."""
    users = db.query(UserPlan).order_by(UserPlan.created_at.desc()).all()

    # Calculate dashboard metrics
    total_users = len(users)
    updated_count = sum(1 for u in users if u.updated_plan)
    
    # Calculate most popular goal
    goals_count = {}
    for u in users:
        goals_count[u.goal] = goals_count.get(u.goal, 0) + 1
    popular_goal = max(goals_count.items(), key=lambda x: x[1])[0] if goals_count else "None"
    
    avg_age = round(sum(u.age for u in users) / total_users, 1) if total_users > 0 else 0

    stats = {
        "total_users": total_users,
        "updated_count": updated_count,
        "popular_goal": popular_goal,
        "avg_age": avg_age,
    }

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "title": "FitBuddy – Admin Dashboard & User Directory",
            "users": users,
            "stats": stats,
            "api_status": settings.api_status_label,
            "api_configured": settings.is_gemini_configured,
        },
    )


# ============================================================================
# PROGRAMMATIC REST API ENDPOINTS (For Testing & Integrations)
# ============================================================================


@router.post(
    "/api/workout",
    response_model=WorkoutPlanResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="API: Generate Workout Plan (JSON)",
)
async def api_generate_workout(payload: WorkoutPlanInput, db: Session = Depends(get_db)):
    """Programmatic JSON endpoint to generate and persist a workout plan."""
    plan_text, is_workout_mock = generate_workout_gemini(
        username=payload.username,
        user_id=payload.user_id,
        age=payload.age,
        weight=payload.weight,
        goal=payload.goal,
        intensity=payload.intensity,
    )

    nutrition_tip, is_nutrition_mock = generate_nutrition_tip_with_flash(
        goal=payload.goal,
        age=payload.age,
        weight=payload.weight,
        intensity=payload.intensity,
    )

    existing = (
        db.query(UserPlan)
        .filter(UserPlan.user_id == payload.user_id)
        .order_by(UserPlan.id.desc())
        .first()
    )

    if existing:
        existing.username = payload.username
        existing.age = payload.age
        existing.weight = payload.weight
        existing.goal = payload.goal
        existing.intensity = payload.intensity
        existing.original_plan = plan_text
        existing.nutrition_tip = nutrition_tip
        existing.updated_plan = None
        existing.feedback = None
        existing.updated_at = utc_now()
        user_plan = existing
    else:
        user_plan = UserPlan(
            user_id=payload.user_id,
            username=payload.username,
            age=payload.age,
            weight=payload.weight,
            goal=payload.goal,
            intensity=payload.intensity,
            original_plan=plan_text,
            nutrition_tip=nutrition_tip,
        )
        db.add(user_plan)

    db.commit()
    db.refresh(user_plan)

    return WorkoutPlanResultResponse(
        success=True,
        is_mock=is_workout_mock or is_nutrition_mock,
        user=UserPlanOut.model_validate(user_plan),
        message="Workout plan generated successfully",
    )


@router.post(
    "/api/feedback",
    response_model=WorkoutPlanResultResponse,
    summary="API: Submit Feedback & Update Plan (JSON)",
)
async def api_submit_feedback(payload: FeedbackInput, db: Session = Depends(get_db)):
    """Programmatic JSON endpoint to revise a plan based on feedback."""
    user_record = (
        db.query(UserPlan)
        .filter(UserPlan.user_id == payload.user_id)
        .order_by(UserPlan.id.desc())
        .first()
    )

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User ID '{payload.user_id}' not found.",
        )

    revised_plan, is_mock = regenerate_workout_with_feedback(
        original_plan=user_record.original_plan,
        feedback=payload.feedback,
        username=user_record.username,
        goal=user_record.goal,
        intensity=user_record.intensity,
        age=user_record.age,
        weight=user_record.weight,
    )

    user_record.updated_plan = revised_plan
    user_record.feedback = payload.feedback
    user_record.updated_at = utc_now()

    db.commit()
    db.refresh(user_record)

    return WorkoutPlanResultResponse(
        success=True,
        is_mock=is_mock,
        user=UserPlanOut.model_validate(user_record),
        message="Workout plan updated successfully with feedback",
    )


@router.get("/api/users", response_model=List[UserPlanOut], summary="API: List All Users (JSON)")
async def api_list_users(db: Session = Depends(get_db)):
    """Returns all registered user plans in JSON format."""
    users = db.query(UserPlan).order_by(UserPlan.created_at.desc()).all()
    return [UserPlanOut.model_validate(u) for u in users]


@router.get("/api/users/{user_id}", response_model=UserPlanOut, summary="API: Get User by ID (JSON)")
async def api_get_user(user_id: str, db: Session = Depends(get_db)):
    """Returns details for a specific user ID."""
    user = db.query(UserPlan).filter(UserPlan.user_id == user_id).order_by(UserPlan.id.desc()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPlanOut.model_validate(user)


@router.get("/health", summary="Application & AI Health Check")
async def health_check():
    """Returns application health and configuration diagnostics."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "gemini_configured": settings.is_gemini_configured,
        "gemini_model": settings.GEMINI_MODEL,
        "flash_model": settings.GEMINI_FLASH_MODEL,
        "database_url": settings.DATABASE_URL,
    }
