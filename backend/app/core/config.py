"""Application configuration loaded from environment variables.

Secrets (Resend API key, JWT secret, DB password) MUST come from the
environment or a local .env file — never hard-coded. See .env.example.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "安心圈"
    environment: str = Field(default="dev")
    debug: bool = False

    # --- Database ---
    database_url: str = "postgresql+psycopg2://ruthere:ruthere@localhost:5432/ruthere"

    # --- Auth ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # --- Resend (email verification) ---
    resend_api_key: str = ""
    resend_from_email: str = "no-reply@anxinquan.app"
    email_code_length: int = 6
    email_code_expire_minutes: int = 10
    resend_cooldown_seconds: int = 60  # min gap between two codes for the same email

    # --- Activity decay / offline ---
    decay_interval_minutes: int = 10
    offline_threshold_hours: int = 12

    # --- Friends ---
    qr_token_expire_minutes: int = 10  # dynamic friend-QR token lifetime
    max_data_sources_per_friend: int = 7  # PRD §4.1 lists 7 sensor sources


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
