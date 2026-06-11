"""
Initialize demo data: real users with Chinese nicknames.
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
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(User))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} users, skipping init. Delete activity.db to re-init.")
            return

        # ── Real users with Chinese nicknames ──────────────────────────────
        users_data = [
            ("13800001111", "隔壁老王", "laowang123"),
            ("13800002222", "西毒", "xidu123"),
            ("13800003333", "东方不败", "dongfang123"),
            ("13800004444", "南帝", "nandi123"),
            ("13800005555", "北丐", "beigai123"),
        ]
        real_users = []
        for phone, nickname, pw in users_data:
            u = User(
                phone=phone,
                nickname=nickname,
                username=phone,
                password_hash=hash_password(pw),
                activity_score=random.randint(0, 100),
                is_online=True,
                is_simulated=False,
                last_heartbeat=datetime.datetime.utcnow(),
            )
            db.add(u)
            await db.flush()
            real_users.append(u)

        # ── Virtual / Simulated users ──────────────────────────────────────
        virtual_data = [
            ("13900001111", "天山童姥"),
            ("13900002222", "扫地僧"),
            ("13900003333", "风清扬"),
            ("13900004444", "令狐冲"),
            ("13900005555", "张三丰"),
            ("13900006666", "独孤求败"),
            ("13900007777", "叶孤城"),
            ("13900008888", "花满楼"),
        ]
        virtual_users = []
        for phone, nickname in virtual_data:
            u = User(
                phone=phone,
                nickname=nickname,
                username=phone,
                password_hash=hash_password(f"{nickname}123"),
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

        # ── Friendships (bidirectional for mutual friends) ─────────────────
        # 隔壁老王 -> 西毒, 东方不败, 南帝, 北丐, 天山童姥, 扫地僧
        laowang = real_users[0]
        for target in real_users[1:]:
            db.add(Friendship(follower_id=laowang.id, followee_id=target.id))
        for target in virtual_users[:2]:
            db.add(Friendship(follower_id=laowang.id, followee_id=target.id))

        # 西毒 -> 隔壁老王, 东方不败, 南帝, 风清扬, 令狐冲
        xidu = real_users[1]
        for target in [real_users[0], real_users[2], real_users[3]]:
            db.add(Friendship(follower_id=xidu.id, followee_id=target.id))
        for target in [virtual_users[2], virtual_users[3]]:
            db.add(Friendship(follower_id=xidu.id, followee_id=target.id))

        # 东方不败 -> 隔壁老王, 西毒, 北丐, 张三丰, 独孤求败
        dongfang = real_users[2]
        for target in [real_users[0], real_users[1], real_users[4]]:
            db.add(Friendship(follower_id=dongfang.id, followee_id=target.id))
        for target in [virtual_users[4], virtual_users[5]]:
            db.add(Friendship(follower_id=dongfang.id, followee_id=target.id))

        # 南帝 -> 隔壁老王, 西毒, 北丐, 叶孤城, 花满楼
        nandi = real_users[3]
        for target in [real_users[0], real_users[1], real_users[4]]:
            db.add(Friendship(follower_id=nandi.id, followee_id=target.id))
        for target in [virtual_users[6], virtual_users[7]]:
            db.add(Friendship(follower_id=nandi.id, followee_id=target.id))

        # 北丐 -> 隔壁老王, 东方不败, 南帝
        beigai = real_users[4]
        for target in [real_users[0], real_users[2], real_users[3]]:
            db.add(Friendship(follower_id=beigai.id, followee_id=target.id))

        # Some virtual users also follow each other
        db.add(Friendship(follower_id=virtual_users[0].id, followee_id=virtual_users[1].id))
        db.add(Friendship(follower_id=virtual_users[2].id, followee_id=virtual_users[3].id))
        db.add(Friendship(follower_id=virtual_users[4].id, followee_id=virtual_users[5].id))
        db.add(Friendship(follower_id=virtual_users[6].id, followee_id=virtual_users[7].id))

        await db.commit()
        print("Friendships created")

        # ── Summary ─────────────────────────────────────────────────────────
        print(f"\nDemo users (login with phone + password):")
        for u in real_users:
            pw = [d[2] for d in users_data if d[0] == u.phone][0]
            print(f"  {u.phone} / {pw} — {u.nickname}")
        print(f"\n  Virtual users: {', '.join(d[1] for d in virtual_data)} (auto-simulated activity)")
        print(f"\n  Admin page: http://127.0.0.1:8000/admin")
        print(f"  API base:   http://127.0.0.1:8000")


if __name__ == "__main__":
    asyncio.run(init_demo())
    print("Done.")