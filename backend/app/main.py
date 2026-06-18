"""FastAPI application factory.

Wire every router here. M0 only exposes /health, but the structure is ready
for the M1–M4 routers to be included with a single line each.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.friends import router as friends_router
from app.api.activity import router as activity_router
from app.api.interactions import router as interactions_router
from app.core.config import settings
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # APScheduler: decay + offline scan (PRD §4.4).
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="安心圈 API",
        description=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(friends_router)
    app.include_router(activity_router)
    app.include_router(interactions_router)
    return app


app = create_app()
