"""FastAPI dependencies: DB session + current user/device.

`get_current_user` decodes the Bearer token AND confirms the bound device
session is still active — that is what enforces single-device login (a kicked
device's token is rejected here even though the JWT itself hasn't expired).
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import JWTError, decode_token
from app.db.session import get_db
from app.models import Device, User

bearer_scheme = HTTPBearer(auto_error=True)


def _resolve_device(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> tuple[User, Device]:
    """Decode the token and return (user, active_device). Raises 401 on any issue."""
    cred_err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或已过期的登录凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise cred_err

    user_id = int(payload.get("sub", 0))
    device_id = int(payload.get("device_id", 0))

    device = db.get(Device, device_id)
    if device is None or not device.is_active or device.user_id != user_id:
        raise cred_err

    user = db.get(User, user_id)
    if user is None:
        raise cred_err
    return user, device


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user, _ = _resolve_device(credentials, db)
    return user


def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Device:
    """Return the active device row backing the current token (for logout)."""
    _, device = _resolve_device(credentials, db)
    return device
