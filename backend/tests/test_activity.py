"""M3 activity system tests.

Covers the calc engine, report (per-friend visible values + desensitized
delivery + notification piggyback), decay, offline, and reset. Decay/offline
are exercised by calling the service functions directly (scheduler disabled).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.activity_calc import compute_activity, compute_visible_for_friend
from app.models import ActivityReport
from app.services.activity import decay_all, mark_offline, reset_activity_for_user

from tests.helpers import auth_header, make_user


# --- helpers ---------------------------------------------------------------

def two_friends(client, db):
    """A and B are mutual friends. Returns (tokenA, tokenB, idA, idB)."""
    ta = make_user(client, db, email="a@example.com", device="A")
    tb = make_user(client, db, email="b@example.com", device="B")
    ida = client.get("/auth/me", headers=auth_header(ta)).json()["id"]
    idb = client.get("/auth/me", headers=auth_header(tb)).json()["id"]
    qr = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    assert client.post("/friends/add-by-qrcode", json={"token": qr}, headers=auth_header(tb)).status_code == 200
    return ta, tb, ida, idb


def set_sources(client, token, friendship_id, sources):
    return client.put(
        f"/friends/{friendship_id}/data-sources",
        json={"allowed_sources": sources},
        headers=auth_header(token),
    )


# --- calc engine -----------------------------------------------------------

def test_compute_activity_default_weights():
    # All sources at 1.0 -> 100.
    comps = {
        "steps": 1.0, "screen_unlock": 1.0, "significant_motion": 1.0,
        "charging": 1.0, "headset": 1.0, "pickup_flip": 1.0, "ambient_light": 1.0,
    }
    assert compute_activity(comps) == 100
    # All zero -> 0.
    assert compute_activity({k: 0.0 for k in comps}) == 0


def test_compute_visible_subset_renormalizes():
    """A friend seeing only `steps` should reflect steps alone."""
    comps = {"steps": 1.0, "screen_unlock": 0.0}  # steps dominates
    only_steps = compute_visible_for_friend(comps, ["steps"])
    assert only_steps == 100  # steps=1.0, renormalized to weight 1.0

    # If the friend sees only screen_unlock (0.0), they see 0.
    only_screen = compute_visible_for_friend(comps, ["screen_unlock"])
    assert only_screen == 0


def test_compute_visible_no_allowed_sources_is_zero():
    assert compute_visible_for_friend({"steps": 1.0}, []) == 0


def test_compute_clamps_to_0_100():
    assert compute_activity({"steps": 5.0}) <= 100
    assert compute_activity({"steps": -3.0}) == 0


# --- report: per-friend visible values -------------------------------------

def test_report_creates_per_friend_rows(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    comps = {"steps": 1.0, "screen_unlock": 1.0}
    resp = client.post("/activity/report", json={"components": comps}, headers=auth_header(ta))
    assert resp.status_code == 200
    # A exposed a row (user_id=A, friend_id=B).
    rows = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).all()
    assert len(rows) == 1
    assert rows[0].value > 0
    assert rows[0].is_offline is False


def test_report_different_value_per_friend(client, db):
    """Same user, two friends with different allowed sources -> different stored values."""
    ta = make_user(client, db, email="a@example.com", device="A")
    tb = make_user(client, db, email="b@example.com", device="B")
    tc = make_user(client, db, email="c@example.com", device="C")
    ida = client.get("/auth/me", headers=auth_header(ta)).json()["id"]
    idb = client.get("/auth/me", headers=auth_header(tb)).json()["id"]
    idc = client.get("/auth/me", headers=auth_header(tc)).json()["id"]

    # A friends B and C.
    for scanner_token in (tb, tc):
        qr = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
        client.post("/friends/add-by-qrcode", json={"token": qr}, headers=auth_header(scanner_token))

    friends = client.get("/friends", headers=auth_header(ta)).json()["friends"]
    fs_b = [f for f in friends if f["friend_id"] == idb][0]["friendship_id"]
    fs_c = [f for f in friends if f["friend_id"] == idc][0]["friendship_id"]

    # A opens only steps to B; all sources to C.
    set_sources(client, ta, fs_b, ["steps"])
    set_sources(client, ta, fs_c, ["steps", "screen_unlock", "charging"])

    comps = {"steps": 1.0, "screen_unlock": 0.0, "charging": 0.0}
    client.post("/activity/report", json={"components": comps}, headers=auth_header(ta))

    val_b = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one().value
    val_c = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idc).one().value
    # B sees steps only (1.0) -> 100; C sees steps(1)+screen(0)+charging(0) renormalized -> 100 too.
    assert val_b == 100
    # Different subsets can still differ; verify with a mix where they do.
    comps2 = {"steps": 0.0, "screen_unlock": 1.0, "charging": 1.0}
    client.post("/activity/report", json={"components": comps2}, headers=auth_header(ta))
    val_b2 = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one().value
    val_c2 = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idc).one().value
    assert val_b2 == 0          # B sees only steps (0.0)
    assert val_c2 > 0           # C sees screen_unlock+charging (both 1.0)
    assert val_b2 != val_c2     # PRD §4.2: different values per friend


# --- report: desensitized delivery + notification piggyback ----------------

def test_report_response_is_desensitized(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    # B reports so A has something to receive.
    client.post(
        "/activity/report", json={"components": {"steps": 0.8}}, headers=auth_header(tb)
    )
    resp = client.post(
        "/activity/report", json={"components": {"steps": 0.5}}, headers=auth_header(ta)
    )
    body = resp.json()
    assert "friends_activity" in body
    fa = body["friends_activity"]
    assert len(fa) == 1
    item = fa[0]
    # PRD §4.5: only these fields, never raw components/details.
    assert set(item.keys()) == {"friend_id", "value", "last_reported_at", "is_offline"}
    assert item["friend_id"] == idb
    assert 0 <= item["value"] <= 100


def test_report_delivers_pending_notifications(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    # B deletes A -> A gets a friend_removed notification.
    fs_b = client.get("/friends", headers=auth_header(tb)).json()["friends"][0]["friendship_id"]
    client.delete(f"/friends/{fs_b}", headers=auth_header(tb))

    # A reports -> notification piggybacked and consumed.
    resp = client.post(
        "/activity/report", json={"components": {"steps": 0.5}}, headers=auth_header(ta)
    )
    notifs = resp.json()["notifications"]
    assert any(n["type"] == "friend_removed" for n in notifs)

    # Second report -> no more notifications.
    resp2 = client.post(
        "/activity/report", json={"components": {"steps": 0.5}}, headers=auth_header(ta)
    )
    assert resp2.json()["notifications"] == []


# --- decay -----------------------------------------------------------------

def test_decay_lowers_value_over_time(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    # Restrict B to steps only so a steps=1.0 report yields 100.
    fs = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    set_sources(client, ta, fs, ["steps"])
    client.post("/activity/report", json={"components": {"steps": 1.0}}, headers=auth_header(ta))
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    assert row.value == 100

    # Backdate the last report by 6 hours -> ~50% decayed (rate 100/12 per hour * 6 = 50).
    row.last_reported_at = datetime.now(timezone.utc) - timedelta(hours=6)
    db.commit()

    changed = decay_all(db)
    assert changed >= 1
    db.refresh(row)
    assert row.value < 100
    assert row.value > 0  # 6h of 12h -> around 50


def test_decay_floors_at_zero(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    fs = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    set_sources(client, ta, fs, ["steps"])
    client.post("/activity/report", json={"components": {"steps": 1.0}}, headers=auth_header(ta))
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    # Backdate well past full decay (e.g. 24h).
    row.last_reported_at = datetime.now(timezone.utc) - timedelta(hours=24)
    db.commit()
    decay_all(db)
    db.refresh(row)
    assert row.value == 0


# --- offline ---------------------------------------------------------------

def test_mark_offline_after_threshold(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    client.post("/activity/report", json={"components": {"steps": 1.0}}, headers=auth_header(ta))
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    assert row.is_offline is False

    # Backdate past 12h.
    row.last_reported_at = datetime.now(timezone.utc) - timedelta(hours=13)
    db.commit()

    marked = mark_offline(db)
    assert marked >= 1
    db.refresh(row)
    assert row.is_offline is True


def test_recent_report_not_marked_offline(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    client.post("/activity/report", json={"components": {"steps": 1.0}}, headers=auth_header(ta))
    marked = mark_offline(db)
    assert marked == 0
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    assert row.is_offline is False


# --- reset (login trigger) -------------------------------------------------

def test_reset_sets_value_to_full(client, db):
    ta, tb, ida, idb = two_friends(client, db)
    client.post("/activity/report", json={"components": {"steps": 0.2}}, headers=auth_header(ta))
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    assert row.value < 100

    reset_activity_for_user(ida, db)
    db.refresh(row)
    assert row.value == 100
    assert row.is_offline is False


def test_login_resets_activity(client, db):
    """PRD §4.4: initial login resets activity to full (M3 hook wired in M1)."""
    ta, tb, ida, idb = two_friends(client, db)
    # Report a low value first.
    client.post("/activity/report", json={"components": {"steps": 0.1}}, headers=auth_header(ta))
    row = db.query(ActivityReport).filter_by(user_id=ida, friend_id=idb).one()
    assert row.value < 100

    # Log in again (new device) -> reset triggered.
    resp = client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "secret123", "device_identifier": "A2"},
    )
    assert resp.status_code == 200
    db.refresh(row)
    assert row.value == 100


# --- auth ------------------------------------------------------------------

def test_report_requires_auth(client):
    resp = client.post("/activity/report", json={"components": {"steps": 0.5}})
    assert resp.status_code == 401
