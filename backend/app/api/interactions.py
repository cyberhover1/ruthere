"""Interaction routes: check-ins (PRD §5.1) + pokes (PRD §5.2).

A poke resets the initiator's activity to full (PRD §4.4) and notifies the
recipient (delivered piggyback on their next report). Same-friend pokes are
rate-limited to one per poke_cooldown_seconds.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import BEIJING_TZ, settings
from app.db.session import get_db
from app.models import CheckIn, Friendship, Poke, User
from app.schemas.auth import MessageResponse
from app.schemas.interactions import CHECKIN_TYPES, CheckInCreate, CheckInOut, PokeOut
from app.services.activity import reset_activity_for_user
from app.services.notifications import create_notification, poked_payload

router = APIRouter(tags=["interactions"])


def _now() -> datetime:
    return datetime.now(BEIJING_TZ)


def _get_my_friendship(db: Session, me_id: int, friendship_id: int) -> Friendship:
    """Resolve a friendship row owned by `me_id` (mirrors friends.py helper)."""
    fs = db.get(Friendship, friendship_id)
    if fs is None or fs.user_id != me_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="好友关系不存在")
    return fs


# --- check-ins (PRD §5.1) -------------------------------------------------

@router.post("/checkins", response_model=CheckInOut, status_code=status.HTTP_201_CREATED)
def create_checkin(
    body: CheckInCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckInOut:
    if body.type not in CHECKIN_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"非法打卡类型，允许: {', '.join(CHECKIN_TYPES)}",
        )
    row = CheckIn(user_id=user.id, type=body.type, note=body.note)
    db.add(row)
    db.commit()
    db.refresh(row)
    return CheckInOut.model_validate(row)


@router.get("/checkins", response_model=list[CheckInOut])
def list_checkins(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CheckInOut]:
    rows = db.scalars(
        select(CheckIn)
        .where(CheckIn.user_id == user.id)
        .order_by(CheckIn.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [CheckInOut.model_validate(r) for r in rows]


# --- pokes (PRD §5.2) -----------------------------------------------------

@router.post("/pokes/{friendship_id}", response_model=PokeOut)
def poke_friend(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PokeOut:
    fs = _get_my_friendship(db, user.id, friendship_id)
    friend_id = fs.friend_id

    # Rate limit: at most one poke to the same friend per cooldown window.
    latest = db.scalar(
        select(Poke)
        .where(Poke.from_user_id == user.id, Poke.to_user_id == friend_id)
        .order_by(Poke.created_at.desc())
    )
    if latest is not None:
        created = latest.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=BEIJING_TZ)
        elapsed = (_now() - created).total_seconds()
        if elapsed < settings.poke_cooldown_seconds:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="戳一戳太频繁，每小时只能戳同一好友一次",
            )

    poke = Poke(from_user_id=user.id, to_user_id=friend_id)
    db.add(poke)

    # PRD §4.4: the initiator's activity resets to full.
    reset_activity_for_user(user.id, db)

    # Notify the poked friend (delivered on their next report).
    create_notification(
        db,
        user_id=friend_id,
        type_="poked",
        payload=poked_payload(user.id, user.email),
    )
    db.commit()
    db.refresh(poke)
    return PokeOut(to_user_id=friend_id, created_at=poke.created_at)
