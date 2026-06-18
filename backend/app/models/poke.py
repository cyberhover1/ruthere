"""Poke model — light interaction between friends (PRD §5.2).

Used as the rate-limit source: a poke to the same friend within
`poke_cooldown_seconds` is rejected. No uniqueness constraint because
repeated pokes (across cooldown windows) are legitimate.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Poke(Base):
    __tablename__ = "pokes"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
