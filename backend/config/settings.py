"""
Configuration Settings for ManganeseInsight Backend
----------------------------------------------------
This module manages all application settings and environment variables.
Using centralized settings ensures configuration values (like CORS origins,
ports, and external API credentials) are loaded from a single source of truth.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory pointing to the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from .env file if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Also attempt default load
    load_dotenv()


class Settings:
    """
    Application configuration container.
    Reads from environment variables with safe fallback defaults for local development.
    """
    PROJECT_NAME: str = "ManganeseInsight API"
    PROJECT_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Server binding
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS configuration: Vite frontend runs on http://localhost:5173 by default.
    # Allowing this origin is required for browser HTTP requests from React to FastAPI.
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    # Google Earth Engine (GEE) credentials (kept strictly on server side)
    GEE_PROJECT_ID: str = os.getenv("GEE_PROJECT_ID", "")
    GEE_SERVICE_ACCOUNT: str = os.getenv("GEE_SERVICE_ACCOUNT", os.getenv("GEE_SERVICE_ACCOUNT_EMAIL", ""))
    GEE_PRIVATE_KEY: str = os.getenv("GEE_PRIVATE_KEY", "")
    GEE_SERVICE_ACCOUNT_KEY_PATH: str = os.getenv("GEE_SERVICE_ACCOUNT_KEY_PATH", "")


# Singleton instance of application settings
settings = Settings()
