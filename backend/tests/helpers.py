"""Shared test helpers for auth flow — reused by test_auth and test_friends."""

from __future__ import annotations

from app.models import EmailCode


def register(client, email="alice@example.com", password="secret123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def latest_code(db, email) -> str:
    code = (
        db.query(EmailCode)
        .filter(EmailCode.email == email)
        .order_by(EmailCode.created_at.desc())
        .first()
    )
    assert code is not None, "no verification code was created"
    return code.code


def verify(client, email, code):
    return client.post("/auth/verify", json={"email": email, "code": code})


def login(client, email="alice@example.com", password="secret123", device="device-A"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password, "device_identifier": device},
    )


def full_flow(client, db, email="alice@example.com", password="secret123", device="device-A"):
    """register -> verify -> login. Returns the login response."""
    assert register(client, email, password).status_code == 201
    code = latest_code(db, email)
    assert verify(client, email, code).status_code == 200
    resp = login(client, email, password, device)
    assert resp.status_code == 200
    return resp


def make_user(client, db, email="alice@example.com", device="device-A") -> str:
    """Run full_flow and return the access token."""
    return full_flow(client, db, email=email, device=device).json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
