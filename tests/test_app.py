"""Automated test suite for FitBuddy AI Fitness Plan Generator."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import UserPlan

# Use an in-memory SQLite database with StaticPool for isolated and shared test execution
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Create fresh tables for every test and clean up after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_home_page_loads():
    """Verifies that the home page renders with expected title and elements."""
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text
    assert "Enter Your Fitness Profile" in response.text
    assert 'name="username"' in response.text
    assert 'name="user_id"' in response.text
    assert 'name="age"' in response.text
    assert 'name="weight"' in response.text
    assert 'name="goal"' in response.text
    assert 'name="intensity"' in response.text


def test_generate_workout_form_success():
    """Tests submitting the initial workout plan generation form."""
    form_data = {
        "username": "Alex Rivera",
        "user_id": "alex_rivera_101",
        "age": 28,
        "weight": 76.5,
        "goal": "Muscle Gain",
        "intensity": "High",
    }
    response = client.post("/generate-workout", data=form_data)
    assert response.status_code == 200
    assert "Alex Rivera" in response.text
    assert "alex_rivera_101" in response.text
    assert "Muscle Gain" in response.text
    assert "High" in response.text
    assert "NUTRITION &amp; RECOVERY PROTOCOL" in response.text or "NUTRITION & RECOVERY PROTOCOL" in response.text
    assert "Day 1" in response.text
    assert "Day 7" in response.text

    # Verify database persistence
    db = TestingSessionLocal()
    user = db.query(UserPlan).filter_by(user_id="alex_rivera_101").first()
    assert user is not None
    assert user.username == "Alex Rivera"
    assert user.age == 28
    assert user.weight == 76.5
    assert user.goal == "Muscle Gain"
    assert user.intensity == "High"
    assert user.original_plan is not None
    assert user.nutrition_tip is not None
    assert user.updated_plan is None
    db.close()


def test_form_validation_errors():
    """Tests backend validation rejection for invalid inputs."""
    # Invalid age (under 14)
    invalid_data = {
        "username": "Tom",
        "user_id": "tom123",
        "age": 10,  # Below min 14
        "weight": 70,
        "goal": "Muscle Gain",
        "intensity": "Medium",
    }
    response = client.post("/generate-workout", data=invalid_data)
    assert response.status_code == 422
    assert "Validation Error" in response.text

    # Invalid characters in user_id
    invalid_id = {
        "username": "Sarah",
        "user_id": "sarah space!@#",
        "age": 25,
        "weight": 60,
        "goal": "Weight Loss",
        "intensity": "Low",
    }
    response2 = client.post("/generate-workout", data=invalid_id)
    assert response2.status_code == 422
    assert "Validation Error" in response2.text


def test_submit_feedback_and_regenerate():
    """Tests submitting feedback to revise an existing plan."""
    # First create a user
    form_data = {
        "username": "Diana Prince",
        "user_id": "diana_warrior",
        "age": 30,
        "weight": 68.0,
        "goal": "Weight Loss",
        "intensity": "Medium",
    }
    res1 = client.post("/generate-workout", data=form_data)
    assert res1.status_code == 200

    # Submit feedback to revise plan
    feedback_data = {
        "user_id": "diana_warrior",
        "feedback": "Add more cardio intervals and include more rest days.",
    }
    res2 = client.post("/submit-feedback", data=feedback_data)
    assert res2.status_code == 200
    assert "REVISED 7-DAY WORKOUT PLAN" in res2.text or "REVISED WORKOUT PLAN" in res2.text
    assert "Add more cardio" in res2.text

    # Verify DB update
    db = TestingSessionLocal()
    user = db.query(UserPlan).filter_by(user_id="diana_warrior").first()
    assert user.updated_plan is not None
    assert user.feedback == "Add more cardio intervals and include more rest days."
    db.close()


def test_submit_feedback_user_not_found():
    """Tests submitting feedback for a non-existent user ID."""
    feedback_data = {
        "user_id": "ghost_user_999",
        "feedback": "Please add more cardio",
    }
    response = client.post("/submit-feedback", data=feedback_data)
    assert response.status_code == 404
    assert "was not found" in response.text


def test_submit_empty_feedback():
    """Tests submitting too short feedback on an existing user."""
    form_data = {
        "username": "Diana Prince",
        "user_id": "diana_warrior",
        "age": 30,
        "weight": 68.0,
        "goal": "Weight Loss",
        "intensity": "Medium",
    }
    res1 = client.post("/generate-workout", data=form_data)
    assert res1.status_code == 200

    feedback_data = {
        "user_id": "diana_warrior",
        "feedback": "a",  # Too short (min 3 chars required)
    }
    response = client.post("/submit-feedback", data=feedback_data)
    assert response.status_code == 422
    assert "Feedback Error" in response.text


def test_admin_dashboard_view():
    """Tests the /view-all-users admin dashboard view."""
    # Seed 2 users
    db = TestingSessionLocal()
    user1 = UserPlan(
        user_id="user_one",
        username="User One",
        age=25,
        weight=70.0,
        goal="Flexibility",
        intensity="Low",
        original_plan="Day 1 mobility...",
        nutrition_tip="Hydration tip...",
    )
    user2 = UserPlan(
        user_id="user_two",
        username="User Two",
        age=35,
        weight=85.0,
        goal="Muscle Gain",
        intensity="High",
        original_plan="Day 1 bench press...",
        updated_plan="Day 1 adjusted...",
        feedback="More tricep focus",
        nutrition_tip="High protein tip...",
    )
    db.add(user1)
    db.add(user2)
    db.commit()
    db.close()

    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "Admin &amp; Training" in response.text or "Admin & Training" in response.text
    assert "User One" in response.text
    assert "user_one" in response.text
    assert "User Two" in response.text
    assert "user_two" in response.text
    assert "Flexibility" in response.text
    assert "Muscle Gain" in response.text


def test_api_rest_endpoints():
    """Tests programmatic REST endpoints (/api/workout, /api/feedback, /api/users, /health)."""
    # 1. Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. POST /api/workout
    workout_payload = {
        "username": "Rest Athlete",
        "user_id": "rest_athlete_01",
        "age": 29,
        "weight": 72.0,
        "goal": "General Wellness",
        "intensity": "Medium",
    }
    res_create = client.post("/api/workout", json=workout_payload)
    assert res_create.status_code == 201
    data = res_create.json()
    assert data["success"] is True
    assert data["user"]["user_id"] == "rest_athlete_01"
    assert "Day 1" in data["user"]["original_plan"]

    # 3. GET /api/users/{user_id}
    res_get = client.get("/api/users/rest_athlete_01")
    assert res_get.status_code == 200
    assert res_get.json()["username"] == "Rest Athlete"

    # 4. POST /api/feedback
    feedback_payload = {
        "user_id": "rest_athlete_01",
        "feedback": "Add yoga and more mobility work",
    }
    res_fb = client.post("/api/feedback", json=feedback_payload)
    assert res_fb.status_code == 200
    fb_data = res_fb.json()
    assert fb_data["user"]["updated_plan"] is not None
    assert "yoga" in fb_data["user"]["feedback"].lower()

    # 5. GET /api/users
    res_all = client.get("/api/users")
    assert res_all.status_code == 200
    assert len(res_all.json()) >= 1
