import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class FriendRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # phone is the login identifier — unique, China mobile format
    phone = Column(String(11), unique=True, index=True, nullable=False)
    # nickname for display
    nickname = Column(String(50), nullable=False)
    # keep username as fallback / admin, but login uses phone
    username = Column(String(50), unique=True, index=True, nullable=True)
    password_hash = Column(String(128), nullable=False)
    activity_score = Column(Integer, default=0)
    is_online = Column(Boolean, default=False)
    is_simulated = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime, default=None, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # relationships
    friendships = relationship(
        "Friendship",
        foreign_keys="Friendship.follower_id",
        back_populates="follower",
        lazy="selectin",
    )


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    followee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    follower = relationship("User", foreign_keys=[follower_id], back_populates="friendships")


class FriendRequest(Base):
    """Bidirectional friend request system.

    When user A wants to add user B as a friend, A sends a request.
    If B accepts, the two become mutual friends (two Friendship rows).
    """
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(FriendRequestStatus), default=FriendRequestStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=None, nullable=True)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)