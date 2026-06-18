"""Activity service: report, decay, offline detection, reset.

Replaces the M1 placeholder. Raw components are accepted from the report
endpoint, used to compute per-friend visible values via the data-source matrix,
then discarded — only the computed 0..100 integers are persisted (PRD §4.5).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.activity_calc import compute_visible_for_friend
from app.core.config import settings
from app.core.data_sources import ALL_DATA_SOURCES, deserialize
from app.models import ActivityReport, FriendDataSource, Friendship

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_or_create_report(db: Session, user_id: int, friend_id: int) -> ActivityReport:
    row = db.scalar(
        select(ActivityReport).where(
            ActivityReport.user_id == user_id, ActivityReport.friend_id == friend_id
        )
    )
    if row is None:
        row = ActivityReport(user_id=user_id, friend_id=friend_id)
        db.add(row)
        db.flush()
    return row


def _allowed_sources_for(db: Session, owner_id: int, viewer_id: int) -> list[str]:
    fds = db.scalar(
        select(FriendDataSource).where(
            FriendDataSource.user_id == owner_id, FriendDataSource.friend_id == viewer_id
        )
    )
    if fds is None:
        # No explicit matrix -> open all sources (default permissive).
        return list(ALL_DATA_SOURCES)
    return deserialize(fds.allowed_sources) or []


def report_activity(
    db: Session, user_id: int, components: dict[str, float]
) -> list[ActivityReport]:
    """Compute + persist per-friend visible values for `user_id`.

    Returns the updated ActivityReport rows (one per friend). Raw components
    are NOT stored.
    """
    friends = db.scalars(
        select(Friendship.friend_id).where(Friendship.user_id == user_id)
    )
    now = _now()
    updated: list[ActivityReport] = []
    for friend_id in friends:
        allowed = _allowed_sources_for(db, user_id, friend_id)
        visible = compute_visible_for_friend(components, allowed)
        row = _get_or_create_report(db, user_id, friend_id)
        row.value = visible
        row.raw_reported_value = visible
        row.last_reported_at = now
        row.is_offline = False
        updated.append(row)
    db.commit()
    return updated


def reset_activity_for_user(user_id: int, db: Session) -> None:
    """Set all of a user's per-friend visible values to full (100).

    Triggered on login (PRD §4.4.1) and poke-initiator (M4).
    """
    rows = list(
        db.scalars(select(ActivityReport).where(ActivityReport.user_id == user_id))
    )
    now = _now()
    for row in rows:
        row.value = settings.activity_max_value
        row.raw_reported_value = settings.activity_max_value
        row.last_reported_at = now
        row.is_offline = False
    db.commit()
    logger.info("reset activity for user_id=%s (%d rows)", user_id, len(rows))


def decay_all(db: Session) -> int:
    """Linearly decay every activity row based on time since last report.

    value = max(0, raw_reported_value - rate * hours_since_report).
    Returns the number of rows updated.
    """
    rows = list(db.scalars(select(ActivityReport)))
    now = _now()
    changed = 0
    for row in rows:
        reported = row.last_reported_at
        if reported.tzinfo is None:
            reported = reported.replace(tzinfo=timezone.utc)
        hours = (now - reported).total_seconds() / 3600.0
        decayed = row.raw_reported_value - settings.decay_rate_per_hour * hours
        new_value = max(0, round(decayed))
        if new_value != row.value:
            row.value = new_value
            changed += 1
    db.commit()
    return changed


def mark_offline(db: Session) -> int:
    """Flag rows whose last report is older than offline_threshold_hours as offline.

    Returns the number of rows newly marked offline.
    """
    threshold = _now() - timedelta(hours=settings.offline_threshold_hours)
    rows = list(
        db.scalars(
            select(ActivityReport).where(ActivityReport.is_offline.is_(False))
        )
    )
    marked = 0
    for row in rows:
        reported = row.last_reported_at
        if reported.tzinfo is None:
            reported = reported.replace(tzinfo=timezone.utc)
        if reported < threshold:
            row.is_offline = True
            marked += 1
    db.commit()
    return marked


def visible_to_user(db: Session, viewer_id: int) -> list[ActivityReport]:
    """Return the activity rows that friends expose to `viewer_id`.

    These are rows where friend_id == viewer_id (friend is the owner/user_id).
    Delivered to the viewer desensitized (value + time + offline only).
    """
    return list(
        db.scalars(
            select(ActivityReport).where(ActivityReport.friend_id == viewer_id)
        )
    )
