"""Friend-related request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import MessageResponse  # reuse


class QrCodeResponse(BaseModel):
    token: str
    expire_at: datetime


class AddByQrCodeRequest(BaseModel):
    token: str = Field(min_length=1, max_length=128)


class SearchUserOut(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class FriendRequestCreate(BaseModel):
    to_user_id: int


class FriendRequestOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str
    created_at: datetime
    from_email: str = ""
    from_nickname: str | None = None

    model_config = {"from_attributes": True}


class FriendOut(BaseModel):
    """A friend as seen from the current user's list."""

    friendship_id: int  # the row in friendships (user_id=me, friend_id=them)
    friend_id: int
    email: EmailStr
    nickname: str | None       # per-friendship nickname (what I call them)
    friend_nickname: str | None = None  # the friend's own nickname (from User)
    created_at: datetime

    model_config = {"from_attributes": True}


class PokeStatsResponse(BaseModel):
    """Poke statistics from a friend toward me."""

    total_pokes: int = 0
    recent_pokes: list[datetime] = Field(default_factory=list)


class NicknameUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)


class DataSourcesOut(BaseModel):
    friend_id: int
    allowed_sources: list[str]


class DataSourcesUpdate(BaseModel):
    allowed_sources: list[str] = Field(default_factory=list)


class NotificationOut(BaseModel):
    id: int
    type: str
    payload: dict
    created_at: datetime


class FriendActivityItem(BaseModel):
    """A friend's activity as seen by me (duplicated from activity.py to avoid circular imports)."""

    friend_id: int
    value: int = 0
    last_reported_at: datetime | None = None
    is_offline: bool = False
    last_poked_at: datetime | None = None


class FriendsListResponse(BaseModel):
    friends: list[FriendOut]
    notifications: list[NotificationOut] = Field(default_factory=list)
    friends_activity: list[FriendActivityItem] = Field(default_factory=list)
