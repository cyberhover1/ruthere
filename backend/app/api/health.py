"""Health check endpoint."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


_BUILD_TIMESTAMP: str | None = None


def _load_build_timestamp() -> str | None:
    """Read the build timestamp written by the Dockerfile at image-build time."""
    try:
        with open("/app/BUILD_TIMESTAMP") as f:
            raw = f.read().strip()
        if raw:
            return raw
    except (FileNotFoundError, OSError):
        pass
    return None


def _get_build_timestamp() -> str:
    global _BUILD_TIMESTAMP
    if _BUILD_TIMESTAMP is None:
        _BUILD_TIMESTAMP = _load_build_timestamp()
    return _BUILD_TIMESTAMP or "unknown"


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — does not touch the DB. Used by Docker / load balancers."""
    return {
        "status": "ok",
        "build_timestamp": _get_build_timestamp(),
    }
