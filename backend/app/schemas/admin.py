"""Admin request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AdminUserOut(BaseModel):
    """User info returned in admin user list."""
    id: int
    email: str
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminMessageResponse(BaseModel):
    message: str