"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)


class ResendCodeRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_identifier: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserOut(BaseModel):
    id: int
    email: EmailStr
    nickname: str | None = None
    is_verified: bool

    model_config = {"from_attributes": True}


class NicknameUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)


class MessageResponse(BaseModel):
    message: str
