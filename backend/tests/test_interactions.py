"""M4 interaction tests: check-ins + pokes."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.config import BEIJING_TZ
from app.models import Poke

from tests.helpers import auth_header, make_user


# --- helpers ---------------------------------------------------------------

def two_friends(client, db):
    ta = make_user(client, db, email="a@example.com", device="A")
    tb = make_user(client, db, email="b@example.com", device="B")
    ida = client.get("/auth/me", headers=auth_header(ta)).json()["id"]
    idb = client.get("/auth/me", headers=auth_header(tb)).json()["id"]
    qr = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": qr}, headers=auth_header(tb))
    return ta, tb, ida, idb


def my_friendship_id(client, token):
    return client.get("/friends", headers=auth_header(token)).json()["friends"][0]["friendship_id"]


# --- check-ins -------------------------------------------------------------

def test_checkin_create_success(client, db):
    ta = make_user(client, db)
    resp = client.post("/checkins", json={"type": "起床"}, headers=auth_header(ta))
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "起床"
    assert body["note"] is None


def test_checkin_create_with_note(client, db):
    ta = make_user(client, db)
    resp = client.post("/checkins", json={"type": "运动", "note": "跑了5公里"}, headers=auth_header(ta))
    assert resp.status_code == 201
    assert resp.json()["note"] == "跑了5公里"


def test_checkin_invalid_type_rejected(client, db):
    ta = make_user(client, db)
    resp = client.post("/checkins", json={"type": "睡觉"}, headers=auth_header(ta))
    assert resp.status_code == 400
    assert "非法" in resp.json()["detail"]


def test_checkin_list_returns_only_mine(client, db):
    ta = make_user(client, db, email="a@example.com")
    tb = make_user(client, db, email="b@example.com")
    client.post("/checkins", json={"type": "起床"}, headers=auth_header(ta))
    client.post("/checkins", json={"type": "吃饭"}, headers=auth_header(ta))
    client.post("/checkins", json={"type": "运动"}, headers=auth_header(tb))

    mine = client.get("/checkins", headers=auth_header(ta)).json()
    # Both A's check-ins returned (order may tie on same-second timestamps);
    # B's check-in must NOT appear.
    assert {c["type"] for c in mine} == {"起床", "吃饭"}


def test_checkin_pagination(client, db):
    ta = make_user(client, db)
    for _ in range(3):
        client.post("/checkins", json={"type": "休息"}, headers=auth_header(ta))
    page = client.get("/checkins", params={"limit": 2, "offset": 0}, headers=auth_header(ta)).json()
    assert len(page) == 2
    page2 = client.get("/checkins", params={"limit": 2, "offset": 2}, headers=auth_header(ta)).json()
    assert len(page2) == 1


def test_checkin_requires_auth(client):
    assert client.post("/checkins", json={"type": "起床"}).status_code == 401
    assert client.get("/checkins").status_code == 401


# --- pokes -----------------------------------------------------------------

def test_poke_success_resets_initiator_and_notifies(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    # A reports a low value first so reset is observable.
    client.post("/activity/report", json={"components": {"steps": 0.1}}, headers=auth_header(ta))

    fs = my_friendship_id(client, ta)
    resp = client.post(f"/pokes/{fs}", headers=auth_header(ta))
    assert resp.status_code == 200
    assert resp.json()["to_user_id"] == idb

    # A's activity rows should now be 100 (reset).
    from app.models import ActivityReport

    rows = db.query(ActivityReport).filter_by(user_id=ida).all()
    assert len(rows) >= 1
    assert all(r.value == 100 for r in rows)

    # B's next report delivers the `poked` notification (one-shot).
    rb = client.post("/activity/report", json={"components": {"steps": 0.5}}, headers=auth_header(tb)).json()
    notifs = [n for n in rb["notifications"] if n["type"] == "poked"]
    assert len(notifs) == 1
    assert notifs[0]["payload"]["poked_by_user_id"] == ida

    # Second report -> no more poked notifications.
    rb2 = client.post("/activity/report", json={"components": {"steps": 0.5}}, headers=auth_header(tb)).json()
    assert [n for n in rb2["notifications"] if n["type"] == "poked"] == []


def test_poke_rate_limited_within_cooldown(client, db):
    ta, tb, _, _ = two_friends(client, db)
    fs = my_friendship_id(client, ta)
    assert client.post(f"/pokes/{fs}", headers=auth_header(ta)).status_code == 200
    # SQLite's func.now() returns UTC, but the server interprets naive timestamps
    # as Beijing time — backdate to Beijing "now" so elapsed ≈ 0.
    poke = db.query(Poke).order_by(Poke.id.desc()).first()
    if poke is not None:
        poke.created_at = datetime.now(BEIJING_TZ)
        db.commit()
    resp = client.post(f"/pokes/{fs}", headers=auth_header(ta))
    assert resp.status_code == 429
    assert "频繁" in resp.json()["detail"]


def test_poke_allowed_after_cooldown(client, db):
    ta, tb, _, _ = two_friends(client, db)
    fs = my_friendship_id(client, ta)
    assert client.post(f"/pokes/{fs}", headers=auth_header(ta)).status_code == 200

    # Backdate the existing poke past the cooldown window.
    poke = db.query(Poke).filter_by(from_user_id=client.get("/auth/me", headers=auth_header(ta)).json()["id"]).first()
    poke.created_at = datetime.now(BEIJING_TZ) - timedelta(seconds=3700)
    db.commit()

    resp = client.post(f"/pokes/{fs}", headers=auth_header(ta))
    assert resp.status_code == 200


def test_poke_unknown_friendship_404(client, db):
    ta = make_user(client, db)
    resp = client.post("/pokes/9999", headers=auth_header(ta))
    assert resp.status_code == 404


def test_poke_other_users_friendship_404(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    # B's friendship id should not be accessible to A via the same id? Both own
    # their own rows; A using B's friendship row id -> 404 (not owned by A).
    fs_b = my_friendship_id(client, tb)
    resp = client.post(f"/pokes/{fs_b}", headers=auth_header(ta))
    assert resp.status_code == 404


def test_poke_requires_auth(client):
    assert client.post("/pokes/1").status_code == 401
