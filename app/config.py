"""Application Configuration Module.

Reads configuration safely through environment variables and .env file.
Prevents hardcoding of sensitive credentials like the Google Gemini API key.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """FitBuddy application runtime settings."""

    APP_NAME: str = "FitBuddy – AI Fitness Plan Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database Configuration
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'fitbuddy.db'}"

    # Google Gemini Configuration
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"

    # Fallback to dev/mock mode when API key is missing or quota exceeded
    ENABLE_MOCK_FALLBACK: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_gemini_configured(self) -> bool:
        """Checks if a non-placeholder Google API key is configured."""
        key = self.GOOGLE_API_KEY.strip() if self.GOOGLE_API_KEY else ""
        if not key:
            # Also check os.environ directly in case set during execution
            key = os.getenv("GOOGLE_API_KEY", "").strip()
        return bool(key and not key.startswith("your_") and len(key) >= 10)

    @property
    def effective_api_key(self) -> str:
        """Returns the active API key or an empty string."""
        return self.GOOGLE_API_KEY.strip() or os.getenv("GOOGLE_API_KEY", "").strip()

    @property
    def api_status_label(self) -> str:
        """Returns a user-facing label of the AI engine mode."""
        if self.is_gemini_configured:
            return f"Gemini AI Active ({self.GEMINI_MODEL})"
        return "Dev / Mock Mode (API Key not set in .env)"


settings = Settings()
