# ⚡ FitBuddy – AI Fitness Plan Generator

FitBuddy is a production-grade, AI-driven web application that generates personalized 7-day workout plans, goal-oriented nutrition and recovery protocols, and iteratively updates training regimens based on user feedback. Powered by **FastAPI**, **SQLite/SQLAlchemy ORM**, **Jinja2**, and the official **Google Gemini GenAI SDK (`google-genai`)**.

---

## 📋 Table of Contents

- [Overview & Capabilities](#-overview--capabilities)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
  - [1. Clone / Navigate to Project](#1-navigate-to-project)
  - [2. Virtual Environment Setup](#2-virtual-environment-setup)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Environment Variables Configuration](#4-environment-variables-configuration)
- [Running the Application](#-running-the-application)
- [Application Routes](#-application-routes)
- [Features Walkthrough](#-features-walkthrough)
  - [1. Plan Generation](#1-plan-generation)
  - [2. Nutrition & Recovery Protocols](#2-nutrition--recovery-protocols)
  - [3. Iterative Feedback System](#3-iterative-feedback-system)
  - [4. Admin Dashboard](#4-admin-dashboard)
  - [5. Fallback & Dev/Mock Mode](#5-fallback--devmock-mode)
- [Testing the Application](#-testing-the-application)
- [Troubleshooting & Common Errors](#-troubleshooting--common-errors)

---

## 🌟 Overview & Capabilities

FitBuddy collects trainee attributes (**Name**, **User ID**, **Age**, **Weight in kg**, **Primary Goal**, and **Workout Intensity**) to construct tailored 7-day physical training regimens.

### Core Features:
- **7-Day Structured Workout Generation**: Day-by-day programs containing warm-up, primary exercises (sets, reps/duration, rest intervals), and cool-down mobility work.
- **Goal-Tailored Nutrition & Recovery Protocols**: Specific protein intake targets in grams, daily hydration formulas in liters, meal timing, and sleep/fascial recovery guidelines.
- **Adaptive AI Feedback Engine**: Allows trainees to submit modification requests (e.g., *"Add more cardio"*, *"Include more rest days"*, *"Add yoga"*, *"Reduce workout intensity"*, *"Focus more on core exercises"*). The AI preserves the user's primary goal while rebalancing training volume and splits.
- **Persistence with SQLite & SQLAlchemy ORM**: Automatically handles database creation and stores original plans, revised plans, biometric parameters, and modification history.
- **Interactive Admin Dashboard**: Responsive card and table layout displaying all registered athletes, filtering by fitness goal, instant search, and a modal plan dossier.
- **Pure CSS Athletic Dark Theme**: High-contrast, responsive UI styled with CSS variables, glowing focus states, print-to-PDF styles, and preset 1-click test profiles.
- **Dual Mode (Production Gemini & Safe Dev Fallback)**: Runs with live Gemini 2.5 models when an API key is provided, or seamlessly runs in a local mock simulation mode for testing when an API key is absent.

---

## 🏗️ Architecture & Tech Stack

| Layer | Technology | Description |
|---|---|---|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance asynchronous Python web framework |
| **Server** | [Uvicorn](https://www.uvicorn.org/) | Lightning-fast ASGI web server implementation |
| **Templating** | [Jinja2](https://palletsprojects.com/p/jinja/) | Server-side template rendering with custom Markdown filters |
| **Database & ORM** | [SQLite](https://www.sqlite.org/) & [SQLAlchemy](https://www.sqlalchemy.org/) | Lightweight relational persistence and object-relational mapping |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict data parsing, type validation, and range checks |
| **AI Provider** | [Google GenAI SDK](https://github.com/google/generative-ai-python) (`google-genai`) | Official modern Gemini SDK using `gemini-2.5-flash` |
| **Styling** | Modern CSS3 (Vanilla) | Custom dark athletic design without paid or heavy frontend dependencies |
| **Configuration** | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) & [python-dotenv](https://github.com/theskumar/python-dotenv) | Safe environment configuration from `.env` |
| **Testing** | [pytest](https://pytest.org/) & [HTTPX](https://www.python-httpx.org/) | Comprehensive integration and unit testing suite |

---

## 📁 Project Directory Structure

```
fitbuddy/
│
├── app/
│   ├── __init__.py                  # App package initialization
│   ├── main.py                      # FastAPI application entrypoint & exception handlers
│   ├── routes.py                    # Web form routes and REST API endpoints
│   ├── database.py                  # SQLAlchemy engine, session generator, init_db()
│   ├── models.py                    # SQLAlchemy ORM models (UserPlan)
│   ├── schemas.py                   # Pydantic validation schemas & API models
│   ├── gemini_generator.py          # 7-day workout plan generator (Gemini / Mock)
│   ├── gemini_flash_generator.py    # Nutrition & recovery protocol generator
│   ├── updated_plan.py              # Feedback revision generator
│   └── config.py                    # Environment settings & API status inspection
│
├── templates/
│   ├── index.html                   # Trainee input form with quick test presets
│   ├── result.html                  # Plan display, nutrition tip & feedback form
│   └── all_users.html               # Admin dashboard & interactive plan inspector
│
├── static/
│   ├── css/
│   │   └── style.css                # Dark fitness theme & responsive layout
│   └── images/
│       └── logo.svg                 # FitBuddy SVG logo
│
├── tests/
│   ├── __init__.py                  # Test package initialization
│   └── test_app.py                  # Pytest test suite (8 test cases)
│
├── .env.example                     # Sample environment variable template
├── .gitignore                       # Git ignore rules for virtualenvs, keys & DB
├── requirements.txt                 # Pinned production dependencies
└── README.md                        # Documentation & operation manual
```

---

## 💻 Prerequisites

- **Python 3.10+** (Tested on Python 3.12)
- **Google Gemini API Key** (Optional for testing; required for live AI responses from Google AI Studio)

---

## 🚀 Installation & Setup

### 1. Navigate to Project Directory

```bash
cd d:\fitbuddy
```

### 2. Virtual Environment Setup

#### On Windows (PowerShell or Command Prompt):
```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

#### On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Variables Configuration

Copy `.env.example` to create your active `.env` file:

#### On Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### On Linux / macOS:
```bash
cp .env.example .env
```

Open `.env` in any text editor and supply your **Google Gemini API key**:

```env
# Get your API key from https://aistudio.google.com/
GOOGLE_API_KEY=your_actual_gemini_api_key_here

GEMINI_MODEL=gemini-2.5-flash
GEMINI_FLASH_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./fitbuddy.db
ENABLE_MOCK_FALLBACK=true
DEBUG=false
```

> **Note:** If you do not have a Gemini API key yet, you can leave `GOOGLE_API_KEY` blank or commented out. FitBuddy will automatically detect this and run in **Development / Mock Mode**, providing fully formatted 7-day plans and nutrition tips for testing!

---

## ▶️ Running the Application

Start the Uvicorn ASGI development server:

```bash
uvicorn app.main:app --reload
```

Once started:
- 🌐 **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📚 **FastAPI Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📖 **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🛣️ Application Routes

### Web Interface Routes:
| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Home page with parameter input form and 1-click test presets |
| `POST` | `/generate-workout` | Validates inputs, generates 7-day plan + nutrition tip, saves to DB, renders `result.html` |
| `POST` | `/submit-feedback` | Receives feedback for a user ID, regenerates revised plan with Gemini, renders updated results |
| `GET` | `/view-all-users` | Admin dashboard listing all registered users, stats, and plan modals |

### Programmatic REST API Endpoints:
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/workout` | JSON endpoint to generate and save workout plan |
| `POST` | `/api/feedback` | JSON endpoint to submit modification feedback |
| `GET` | `/api/users` | JSON endpoint returning list of all registered users |
| `GET` | `/api/users/{user_id}` | JSON endpoint returning full dossier for a specific user ID |
| `GET` | `/health` | Health check endpoint returning configuration & model status |

---

## 💡 Features Walkthrough

### 1. Plan Generation
On the homepage (`/`), provide:
- **Full Name**: e.g., "Alex Rivera"
- **User ID**: Alphanumeric ID (e.g., `alex_rivera_101`)
- **Age**: 14 to 100
- **Weight**: 30.0 to 300.0 kg
- **Goal**: *Weight Loss*, *Muscle Gain*, *General Wellness*, or *Flexibility*
- **Intensity**: *Low*, *Medium*, or *High*

*Tip: Use the 1-click quick-fill buttons under "Quick Test Profiles" to instantly test realistic scenarios!*

### 2. Nutrition & Recovery Protocols
Each plan is accompanied by a targeted nutrition card displaying:
- Exact daily protein target in grams calculated from the user's body weight.
- Hydration targets based on physical mass and training expenditure.
- Pre- and post-workout nutritional timing recommendations.
- Sleep hygiene and neuromuscular recovery protocols.

### 3. Iterative Feedback System
From the result page (`/generate-workout`), trainees can adjust their plans:
- Suggestion chips provide quick actions (*+ Add more cardio*, *+ Include more rest days*, *+ Add yoga*, *+ Reduce workout intensity*, *+ Focus more on core exercises*).
- Custom feedback can be entered in the textarea.
- The revised plan is displayed in an accented container, clearly showing the changes applied while maintaining the user's primary goal.

### 4. Admin Dashboard
Available at `/view-all-users`:
- Summarizes metric indicators: Total Users, Revisions Applied, Top Goal, Average Age.
- Live client-side search by user name or ID.
- Goal filter dropdown.
- "Inspect Plan" button opens a popup modal with the baseline plan, updated plan, and feedback notes.

---

## 🧪 Testing the Application

FitBuddy includes an automated test suite covering all routes, validation rules, feedback regeneration, database persistence, and API endpoints.

To run the test suite:

```bash
pytest -v
```

Expected output:
```
tests/test_app.py::test_home_page_loads PASSED                     [ 12%]
tests/test_app.py::test_generate_workout_form_success PASSED       [ 25%]
tests/test_app.py::test_form_validation_errors PASSED              [ 37%]
tests/test_app.py::test_submit_feedback_and_regenerate PASSED      [ 50%]
tests/test_app.py::test_submit_feedback_user_not_found PASSED      [ 62%]
tests/test_app.py::test_submit_empty_feedback PASSED               [ 75%]
tests/test_app.py::test_admin_dashboard_view PASSED                [ 87%]
tests/test_app.py::test_api_rest_endpoints PASSED                  [100%]

========================= 8 passed in 0.68s =========================
```

---

## 🛠️ Troubleshooting & Common Errors

1. **`GOOGLE_API_KEY` is not set**:
   - FitBuddy will display a yellow `DEV / MOCK MODE` badge in the header. The app remains fully functional and uses structured local templates.
   - To enable live AI, create `.env` and set `GOOGLE_API_KEY=AIzaSy...`.
2. **Quota Exceeded / Network Timeout on Gemini API**:
   - FitBuddy gracefully falls back to the local rules engine and prepends an informative warning alert rather than crashing with an unhandled 500 error.
3. **Database Locks**:
   - SQLite handles multi-threading via `check_same_thread=False` in `app/database.py`. If you ever need a clean database reset, simply delete `fitbuddy.db` and restart the server.
4. **Input Validation Failures**:
   - If an age (< 14 or > 100), weight (< 30kg or > 300kg), or user ID containing special characters is entered, the form preserves your input and renders an accessible error alert.

---

## 📄 License & Attribution

FitBuddy AI is built for personal training, exercise physiology research, and fitness education.
Exercises should be performed with proper form and safety equipment. Consult a healthcare provider before beginning any strenuous physical activity.
