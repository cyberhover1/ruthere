import datetime
import random
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import User, Friendship

logger = logging.getLogger("codewhale.tasks")
HEARTBEAT_TIMEOUT_MINUTES = 3
PUSH_INTERVAL_SECONDS = 3600  # 1 hour


async def check_heartbeats():
    """Mark users offline if no heartbeat within timeout."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
    async with async_session() as db:
        result = await db.execute(
            select(User).where(
                User.is_online == True,
                User.is_simulated == False,
                User.last_heartbeat.isnot(None),
                User.last_heartbeat < cutoff,
            )
        )
        stale_users = result.scalars().all()
        if not stale_users:
            return

        for user in stale_users:
            user.is_online = False
            user.activity_score = 0
            logger.info("User %s (id=%d) went offline (heartbeat timeout)", user.username, user.id)

        await db.commit()


async def simulate_virtual_activities():
    """Assign random activity scores to simulated users."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.is_simulated == True))
        sim_users = result.scalars().all()
        if not sim_users:
            return

        for user in sim_users:
            user.activity_score = random.randint(0, 100)
            user.is_online = True
            user.last_heartbeat = datetime.datetime.utcnow()

        await db.commit()
        logger.info("Simulated activities for %d virtual users", len(sim_users))


async def push_activities_to_friends():
    """
    Push current activity scores to all real users.
    This logs the push event; the actual data is always available via GET /api/friends/activity.
    """
    async with async_session() as db:
        result = await db.execute(select(User).where(User.is_simulated == False))
        real_users = result.scalars().all()

        for user in real_users:
            friends_query = await db.execute(
                select(User).join(Friendship, Friendship.followee_id == User.id).where(
                    Friendship.follower_id == user.id
                )
            )
            friends = friends_query.scalars().all()
            friend_data = [{"username": f.username, "activity_score": f.activity_score, "is_online": f.is_online} for f in friends]
            logger.info(
                "Pushed activity to user=%s (id=%d): %d friends",
                user.username,
                user.id,
                len(friend_data),
            )

        await db.commit()