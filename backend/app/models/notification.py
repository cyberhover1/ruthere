"""Pending notification model — delivered piggyback on the next report.

Per the "no push, no poll" architecture (PRD §6), events like `friend_removed`
are stored here and returned to the recipient when they next call
`/activity/report` (or `/friends/notifications`). `delivered` marks consumed.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. friend_removed
    payload: Mapped[str] = mapped_column(String(512), default="{}", nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
