"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (no Postgres needed) and a
monkeypatched email sender that records calls instead of hitting Resend.
"""

from __future__ import annotations

import os
from collections.abc import Generator

# Force a safe in-process config before any app import happens.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("RESEND_API_KEY", "")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import session as db_session  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.services import email as email_service  # noqa: E402


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """A fresh in-memory SQLite session per test, with all tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient wired to use the per-test SQLite session via dependency override."""

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass  # session lifetime managed by the `db` fixture

    app.dependency_overrides[db_session.get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sent_emails() -> list[tuple[str, str]]:
    """Captures (email, code) pairs that would have been sent by Resend."""
    return []


@pytest.fixture(autouse=True)
def mock_email_sender(sent_emails: list[tuple[str, str]], monkeypatch) -> None:
    """Replace the real Resend sender with one that records into `sent_emails`."""

    def _fake_send(email: str, code: str) -> None:
        sent_emails.append((email, code))

    monkeypatch.setattr(email_service, "send_verification_email", _fake_send)
    # Also patch the name imported into the auth router module.
    import app.api.auth as auth_module

    monkeypatch.setattr(auth_module, "send_verification_email", _fake_send)


@pytest.fixture(autouse=True)
def disable_scheduler(monkeypatch) -> None:
    """Never start the real APScheduler in tests — decay/offline are called directly."""
    import app.services.scheduler as sched

    monkeypatch.setattr(sched, "start_scheduler", lambda: None)
    monkeypatch.setattr(sched, "stop_scheduler", lambda: None)
    # main.py imported the names by value; patch them there too.
    import app.main as main_module

    monkeypatch.setattr(main_module, "start_scheduler", lambda: None)
    monkeypatch.setattr(main_module, "stop_scheduler", lambda: None)
