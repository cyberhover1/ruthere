import datetime
import logging
import re
import asyncio
from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, init_db
from app.models import User, Friendship, FriendRequest, FriendRequestStatus, ActivityLog
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token, decode_refresh_token, get_current_user
from app.tasks import check_heartbeats, simulate_virtual_activities, push_activities_to_friends, decay_activity_scores

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
logger = logging.getLogger("codewhale")

# ── China mobile phone regex ────────────────────────────────────────────────
CHINA_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")

# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    phone: str = Field(...)
    nickname: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)

class LoginRequest(BaseModel):
    phone: str
    password: str

class ActivityReport(BaseModel):
    increment: int = Field(..., ge=1, le=100)

class FriendAction(BaseModel):
    phone: str

class FriendRequestAction(BaseModel):
    receiver_phone: str

class RefreshRequest(BaseModel):
    refresh_token: str

# ── App ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_heartbeats, "interval", seconds=30, id="check_hb", replace_existing=True)
    scheduler.add_job(simulate_virtual_activities, "interval", seconds=60, id="sim_act", replace_existing=True)
    scheduler.add_job(push_activities_to_friends, "interval", seconds=60, id="push_act", replace_existing=True)
    # Vitality decay: -1 every 5 seconds
    scheduler.add_job(decay_activity_scores, "interval", seconds=5, id="decay_vitality", replace_existing=True)
    scheduler.start()
    logger.info("Background scheduler started")
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="RuThere API", version="1.1.0", lifespan=lifespan)

# ── Helper ────────────────────────────────────────────────────────────────────

def _validate_china_phone(phone: str) -> None:
    if not CHINA_PHONE_RE.match(phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确，需为11位中国手机号")

def _token_response(user: User):
    """Build response with both access and refresh tokens."""
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user_id": user.id,
        "nickname": user.nickname,
        "phone": user.phone,
    }

# ── Public Auth Endpoints ────────────────────────────────────────────────────

