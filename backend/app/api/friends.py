"""Friend routes: QR add, email search, requests, list, nickname, delete,
per-friend data-source matrix, and pending notifications.

All endpoints require auth. Friendships are stored as symmetric directional
rows; deleting writes a `friend_removed` notification delivered piggyback on
the recipient's next report (PRD §6).
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import BEIJING_TZ, settings
from app.core.data_sources import deserialize, serialize
from app.db.session import get_db
from app.models import (
    FriendDataSource,
    FriendRequest,
    Friendship,
    Notification,
    QrToken,
    User,
)
from app.models import Poke
from app.schemas.friends import (
    AddByQrCodeRequest,
    DataSourcesOut,
    DataSourcesUpdate,
    FriendOut,
    FriendRequestCreate,
    FriendRequestOut,
    FriendsListResponse,
    NicknameUpdate,
    NotificationOut,
    PokeStatsResponse,
    QrCodeResponse,
    SearchUserOut,
)
from app.schemas.auth import MessageResponse
from app.schemas.friends import FriendActivityItem
from app.services.activity import visible_to_user
from app.services.notifications import (
    create_notification,
    fetch_and_mark_delivered,
    friend_removed_payload,
    to_payload_dicts,
)

router = APIRouter(prefix="/friends", tags=["friends"])


# --- helpers ---------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(BEIJING_TZ)


def _create_mutual_friendship(db: Session, a_id: int, b_id: int) -> None:
    """Insert the two symmetric friendship rows (idempotent if already friends)."""
    for owner, friend in ((a_id, b_id), (b_id, a_id)):
        exists = db.scalar(
            select(Friendship).where(
                Friendship.user_id == owner, Friendship.friend_id == friend
            )
        )
        if exists is None:
            db.add(Friendship(user_id=owner, friend_id=friend, status="accepted"))
    db.commit()


def _are_friends(db: Session, a_id: int, b_id: int) -> bool:
    return (
        db.scalar(
            select(Friendship).where(
                Friendship.user_id == a_id, Friendship.friend_id == b_id
            )
        )
        is not None
    )


# --- QR code add (no verification) ----------------------------------------

@router.post("/qrcode", response_model=QrCodeResponse)
def create_qrcode(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> QrCodeResponse:
    token = secrets.token_urlsafe(32)
    expire_at = _now() + timedelta(minutes=settings.qr_token_expire_minutes)
    row = QrToken(owner_user_id=user.id, token=token, expire_at=expire_at, used=False)
    db.add(row)
    db.commit()
    db.refresh(row)
    return QrCodeResponse(token=row.token, expire_at=row.expire_at)


@router.post("/add-by-qrcode", response_model=MessageResponse)
def add_by_qrcode(
    body: AddByQrCodeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    row = db.scalar(select(QrToken).where(QrToken.token == body.token))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="二维码不存在")
    if row.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="二维码已使用")
    if row.expire_at.replace(tzinfo=BEIJING_TZ) < _now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="二维码已过期")
    if row.owner_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能添加自己为好友")

    if _are_friends(db, user.id, row.owner_user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你们已经是好友")

    _create_mutual_friendship(db, user.id, row.owner_user_id)
    row.used = True
    db.commit()
    return MessageResponse(message="添加好友成功")


# --- email search ----------------------------------------------------------

@router.get("/search", response_model=list[SearchUserOut])
def search_by_email(
    email: str = Query(min_length=3, max_length=255),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SearchUserOut]:
    target = db.scalar(select(User).where(User.email == email))
    if target is None or target.id == user.id:
        return []
    return [SearchUserOut.model_validate(target)]


# --- friend requests (email-search path, needs acceptance) ----------------

@router.post("/request", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    body: FriendRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if body.to_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能向自己发送好友申请")

    target = db.get(User, body.to_user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="目标用户不存在")
    if _are_friends(db, user.id, body.to_user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="你们已经是好友")

    existing = db.scalar(
        select(FriendRequest).where(
            FriendRequest.from_user_id == user.id,
            FriendRequest.to_user_id == body.to_user_id,
            FriendRequest.status == "pending",
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已存在待处理的好友申请")

    req = FriendRequest(from_user_id=user.id, to_user_id=body.to_user_id, status="pending")
    db.add(req)
    db.commit()
    return MessageResponse(message="好友申请已发送")


@router.get("/requests", response_model=list[FriendRequestOut])
def list_requests(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FriendRequestOut]:
    """Return incoming friend requests for the current user (sent to me)."""
    rows = db.scalars(
        select(FriendRequest)
        .where(
            FriendRequest.to_user_id == user.id,
            FriendRequest.status == "pending",
        )
        .order_by(FriendRequest.created_at.desc())
    )
    result: list[FriendRequestOut] = []
    for r in rows:
        from_user = db.get(User, r.from_user_id)
        out = FriendRequestOut.model_validate(r)
        if from_user:
            out.from_email = from_user.email
            out.from_nickname = from_user.nickname
        result.append(out)
    return result


def _get_pending_request(db: Session, req_id: int, user_id: int) -> FriendRequest:
    req = db.get(FriendRequest, req_id)
    if req is None or req.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="好友申请不存在或已处理")
    if req.to_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理该申请")
    return req


@router.post("/requests/{req_id}/accept", response_model=MessageResponse)
def accept_request(
    req_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    req = _get_pending_request(db, req_id, user.id)
    req.status = "accepted"
    _create_mutual_friendship(db, req.from_user_id, req.to_user_id)
    db.commit()
    return MessageResponse(message="已接受好友申请")


@router.post("/requests/{req_id}/reject", response_model=MessageResponse)
def reject_request(
    req_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    req = _get_pending_request(db, req_id, user.id)
    req.status = "rejected"
    db.commit()
    return MessageResponse(message="已拒绝好友申请")


# --- friend list / nickname / delete --------------------------------------

def _friend_out(db: Session, me_id: int, fs: Friendship) -> FriendOut:
    friend = db.get(User, fs.friend_id)
    return FriendOut(
        friendship_id=fs.id,
        friend_id=fs.friend_id,
        email=friend.email,
        nickname=fs.nickname,
        friend_nickname=friend.nickname,
        created_at=fs.created_at,
    )


@router.get("", response_model=FriendsListResponse)
def list_friends(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FriendsListResponse:
    rows = db.scalars(
        select(Friendship).where(Friendship.user_id == user.id).order_by(Friendship.created_at.desc())
    )
    friends = [_friend_out(db, user.id, fs) for fs in rows]
    # Piggyback undelivered notifications so the list view can surface them.
    notifs = fetch_and_mark_delivered(db, user.id)
    # Include each friend's visible activity + poke data in the response.
    # Always create an entry for every friend, even without activity reports,
    # so the frontend always gets poke timestamps.
    latest_pokes = db.execute(
        select(Poke.from_user_id, func.max(Poke.created_at).label("last_poked_at"))
        .where(Poke.to_user_id == user.id)
        .group_by(Poke.from_user_id)
    ).all()
    poke_map = {row.from_user_id: row.last_poked_at for row in latest_pokes}

    # visible_to_user returns ActivityReport rows where friend_id == viewer_id.
    # These have: user_id = friend (data owner), friend_id = viewer.
    activity_map = {r.user_id: r for r in visible_to_user(db, user.id)}

    friends_activity = []
    for f in friends:
        ar = activity_map.get(f.friend_id)
        friends_activity.append(
            FriendActivityItem(
                friend_id=f.friend_id,
                value=ar.value if ar else 0,
                last_reported_at=ar.last_reported_at if ar else None,
                is_offline=ar.is_offline if ar else True,
                last_poked_at=poke_map.get(f.friend_id),
            )
        )

    return FriendsListResponse(
        friends=friends,
        notifications=[NotificationOut(**n) for n in to_payload_dicts(notifs)],
        friends_activity=friends_activity,
    )


def _get_my_friendship(db: Session, me_id: int, friendship_id: int) -> Friendship:
    fs = db.get(Friendship, friendship_id)
    if fs is None or fs.user_id != me_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="好友关系不存在")
    return fs


@router.get("/{friendship_id}/poke-stats", response_model=PokeStatsResponse)
def friend_poke_stats(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PokeStatsResponse:
    """Return how many times this friend has poked me, plus the last 2 timestamps."""
    fs = _get_my_friendship(db, user.id, friendship_id)
    friend_id = fs.friend_id

    from sqlalchemy import func as sa_func

    count = db.scalar(
        select(sa_func.count(Poke.id)).where(
            Poke.from_user_id == friend_id, Poke.to_user_id == user.id
        )
    )
    recent = list(
        db.scalars(
            select(Poke.created_at)
            .where(Poke.from_user_id == friend_id, Poke.to_user_id == user.id)
            .order_by(Poke.created_at.desc())
            .limit(2)
        )
    )
    return PokeStatsResponse(total_pokes=count or 0, recent_pokes=recent)


@router.patch("/{friendship_id}/nickname", response_model=MessageResponse)
def update_nickname(
    friendship_id: int,
    body: NicknameUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    fs = _get_my_friendship(db, user.id, friendship_id)
    fs.nickname = body.nickname
    db.commit()
    return MessageResponse(message="昵称已更新")


@router.delete("/{friendship_id}", response_model=MessageResponse)
def delete_friend(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    fs = _get_my_friendship(db, user.id, friendship_id)
    friend_id = fs.friend_id

    # Remove both symmetric rows.
    db.query(Friendship).filter(
        ((Friendship.user_id == user.id) & (Friendship.friend_id == friend_id))
        | ((Friendship.user_id == friend_id) & (Friendship.friend_id == user.id))
    ).delete(synchronize_session=False)

    # Notify the removed friend (delivered on their next report).
    friend = db.get(User, friend_id)
    if friend is not None:
        create_notification(
            db,
            user_id=friend_id,
            type_="friend_removed",
            payload=friend_removed_payload(user.id, user.email),
        )
    db.commit()
    return MessageResponse(message="已删除好友")


# --- per-friend data-source matrix (PRD §4.2) -----------------------------

def _get_or_create_fds(db: Session, me_id: int, friend_id: int) -> FriendDataSource:
    row = db.scalar(
        select(FriendDataSource).where(
            FriendDataSource.user_id == me_id, FriendDataSource.friend_id == friend_id
        )
    )
    if row is None:
        row = FriendDataSource(user_id=me_id, friend_id=friend_id, allowed_sources="")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/{friendship_id}/data-sources", response_model=DataSourcesOut)
def get_data_sources(
    friendship_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataSourcesOut:
    fs = _get_my_friendship(db, user.id, friendship_id)
    row = _get_or_create_fds(db, user.id, fs.friend_id)
    return DataSourcesOut(friend_id=fs.friend_id, allowed_sources=deserialize(row.allowed_sources))


@router.put("/{friendship_id}/data-sources", response_model=DataSourcesOut)
def set_data_sources(
    friendship_id: int,
    body: DataSourcesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataSourcesOut:
    if len(body.allowed_sources) > settings.max_data_sources_per_friend:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据源最多 {settings.max_data_sources_per_friend} 个",
        )
    invalid = [s for s in body.allowed_sources if s not in (
        "steps", "screen_unlock", "charging", "headset", "pickup_flip", "ambient_light", "significant_motion"
    )]
    if invalid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"非法数据源: {invalid}")

    fs = _get_my_friendship(db, user.id, friendship_id)
    row = _get_or_create_fds(db, user.id, fs.friend_id)
    row.allowed_sources = serialize(body.allowed_sources)
    db.commit()
    db.refresh(row)
    return DataSourcesOut(friend_id=fs.friend_id, allowed_sources=deserialize(row.allowed_sources))


# --- pending notifications (consumed by future /activity/report, M3) ------

@router.get("/notifications", response_model=list[NotificationOut])
def my_notifications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[NotificationOut]:
    rows = fetch_and_mark_delivered(db, user.id)
    return [NotificationOut(**n) for n in to_payload_dicts(rows)]
