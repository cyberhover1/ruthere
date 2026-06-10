import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
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


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)