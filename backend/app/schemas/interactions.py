"""Check-in + poke schemas (PRD §5)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.auth import MessageResponse  # reuse


# Fixed check-in types per PRD §5.1 examples.
CHECKIN_TYPES: tuple[str, ...] = ("起床", "休息", "运动", "吃饭")


class CheckInCreate(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    note: str | None = Field(default=None, max_length=255)


class CheckInOut(BaseModel):
    id: int
    type: str
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PokeOut(BaseModel):
    """Minimal confirmation of a poke (no sensitive data)."""

    to_user_id: int
    created_at: datetime


# Re-export MessageResponse for convenience in the router.
__all__ = ["CHECKIN_TYPES", "CheckInCreate", "CheckInOut", "PokeOut", "MessageResponse"]
