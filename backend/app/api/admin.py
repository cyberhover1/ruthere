"""Admin management endpoints — list & delete users.

Protected by a static API key configured via ADMIN_API_KEY in .env.
Requests must carry `Authorization: Bearer <admin_api_key>`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.schemas.admin import AdminMessageResponse, AdminUserOut

router = APIRouter(prefix="/admin", tags=["admin"])

_admin_scheme = HTTPBearer(auto_error=True)


def _verify_admin_key(
    credentials: HTTPAuthorizationCredentials = Depends(_admin_scheme),
) -> None:
    """Reject the request unless the bearer token matches ADMIN_API_KEY."""
    if credentials.credentials != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/users",
    response_model=list[AdminUserOut],
    dependencies=[Depends(_verify_admin_key)],
)
def list_users(db: Session = Depends(get_db)) -> list[AdminUserOut]:
    """Return all registered users."""
    users = db.scalars(select(User).order_by(User.id)).all()
    return [AdminUserOut.model_validate(u) for u in users]


@router.delete(
    "/users/{user_id}",
    response_model=AdminMessageResponse,
    dependencies=[Depends(_verify_admin_key)],
)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> AdminMessageResponse:
    """Delete a user and all their associated data (cascading)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )

    db.delete(user)
    db.commit()
    return AdminMessageResponse(message=f"用户 {user_id} 已删除")