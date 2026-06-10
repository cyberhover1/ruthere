"""
Initialize demo data: real users + simulated virtual friends with pre-built friendships.
Run once before starting the server:  python init_demo.py
"""
import asyncio
import random
import datetime
from app.database import init_db, async_session
from app.models import User, Friendship
from app.auth import hash_password


async def init_demo():
    await init_db()
    async with async_session() as db:
        # Check if data already exists
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(User))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} users, skipping init. Delete activity.db to re-init.")
            return

        # ── Real users ──────────────────────────────────────────────────────
        users_data = [
            ("admin", "admin123", False),
            ("alice", "alice123", False),
            ("bob", "bob123", False),
            ("carol", "carol123", False),
        ]
        real_users = []
        for username, pw, sim in users_data:
            u = User(
                username=username,
                password_hash=hash_password(pw),
                activity_score=random.randint(0, 100),
                is_online=True,
                is_simulated=sim,
                last_heartbeat=datetime.datetime.utcnow(),
            )
            db.add(u)
            await db.flush()
            real_users.append(u)

        # ── Virtual / Simulated users ───────────────────────────────────────
        virtual_names = ["dave", "eve", "frank", "grace", "hank", "iris", "jack", "kate"]
        virtual_users = []
        for name in virtual_names:
            u = User(
                username=name,
                password_hash=hash_password(f"{name}123"),
                activity_score=random.randint(0, 100),
                is_online=True,
                is_simulated=True,
                last_heartbeat=datetime.datetime.utcnow(),
            )
            db.add(u)
            await db.flush()
            virtual_users.append(u)

        await db.commit()
        print(f"Created {len(real_users)} real users + {len(virtual_users)} virtual users")

        # ── Friendships (unidirectional) ────────────────────────────────────
        # admin -> alice, bob, carol, dave, eve
        admin = real_users[0]
        for target in real_users[1:] + virtual_users[:2]:
            db.add(Friendship(follower_id=admin.id, followee_id=target.id))

        # alice -> bob, carol, dave, eve
        alice = real_users[1]
        for target in real_users[2:] + [virtual_users[0], virtual_users[1]]:
            db.add(Friendship(follower_id=alice.id, followee_id=target.id))

        # bob -> alice, carol, frank, grace
        bob = real_users[2]
        for target in [real_users[1], real_users[3], virtual_users[2], virtual_users[3]]:
            db.add(Friendship(follower_id=bob.id, followee_id=target.id))

        # carol -> alice, bob, hank, iris
        carol = real_users[3]
        for target in [real_users[1], real_users[2], virtual_users[4], virtual_users[5]]:
            db.add(Friendship(follower_id=carol.id, followee_id=target.id))

        # Some virtual users also follow each other (for demo richness)
        db.add(Friendship(follower_id=virtual_users[0].id, followee_id=virtual_users[1].id))
        db.add(Friendship(follower_id=virtual_users[2].id, followee_id=virtual_users[3].id))
        db.add(Friendship(follower_id=virtual_users[4].id, followee_id=virtual_users[5].id))

        await db.commit()
        print("Friendships created")

        # ── Summary ─────────────────────────────────────────────────────────
        print(f"\nDemo users:")
        print(f"  admin/admin123 — administrator (all friends)")
        print(f"  alice/alice123 — follows bob, carol, dave, eve")
        print(f"  bob/bob123     — follows alice, carol, frank, grace")
        print(f"  carol/carol123 — follows alice, bob, hank, iris")
        print(f"\n  Virtual users: {', '.join(virtual_names)} (auto-simulated activity)")
        print(f"\n  Admin page: http://127.0.0.1:8000/admin")
        print(f"  API base:   http://127.0.0.1:8000")


if __name__ == "__main__":
    asyncio.run(init_demo())
    print("Done.")