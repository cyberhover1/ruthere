"""Activity report request/response schemas.

The report request carries raw component values (transient — not persisted).
The response is strictly desensitized per PRD §4.5: only value, time, offline.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.friends import NotificationOut


class ActivityReportRequest(BaseModel):
    """Raw per-source component values in 0..1, transient (never stored)."""

    components: dict[str, float] = Field(
        default_factory=dict,
        description="source id -> normalized 0..1 value (e.g. steps, screen_unlock, ...)",
    )


class FriendActivityOut(BaseModel):
    """A friend's activity as seen by me — desensitized (PRD §4.5)."""

    friend_id: int
    value: int  # 0..100
    last_reported_at: datetime
    is_offline: bool


class ActivityReportResponse(BaseModel):
    """Response to /activity/report: friends' desensitized activity + notifications."""

    friends_activity: list[FriendActivityOut]
    notifications: list[NotificationOut] = Field(default_factory=list)