@app.post("/api/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    _validate_china_phone(req.phone)

    result = await db.execute(select(User).where(User.phone == req.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        phone=req.phone,
        nickname=req.nickname,
        username=req.phone,
        password_hash=hash_password(req.password),
        activity_score=100,          # new user starts at 100
        is_online=True,
        last_heartbeat=datetime.datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _token_response(user)


@app.post("/api/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    user.is_online = True
    user.last_heartbeat = datetime.datetime.utcnow()
    user.activity_score = 100          # login resets vitality to 100
    await db.commit()
    return _token_response(user)


@app.post("/api/refresh")
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token + refresh token."""
    user_id = decode_refresh_token(req.refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return _token_response(user)


# ── Authenticated Mobile Endpoints ───────────────────────────────────────────

@app.post("/api/logout")
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Logout — mark user offline and clear activity score."""
    user.is_online = False
    user.activity_score = 0
    await db.commit()
    return {"status": "ok"}


@app.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "phone": user.phone,
        "nickname": user.nickname,
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
    """Report a vitality increment.

    Formula: new_score = max(100, current_score + increment)
    The background decay task subtracts 1 every 5 seconds.
    """
    if user.is_simulated:
        raise HTTPException(status_code=403, detail="Simulated users cannot report activity")
    user.activity_score = min(100, user.activity_score + req.increment)
    user.is_online = True
    user.last_heartbeat = datetime.datetime.utcnow()
    log = ActivityLog(user_id=user.id, score=user.activity_score)
    db.add(log)
    await db.commit()
    return {"status": "ok", "activity_score": user.activity_score}


# ── Friends Activity ─────────────────────────────────────────────────────────

@app.get("/api/friends/activity")
async def get_friends_activity(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull all mutual friends' current activity."""
    result = await db.execute(
        select(User).join(Friendship, Friendship.followee_id == User.id).where(
            Friendship.follower_id == user.id
        )
    )
    friends = result.scalars().all()
    return {
        "friends": [
            {
                "nickname": f.nickname,
                "phone": f.phone,
                "activity_score": f.activity_score if f.is_online else 0,
                "is_online": f.is_online,
                "is_simulated": f.is_simulated,
            }
            for f in friends
        ]
    }


# ── Friend Request System ────────────────────────────────────────────────────

@app.post("/api/friends/search-by-phone")
async def search_by_phone(
    req: FriendAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search a user by phone number."""
    _validate_china_phone(req.phone)
    result = await db.execute(select(User).where(User.phone == req.phone))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="未找到该手机号的用户")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = await db.execute(
        select(Friendship).where(
            Friendship.follower_id == user.id,
            Friendship.followee_id == target.id,
        )
    )
    already_friends = existing.scalar_one_or_none() is not None

    pending_req = await db.execute(
        select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == user.id,
                    FriendRequest.receiver_id == target.id,
                    FriendRequest.status == FriendRequestStatus.pending,
                ),
                and_(
                    FriendRequest.sender_id == target.id,
                    FriendRequest.receiver_id == user.id,
                    FriendRequest.status == FriendRequestStatus.pending,
                ),
            )
        )
    )
    has_pending = pending_req.scalar_one_or_none() is not None

    return {
        "user_id": target.id,
        "phone": target.phone,
        "nickname": target.nickname,
        "is_online": target.is_online,
        "already_friends": already_friends,
        "has_pending_request": has_pending,
    }


@app.post("/api/friends/request")
async def send_friend_request(
    req: FriendRequestAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_china_phone(req.receiver_phone)
    result = await db.execute(select(User).where(User.phone == req.receiver_phone))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="未找到该手机号的用户")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")

    existing = await db.execute(
        select(Friendship).where(
            Friendship.follower_id == user.id,
            Friendship.followee_id == target.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已经是好友了")

    pending_req = await db.execute(
        select(FriendRequest).where(
            or_(
                and_(
                    FriendRequest.sender_id == user.id,
                    FriendRequest.receiver_id == target.id,
                    FriendRequest.status == FriendRequestStatus.pending,
                ),
                and_(
                    FriendRequest.sender_id == target.id,
                    FriendRequest.receiver_id == user.id,
                    FriendRequest.status == FriendRequestStatus.pending,
                ),
            )
        )
    )
    if pending_req.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已有一个待处理的好友请求")

    fr = FriendRequest(
        sender_id=user.id,
        receiver_id=target.id,
        status=FriendRequestStatus.pending,
    )
    db.add(fr)
    await db.commit()
    await db.refresh(fr)
    return {"status": "ok", "request_id": fr.id, "receiver_nickname": target.nickname}


@app.get("/api/friends/requests")
async def list_friend_requests(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.receiver_id == user.id,
            FriendRequest.status == FriendRequestStatus.pending,
        ).order_by(FriendRequest.created_at.desc())
    )
    requests = result.scalars().all()

    items = []
    for fr in requests:
        sender = await db.execute(select(User).where(User.id == fr.sender_id))
        sender_user = sender.scalar_one()
        items.append({
            "request_id": fr.id,
            "sender_id": fr.sender_id,
            "sender_nickname": sender_user.nickname,
            "sender_phone": sender_user.phone,
            "created_at": fr.created_at.isoformat() if fr.created_at else None,
        })

    return {"requests": items}


@app.post("/api/friends/requests/{request_id}/accept")
async def accept_friend_request(
    request_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.id == request_id,
            FriendRequest.receiver_id == user.id,
            FriendRequest.status == FriendRequestStatus.pending,
        )
    )
    fr = result.scalar_one_or_none()
    if not fr:
        raise HTTPException(status_code=404, detail="好友请求不存在或已被处理")

    sender_result = await db.execute(select(User).where(User.id == fr.sender_id))
    sender = sender_result.scalar_one_or_none()

    fs1 = Friendship(follower_id=fr.sender_id, followee_id=fr.receiver_id)
    fs2 = Friendship(follower_id=fr.receiver_id, followee_id=fr.sender_id)
    db.add(fs1)
    db.add(fs2)

    fr.status = FriendRequestStatus.accepted
    fr.updated_at = datetime.datetime.utcnow()

    await db.commit()
    return {"status": "ok", "sender_nickname": sender.nickname if sender else ""}


@app.post("/api/friends/requests/{request_id}/reject")
async def reject_friend_request(
    request_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FriendRequest).where(
            FriendRequest.id == request_id,
            FriendRequest.receiver_id == user.id,
            FriendRequest.status == FriendRequestStatus.pending,
        )
    )
    fr = result.scalar_one_or_none()
    if not fr:
        raise HTTPException(status_code=404, detail="好友请求不存在或已被处理")

    fr.status = FriendRequestStatus.rejected
    fr.updated_at = datetime.datetime.utcnow()
    await db.commit()
    return {"status": "ok"}


# ── Friend Management ────────────────────────────────────────────────────────

@app.post("/api/friends/add")
async def add_friend_by_phone(
    req: FriendAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_china_phone(req.phone)
    result = await db.execute(select(User).where(User.phone == req.phone))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="不能添加自己为好友")
    existing = await db.execute(
        select(Friendship).where(
            Friendship.follower_id == user.id,
            Friendship.followee_id == target.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已经是好友了")
    fs = Friendship(follower_id=user.id, followee_id=target.id)
    db.add(fs)
    await db.commit()
    return {"status": "ok", "friend_nickname": target.nickname}


@app.post("/api/friends/remove")
async def remove_friend(
    req: FriendAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _validate_china_phone(req.phone)
    result = await db.execute(select(User).where(User.phone == req.phone))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.execute(
        delete(Friendship).where(
            or_(
                and_(
                    Friendship.follower_id == user.id,
                    Friendship.followee_id == target.id,
                ),
                and_(
                    Friendship.follower_id == target.id,
                    Friendship.followee_id == user.id,
                ),
            )
        )
    )
    await db.commit()
    return {"status": "ok", "friend_nickname": target.nickname}


@app.get("/api/users")
async def list_users(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.is_simulated == False).order_by(User.nickname)
    )
    users = result.scalars().all()
    return {
        "users": [
            {
                "user_id": u.id,
                "nickname": u.nickname,
                "phone": u.phone,
                "is_online": u.is_online,
            }
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
    phone: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    token = create_access_token(user.id)
    return {"access_token": token, "nickname": user.nickname}


@app.get("/admin/data", response_class=JSONResponse)
async def admin_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    user_list = []
    for u in users:
        friend_count = await db.execute(
            select(Friendship).where(Friendship.follower_id == u.id)
        )
        user_list.append({
            "id": u.id,
            "nickname": u.nickname,
            "phone": u.phone,
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