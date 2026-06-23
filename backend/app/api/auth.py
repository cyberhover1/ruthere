"""Authentication routes: register / resend-code / verify / login / logout / me."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_device, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Device, EmailCode, User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendCodeRequest,
    TokenResponse,
    UserOut,
    VerifyRequest,
)
from app.services.activity import reset_activity_for_user
from app.services.email import EmailSendError, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_code() -> str:
    """Zero-padded numeric code of the configured length."""
    bound = 10 ** settings.email_code_length
    return str(secrets.randbelow(bound)).zfill(settings.email_code_length)


def _new_code_row(db: Session, email: str) -> EmailCode:
    """Create + persist a fresh verification code for `email`."""
    code = _generate_code()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.email_code_expire_minutes)
    row = EmailCode(email=email, code=code, expire_at=expire_at, used=False)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _latest_code(db: Session, email: str) -> EmailCode | None:
    return db.scalar(
        select(EmailCode).where(EmailCode.email == email).order_by(EmailCode.created_at.desc())
    )


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> MessageResponse:
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册")

    user = User(email=body.email, password_hash=hash_password(body.password), is_verified=False)
    db.add(user)
    db.commit()

    code_row = _new_code_row(db, body.email)
    try:
        send_verification_email(body.email, code_row.code)
    except EmailSendError as e:
        # Roll back the user + code so they can retry registration cleanly.
        db.delete(code_row)
        db.delete(user)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return MessageResponse(message="注册成功，验证码已发送至邮箱")


@router.post("/resend-code", response_model=MessageResponse)
def resend_code(body: ResendCodeRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该邮箱未注册")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已验证")

    latest = _latest_code(db, body.email)
    if latest is not None:
        elapsed = (datetime.now(timezone.utc) - latest.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        if elapsed < settings.resend_cooldown_seconds:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请稍后再试（{settings.resend_cooldown_seconds}秒内不可重复发送）",
            )

    code_row = _new_code_row(db, body.email)
    try:
        send_verification_email(body.email, code_row.code)
    except EmailSendError as e:
        db.delete(code_row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return MessageResponse(message="验证码已重新发送")


@router.post("/verify", response_model=MessageResponse)
def verify(body: VerifyRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该邮箱未注册")

    code_row = db.scalar(
        select(EmailCode)
        .where(EmailCode.email == body.email, EmailCode.code == body.code)
        .order_by(EmailCode.created_at.desc())
    )
    if code_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误")
    if code_row.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已使用")
    if code_row.expire_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码已过期")

    code_row.used = True
    user.is_verified = True
    db.commit()
    return MessageResponse(message="邮箱验证成功")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="邮箱未验证，请先完成验证"
        )

    # Single-device login: deactivate all of this user's prior devices, then open a new session.
    db.query(Device).filter(Device.user_id == user.id, Device.is_active.is_(True)).update(
        {Device.is_active: False}, synchronize_session=False
    )
    device = Device(user_id=user.id, device_identifier=body.device_identifier, is_active=True)
    db.add(device)
    db.commit()
    db.refresh(device)

    reset_activity_for_user(user.id, db)  # placeholder; real logic in M3
    token = create_access_token(user.id, device.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.post("/logout", response_model=MessageResponse)
def logout(
    device: Device = Depends(get_current_device), db: Session = Depends(get_db)
) -> MessageResponse:
    device.is_active = False
    db.commit()
    return MessageResponse(message="已退出登录")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
