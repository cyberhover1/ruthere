"""APScheduler wrapper for activity decay + offline scan (PRD §4.4).

A BackgroundScheduler runs two interval jobs:
  - decay: every decay_interval_minutes, linearly decay activity values
  - offline: every hour, mark stale rows offline

Started/stopped from the FastAPI lifespan. Tests call decay_all / mark_offline
directly and do NOT start the scheduler.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.activity import decay_all, mark_offline

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_decay() -> None:
    db = SessionLocal()
    try:
        changed = decay_all(db)
        if changed:
            logger.info("decay: updated %d activity rows", changed)
    except Exception:
        logger.exception("decay job failed")
    finally:
        db.close()


def _run_offline_scan() -> None:
    db = SessionLocal()
    try:
        marked = mark_offline(db)
        if marked:
            logger.info("offline scan: marked %d rows offline", marked)
    except Exception:
        logger.exception("offline scan job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start the background scheduler with decay + offline jobs."""
    global _scheduler
    if _scheduler is not None:
        return
    sched = BackgroundScheduler(timezone="Asia/Shanghai")
    sched.add_job(
        _run_decay,
        "interval",
        minutes=settings.decay_interval_minutes,
        id="activity_decay",
        replace_existing=True,
    )
    sched.add_job(
        _run_offline_scan,
        "interval",
        hours=1,
        id="offline_scan",
        replace_existing=True,
    )
    sched.start()
    _scheduler = sched
    logger.info("scheduler started (decay every %dm, offline every 1h)", settings.decay_interval_minutes)


def stop_scheduler() -> None:
    """Shutdown the scheduler gracefully (waits for running jobs)."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("scheduler stopped")
