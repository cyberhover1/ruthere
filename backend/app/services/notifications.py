"""Notification service — write events and fetch-and-clear for delivery.

Per PRD §6 (no push, no poll), notifications are delivered piggyback on the
recipient's next report. This module writes events (e.g. friend_removed) and
provides `fetch_and_mark_delivered` consumed by `/friends/notifications` and
the future `/activity/report` (M3).
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import BEIJING_TZ
from app.models import Notification


def create_notification(db: Session, user_id: int, type_: str, payload: dict) -> Notification:
    """Persist a pending notification for `user_id`."""
    row = Notification(
        user_id=user_id,
        type=type_,
        payload=json.dumps(payload, ensure_ascii=False, default=str),
        delivered=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def fetch_and_mark_delivered(db: Session, user_id: int) -> list[Notification]:
    """Return undelivered notifications for `user_id` and mark them delivered."""
    rows = list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.delivered.is_(False))
            .order_by(Notification.created_at.asc())
        )
    )
    if rows:
        db.execute(
            update(Notification)
            .where(Notification.id.in_([r.id for r in rows]))
            .values(delivered=True)
        )
        db.commit()
    return rows


def to_payload_dicts(rows: list[Notification]) -> list[dict]:
    """Convert notification rows to plain dicts with parsed payload."""
    out: list[dict] = []
    for r in rows:
        try:
            payload = json.loads(r.payload) if r.payload else {}
        except json.JSONDecodeError:
            payload = {}
        out.append(
            {
                "id": r.id,
                "type": r.type,
                "payload": payload,
                "created_at": r.created_at,
            }
        )
    return out


def friend_removed_payload(removed_by_user_id: int, removed_by_email: str) -> dict:
    """Standard payload for a friend_removed notification (no secrets)."""
    return {
        "removed_by_user_id": removed_by_user_id,
        "removed_by_email": removed_by_email,
        "at": datetime.now(BEIJING_TZ).isoformat(),
    }


def poked_payload(poked_by_user_id: int, poked_by_email: str) -> dict:
    """Standard payload for a `poked` notification (no secrets)."""
    return {
        "poked_by_user_id": poked_by_user_id,
        "poked_by_email": poked_by_email,
        "at": datetime.now(BEIJING_TZ).isoformat(),
    }
