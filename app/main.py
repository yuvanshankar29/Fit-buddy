"""FitBuddy FastAPI Application Entrypoint.

Configures static assets, Jinja2 templates, database lifecycle,
and global exception handling.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, BASE_DIR
from app.database import init_db
from app.routes import router, templates

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fitbuddy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager to initialize database tables on startup."""
    logger.info("Initializing FitBuddy application...")
    init_db()
    logger.info("FitBuddy database initialized. Ready to serve requests.")
    yield
    logger.info("FitBuddy application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered fitness platform that accepts user biometric parameters and fitness goals "
        "to generate personalized 7-day workout plans, targeted nutrition & recovery tips, "
        "and handles iterative user feedback using Google Gemini."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static assets
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include web and API routes
app.include_router(router)


# Global Exception Handlers for graceful user experience
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    """User-friendly 404 page for unmatched routes."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "API endpoint not found."})
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Page Not Found – FitBuddy",
            "goals": ["Weight Loss", "Muscle Gain", "General Wellness", "Flexibility"],
            "intensities": ["Low", "Medium", "High"],
            "api_configured": settings.is_gemini_configured,
            "api_status": settings.api_status_label,
            "error": "The requested page was not found. Returned to home.",
            "form_data": {},
        },
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    """Friendly 500 error display preventing unhandled stack trace leaks."""
    logger.error("Unhandled internal server error on %s: %s", request.url.path, exc, exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."},
        )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Error – FitBuddy",
            "goals": ["Weight Loss", "Muscle Gain", "General Wellness", "Flexibility"],
            "intensities": ["Low", "Medium", "High"],
            "api_configured": settings.is_gemini_configured,
            "api_status": settings.api_status_label,
            "error": "A server error occurred while processing your request. Please check your inputs or try again.",
            "form_data": {},
        },
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
