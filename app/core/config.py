"""
app/core/config.py
──────────────────
Application-wide settings loaded from environment variables.

Uses ``pydantic-settings`` so every value is validated at startup.
A singleton instance is created via ``get_settings()`` to avoid
re-reading the ``.env`` file on every request.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration object.

    All fields map 1-to-1 with environment variables (case-insensitive).
    See ``.env.example`` for the full list.
    """

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "DIY Gift Basket API"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"

    # ── Supabase ─────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # ── JWT Authentication ───────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Email / SMTP ─────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@diygiftbasket.com"
    MAIL_FROM_NAME: str = "DIY Gift Basket"

    # ── Pydantic-settings config ─────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",        # auto-load .env in project root
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached ``Settings`` singleton.

    Using ``lru_cache`` ensures the ``.env`` file is read only once,
    and every ``Depends(get_settings)`` call returns the same object.
    """
    return Settings()
