"""Per-friend data-source permission matrix (PRD §4.2).

`user_id` opens some sources to `friend_id`. The same user can therefore show
different activity values to different friends. M2 only stores/CRUDs the set;
the actual per-friend activity computation lands in M9.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FriendDataSource(Base):
    __tablename__ = "friend_data_sources"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friend_data_sources_user_friend"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    allowed_sources: Mapped[str] = mapped_column(String(255), default="", nullable=False)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
