from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

import logging

logger = logging.getLogger("codewhale")

DATABASE_URL = "sqlite+aiosqlite:///./activity.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    """Initialize database — create tables if missing, upgrade if needed.

    SQLite's ``create_all`` does *not* add columns to existing tables, so on
    schema changes the old DB must be dropped.  We detect old-schema tables
    by trying to select a known-new column and force a recreation if it is
    missing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # ── Detect stale schema ────────────────────────────────────────────
        # Check whether the ``phone`` column exists.  If it doesn't, the
        # DB was created by an older version — drop the whole thing and
        # recreate with the current metadata.
        try:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT phone FROM users LIMIT 1"))
            result.close()
            logger.info("Database schema is up-to-date")
        except Exception:
            logger.warning("Old database schema detected — dropping and recreating")
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema recreated")