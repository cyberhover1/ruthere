import datetime
import logging
import asyncio
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.models import User, Friendship, ActivityLog
from app.auth import hash_password, verify_password, create_token, get_current_user
from app.tasks import check_heartbeats, simulate_virtual_activities, push_activities_to_friends

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
logger = logging.getLogger("codewhale")

# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)

class LoginRequest(BaseModel):
    username: str
    password: str

class ActivityReport(BaseModel):
    score: int = Field(..., ge=0, le=100)

class FriendAction(BaseModel):
    username: str

# ── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    # Start background scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_heartbeats, "interval", seconds=30, id="check_hb", replace_existing=True)
    scheduler.add_job(simulate_virtual_activities, "interval", seconds=60, id="sim_act", replace_existing=True)
    scheduler.add_job(push_activities_to_friends, "interval", seconds=60, id="push_act", replace_existing=True)
    scheduler.start()
    logger.info("Background scheduler started")
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="User Activity Demo", version="1.0.0", lifespan=lifespan)

# ── Public Auth Endpoints ────────────────────────────────────────────────────

@app.post("/api/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        is_online=True,
        last_heartbeat=datetime.datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    token = create_token(user.id)
    return {"token": token, "user_id": user.id, "username": user.username}


@app.post("/api/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Mark online on login
    user.is_online = True
    user.last_heartbeat = datetime.datetime.utcnow()
    await db.commit()
    token = create_token(user.id)
    return {"token": token, "user_id": user.id, "username": user.username}

# ── Authenticated Mobile Endpoints ───────────────────────────────────────────

@app.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "username": user.username,
        "activity_score": user.activity_score,
        "is_online": user.is_online,
        "is_simulated": user.is_simulated,
    }


@app.post("/api/heartbeat")
async def heartbeat(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.is_online = True
    user.last_heartbeat = datetime.datetime.utcnow()
    await db.commit()
    return {"status": "ok", "timestamp": user.last_heartbeat.isoformat()}


@app.post("/api/activity")
async def report_activity(
    req: ActivityReport,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.is_simulated:
        raise HTTPException(status_code=403, detail="Simulated users cannot report activity")
    user.activity_score = req.score
    user.is_online = True
    user.last_heartbeat = datetime.datetime.utcnow()
    log = ActivityLog(user_id=user.id, score=req.score)
    db.add(log)
    await db.commit()
    return {"status": "ok", "score": user.activity_score}


@app.get("/api/friends/activity")
async def get_friends_activity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull all followees' current activity."""
    result = await db.execute(
        select(User).join(Friendship, Friendship.followee_id == User.id).where(
            Friendship.follower_id == user.id
        )
    )
    friends = result.scalars().all()
    return {
        "friends": [
            {
                "username": f.username,
                "activity_score": f.activity_score if f.is_online else 0,
                "is_online": f.is_online,
                "is_simulated": f.is_simulated,
            }
            for f in friends
        ]
    }


@app.post("/api/friends/add")
async def add_friend(
    req: FriendAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == req.username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot friend yourself")
    # Check duplicate
    existing = await db.execute(
        select(Friendship).where(
            Friendship.follower_id == user.id,
            Friendship.followee_id == target.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already friends")
    fs = Friendship(follower_id=user.id, followee_id=target.id)
    db.add(fs)
    await db.commit()
    return {"status": "ok", "friend": target.username}


@app.post("/api/friends/remove")
async def remove_friend(
    req: FriendAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == req.username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(
        delete(Friendship).where(
            Friendship.follower_id == user.id,
            Friendship.followee_id == target.id,
        )
    )
    await db.commit()
    return {"status": "ok", "friend": target.username}


@app.get("/api/users")
async def list_users(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List all real (non-simulated) users for friend discovery."""
    result = await db.execute(
        select(User).where(User.is_simulated == False).order_by(User.username)
    )
    users = result.scalars().all()
    return {
        "users": [
            {"user_id": u.id, "username": u.username, "is_online": u.is_online}
            for u in users
        ]
    }

# ── Admin Web Page ───────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    html = Path("app/templates/admin.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.post("/admin/login")
async def admin_login(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.id)
    return {"token": token, "username": user.username}


@app.get("/admin/data", response_class=JSONResponse)
async def admin_data(db: AsyncSession = Depends(get_db)):
    """JSON data endpoint for the admin dashboard AJAX refresh."""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    user_list = []
    for u in users:
        friend_count = await db.execute(
            select(Friendship).where(Friendship.follower_id == u.id)
        )
        user_list.append({
            "id": u.id,
            "username": u.username,
            "activity_score": u.activity_score,
            "is_online": u.is_online,
            "is_simulated": u.is_simulated,
            "last_heartbeat": u.last_heartbeat.isoformat() if u.last_heartbeat else None,
            "friend_count": len(friend_count.scalars().all()),
        })
    logs_result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(20)
    )
    logs = logs_result.scalars().all()
    log_list = [
        {"id": l.id, "user_id": l.user_id, "score": l.score, "timestamp": l.timestamp.isoformat()}
        for l in logs
    ]
    return {"users": user_list, "activity_logs": log_list}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat()}