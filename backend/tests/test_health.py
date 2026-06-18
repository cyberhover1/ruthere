"""Smoke tests for the M0 skeleton."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_ok() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_app_title_set() -> None:
    assert app.title == "安心圈 API"


def test_settings_loaded() -> None:
    # Secrets must come from the environment, not be hard-coded defaults in prod.
    assert settings.app_name == "安心圈"
    assert settings.access_token_expire_minutes > 0
