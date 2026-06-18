"""FastAPI application factory.

Wire every router here. M0 only exposes /health, but the structure is ready
for the M1–M4 routers to be included with a single line each.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # M3 will start APScheduler (decay + offline scan) here.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="安心圈 API",
        description=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    return app


app = create_app()
