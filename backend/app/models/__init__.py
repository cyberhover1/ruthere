"""ORM models.

Importing every model here lets Alembic's `target_metadata = Base.metadata`
discover them, and lets call sites do `from app.models import User, ...`.
"""

from app.db.base import Base
from app.models.device import Device
from app.models.friend_data_source import FriendDataSource
from app.models.friend_request import FriendRequest
from app.models.friendship import Friendship
from app.models.notification import Notification
from app.models.qr_token import QrToken
from app.models.user import User
from app.models.verification_code import EmailCode

__all__ = [
    "Base",
    "User",
    "Device",
    "EmailCode",
    "Friendship",
    "FriendRequest",
    "QrToken",
    "FriendDataSource",
    "Notification",
]
