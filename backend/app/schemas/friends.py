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

    model_config = {"from_attributes": True}


class FriendOut(BaseModel):
    """A friend as seen from the current user's list."""

    friendship_id: int  # the row in friendships (user_id=me, friend_id=them)
    friend_id: int
    email: EmailStr
    nickname: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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


class FriendsListResponse(BaseModel):
    friends: list[FriendOut]
    notifications: list[NotificationOut] = Field(default_factory=list)
