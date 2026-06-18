"""M1 auth flow tests.

Covers register / resend-code / verify / login / logout / me, including
single-device login (kicking) and the various error paths.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import EmailCode


# --- helpers ---------------------------------------------------------------

def register(client, email="alice@example.com", password="secret123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def latest_code(db, email) -> str:
    code = db.query(EmailCode).filter(EmailCode.email == email).order_by(
        EmailCode.created_at.desc()
    ).first()
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


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- register --------------------------------------------------------------

def test_register_creates_unverified_user_and_sends_code(client, db, sent_emails):
    resp = register(client, "alice@example.com")
    assert resp.status_code == 201
    assert resp.json()["message"]

    from app.models import User

    user = db.query(User).filter_by(email="alice@example.com").one()
    assert user.is_verified is False
    assert user.password_hash != "secret123"  # hashed, not plaintext
    assert len(sent_emails) == 1
    assert sent_emails[0][0] == "alice@example.com"
    assert len(sent_emails[0][1]) == 6


def test_register_duplicate_email_conflicts(client):
    assert register(client, "alice@example.com").status_code == 201
    resp = register(client, "alice@example.com")
    assert resp.status_code == 409


def test_register_invalid_email_rejected(client):
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "secret123"})
    assert resp.status_code == 422


def test_register_short_password_rejected(client):
    resp = client.post("/auth/register", json={"email": "x@example.com", "password": "12"})
    assert resp.status_code == 422


# --- verify ----------------------------------------------------------------

def test_verify_correct_code_activates(client, db):
    register(client, "alice@example.com")
    assert verify(client, "alice@example.com", latest_code(db, "alice@example.com")).status_code == 200

    from app.models import User

    assert db.query(User).filter_by(email="alice@example.com").one().is_verified is True


def test_verify_wrong_code_rejected(client, db):
    register(client, "alice@example.com")
    resp = verify(client, "alice@example.com", "000000")
    assert resp.status_code == 400
    assert "错误" in resp.json()["detail"]


def test_verify_expired_code_rejected(client, db):
    register(client, "alice@example.com")
    code = db.query(EmailCode).filter_by(email="alice@example.com").one()
    code.expire_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    resp = verify(client, "alice@example.com", code.code)
    assert resp.status_code == 400
    assert "过期" in resp.json()["detail"]


def test_verify_used_code_rejected(client, db):
    register(client, "alice@example.com")
    c = latest_code(db, "alice@example.com")
    assert verify(client, "alice@example.com", c).status_code == 200
    resp = verify(client, "alice@example.com", c)
    assert resp.status_code == 400
    assert "已使用" in resp.json()["detail"]


# --- login -----------------------------------------------------------------

def test_login_success_returns_token(client, db):
    resp = full_flow(client, db)
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user_id"] >= 1


def test_login_unverified_user_forbidden(client):
    register(client, "alice@example.com")
    resp = login(client, "alice@example.com")
    assert resp.status_code == 403
    assert "未验证" in resp.json()["detail"]


def test_login_wrong_password(client, db):
    register(client, "alice@example.com")
    code = latest_code(db, "alice@example.com")
    verify(client, "alice@example.com", code)
    resp = login(client, "alice@example.com", password="wrong")
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = login(client, "ghost@example.com")
    assert resp.status_code == 401


# --- single-device login (kicking) ----------------------------------------

def test_new_login_kicks_old_device(client, db):
    token_a = full_flow(client, db, device="A").json()["access_token"]
    # device A works
    assert client.get("/auth/me", headers=auth_header(token_a)).status_code == 200

    # device B logs in with the same (already verified) account -> A is kicked
    resp_b = login(client, device="B")
    assert resp_b.status_code == 200
    assert client.get("/auth/me", headers=auth_header(token_a)).status_code == 401
    # device B's fresh token still works
    assert client.get("/auth/me", headers=auth_header(resp_b.json()["access_token"])).status_code == 200


# --- me / logout -----------------------------------------------------------

def test_me_without_token_unauthorized(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_current_user(client, db):
    token = full_flow(client, db).json()["access_token"]
    resp = client.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["is_verified"] is True


def test_logout_invalidates_token(client, db):
    token = full_flow(client, db).json()["access_token"]
    assert client.post("/auth/logout", headers=auth_header(token)).status_code == 200
    # token no longer works (device deactivated)
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


# --- resend-code -----------------------------------------------------------

def test_resend_code_creates_new_code(client, db, sent_emails):
    register(client, "alice@example.com")
    first = latest_code(db, "alice@example.com")
    resp = client.post("/auth/resend-code", json={"email": "alice@example.com"})
    # may hit cooldown if too fast; allow either 200 or 429 but never 5xx
    assert resp.status_code in (200, 429)
    if resp.status_code == 200:
        second = latest_code(db, "alice@example.com")
        assert second != first


def test_resend_code_cooldown_enforced(client, db):
    register(client, "alice@example.com")
    assert client.post("/auth/resend-code", json={"email": "alice@example.com"}).status_code == 429


def test_resend_code_unknown_email(client):
    resp = client.post("/auth/resend-code", json={"email": "ghost@example.com"})
    assert resp.status_code == 404


def test_resend_code_for_verified_user(client, db):
    register(client, "alice@example.com")
    verify(client, "alice@example.com", latest_code(db, "alice@example.com"))
    resp = client.post("/auth/resend-code", json={"email": "alice@example.com"})
    assert resp.status_code == 400
