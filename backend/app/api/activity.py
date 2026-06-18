"""Activity routes: report (computes per-friend visible values + delivers
friends' desensitized activity + pending notifications piggyback).

PRD §6: no push, no poll — the report response carries what the user needs.
PRD §4.5: delivered data is desensitized (value + time + offline only).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.activity import (
    ActivityReportRequest,
    ActivityReportResponse,
    FriendActivityOut,
)
from app.schemas.friends import NotificationOut
from app.services.activity import report_activity, visible_to_user
from app.services.notifications import fetch_and_mark_delivered, to_payload_dicts

router = APIRouter(prefix="/activity", tags=["activity"])


@router.post("/report", response_model=ActivityReportResponse)
def report(
    body: ActivityReportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityReportResponse:
    # 1. Compute + persist per-friend visible values (raw components discarded).
    report_activity(db, user.id, body.components)

    # 2. Deliver friends' desensitized activity (what friends expose to me).
    rows = visible_to_user(db, user.id)
    friends_activity = [
        FriendActivityOut(
            friend_id=r.user_id,
            value=r.value,
            last_reported_at=r.last_reported_at,
            is_offline=r.is_offline,
        )
        for r in rows
    ]

    # 3. Piggyback pending notifications (PRD §6).
    notifs = fetch_and_mark_delivered(db, user.id)
    notifications = [NotificationOut(**n) for n in to_payload_dicts(notifs)]

    return ActivityReportResponse(
        friends_activity=friends_activity, notifications=notifications
    )
