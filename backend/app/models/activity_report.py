"""Activity report model — one row per (owner, viewer) friend pair.

Stores the *computed visible* activity value (0-100) that `user_id` shows to
`friend_id`, NOT raw sensor data. Raw components live only in the report
request body long enough to compute per-friend values, then are discarded
(PRD §4.5: nothing raw is persisted or delivered).

`value` is the current (decay-adjusted) value; `raw_reported_value` is the
value at last report and serves as the decay baseline.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ActivityReport(Base):
    __tablename__ = "activity_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_activity_reports_user_friend"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # decay-adjusted visible value
    raw_reported_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # decay baseline
    last_reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    is_offline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
