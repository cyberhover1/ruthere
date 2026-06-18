"""M2 friendship flow tests.

Covers QR add, email search, friend requests (send/list/accept/reject),
friend list, nickname, delete (+ friend_removed notification), per-friend
data-source matrix, and notification delivery. Reuses the `client`/`db`
fixtures and `make_user`/`auth_header` helpers.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import QrToken

from tests.helpers import auth_header, make_user


# --- helpers ---------------------------------------------------------------

def two_users(client, db) -> tuple[str, str, int, int]:
    """Create two verified+logged-in users. Returns (tokenA, tokenB, idA, idB)."""
    ta = make_user(client, db, email="a@example.com", device="A")
    tb = make_user(client, db, email="b@example.com", device="B")
    ida = client.get("/auth/me", headers=auth_header(ta)).json()["id"]
    idb = client.get("/auth/me", headers=auth_header(tb)).json()["id"]
    return ta, tb, ida, idb


# --- QR code add -----------------------------------------------------------

def test_qrcode_add_creates_mutual_friendship(client, db):
    ta, tb, ida, idb = two_users(client, db)
    qr = client.post("/friends/qrcode", headers=auth_header(ta))
    assert qr.status_code == 200
    token = qr.json()["token"]

    resp = client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))
    assert resp.status_code == 200

    # Both see each other in their lists.
    la = client.get("/friends", headers=auth_header(ta)).json()["friends"]
    lb = client.get("/friends", headers=auth_header(tb)).json()["friends"]
    assert [f["friend_id"] for f in la] == [idb]
    assert [f["friend_id"] for f in lb] == [ida]


def test_qrcode_reuse_after_used_rejected(client, db):
    ta, tb, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    assert client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb)).status_code == 200
    resp = client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))
    assert resp.status_code == 400
    assert "已使用" in resp.json()["detail"]


def test_qrcode_expired_rejected(client, db):
    ta, tb, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    # Manually expire it.
    row = db.query(QrToken).filter_by(token=token).one()
    row.expire_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    resp = client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))
    assert resp.status_code == 400
    assert "过期" in resp.json()["detail"]


def test_qrcode_add_self_rejected(client, db):
    ta, _, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    resp = client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(ta))
    assert resp.status_code == 400


def test_qrcode_add_already_friends_conflict(client, db):
    ta, tb, _, _ = two_users(client, db)
    t1 = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    assert client.post("/friends/add-by-qrcode", json={"token": t1}, headers=auth_header(tb)).status_code == 200
    t2 = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    resp = client.post("/friends/add-by-qrcode", json={"token": t2}, headers=auth_header(tb))
    assert resp.status_code == 409


# --- email search ----------------------------------------------------------

def test_search_finds_user(client, db):
    ta, tb, ida, idb = two_users(client, db)
    resp = client.get("/friends/search", params={"email": "b@example.com"}, headers=auth_header(ta))
    assert resp.status_code == 200
    assert resp.json() == [{"id": idb, "email": "b@example.com"}]


def test_search_not_found_empty(client, db):
    ta, _, _, _ = two_users(client, db)
    resp = client.get("/friends/search", params={"email": "ghost@example.com"}, headers=auth_header(ta))
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_self_empty(client, db):
    ta, _, _, _ = two_users(client, db)
    resp = client.get("/friends/search", params={"email": "a@example.com"}, headers=auth_header(ta))
    assert resp.json() == []


# --- friend requests -------------------------------------------------------

def test_request_send_accept_creates_friendship(client, db):
    ta, tb, ida, idb = two_users(client, db)
    r = client.post("/friends/request", json={"to_user_id": idb}, headers=auth_header(ta))
    assert r.status_code == 201

    # B sees the pending request.
    reqs = client.get("/friends/requests", headers=auth_header(tb)).json()
    assert any(x["from_user_id"] == ida and x["status"] == "pending" for x in reqs)
    req_id = [x for x in reqs if x["from_user_id"] == ida][0]["id"]

    assert client.post(f"/friends/requests/{req_id}/accept", headers=auth_header(tb)).status_code == 200

    la = client.get("/friends", headers=auth_header(ta)).json()["friends"]
    assert [f["friend_id"] for f in la] == [idb]


def test_request_reject_no_friendship(client, db):
    ta, tb, ida, idb = two_users(client, db)
    client.post("/friends/request", json={"to_user_id": idb}, headers=auth_header(ta))
    req_id = client.get("/friends/requests", headers=auth_header(tb)).json()[0]["id"]
    assert client.post(f"/friends/requests/{req_id}/reject", headers=auth_header(tb)).status_code == 200
    assert client.get("/friends", headers=auth_header(ta)).json()["friends"] == []


def test_request_to_self_rejected(client, db):
    ta, _, ida, _ = two_users(client, db)
    resp = client.post("/friends/request", json={"to_user_id": ida}, headers=auth_header(ta))
    assert resp.status_code == 400


def test_request_duplicate_pending_conflict(client, db):
    ta, tb, _, idb = two_users(client, db)
    assert client.post("/friends/request", json={"to_user_id": idb}, headers=auth_header(ta)).status_code == 201
    resp = client.post("/friends/request", json={"to_user_id": idb}, headers=auth_header(ta))
    assert resp.status_code == 409


def test_request_accept_by_wrong_user_forbidden(client, db):
    ta, tb, _, idb = two_users(client, db)
    client.post("/friends/request", json={"to_user_id": idb}, headers=auth_header(ta))
    req_id = client.get("/friends/requests", headers=auth_header(tb)).json()[0]["id"]
    # A (the sender) tries to accept their own request -> 403
    resp = client.post(f"/friends/requests/{req_id}/accept", headers=auth_header(ta))
    assert resp.status_code == 403


# --- nickname --------------------------------------------------------------

def test_nickname_update_only_affects_my_view(client, db):
    ta, tb, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))

    fs_id = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    assert client.patch(
        f"/friends/{fs_id}/nickname", json={"nickname": "小B"}, headers=auth_header(ta)
    ).status_code == 200

    mine = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]
    assert mine["nickname"] == "小B"
    # B's view of A is unaffected.
    theirs = client.get("/friends", headers=auth_header(tb)).json()["friends"][0]
    assert theirs["nickname"] is None


def test_nickname_unknown_friendship_404(client, db):
    ta, _, _, _ = two_users(client, db)
    resp = client.patch("/friends/9999/nickname", json={"nickname": "x"}, headers=auth_header(ta))
    assert resp.status_code == 404


# --- delete + notification -------------------------------------------------

def test_delete_removes_both_directions(client, db):
    ta, tb, ida, idb = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))

    fs_id = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    assert client.delete(f"/friends/{fs_id}", headers=auth_header(ta)).status_code == 200

    # Both lists empty now (symmetric rows removed).
    assert client.get("/friends", headers=auth_header(ta)).json()["friends"] == []
    assert client.get("/friends", headers=auth_header(tb)).json()["friends"] == []


def test_delete_notification_dedicated(client, db):
    """Isolated: deleting writes friend_removed, delivered on next pull (no prior consumption)."""
    ta, tb, ida, idb = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))

    fs_id = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    client.delete(f"/friends/{fs_id}", headers=auth_header(ta))

    # B has NOT called list_friends yet, so notification is undelivered here.
    notifs = client.get("/friends/notifications", headers=auth_header(tb)).json()
    assert len(notifs) == 1
    assert notifs[0]["type"] == "friend_removed"
    assert notifs[0]["payload"]["removed_by_user_id"] == ida

    # Second pull is empty (already delivered).
    assert client.get("/friends/notifications", headers=auth_header(tb)).json() == []


# --- data-source matrix ----------------------------------------------------

def test_data_sources_set_and_get(client, db):
    ta, tb, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))

    fs_id = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    sources = ["steps", "screen_unlock"]
    r = client.put(f"/friends/{fs_id}/data-sources", json={"allowed_sources": sources}, headers=auth_header(ta))
    assert r.status_code == 200
    assert set(r.json()["allowed_sources"]) == set(sources)

    r = client.get(f"/friends/{fs_id}/data-sources", headers=auth_header(ta))
    assert set(r.json()["allowed_sources"]) == set(sources)


def test_data_sources_independent_per_friend(client, db):
    ta, tb, ida, idb = two_users(client, db)
    # Make a third user C
    tc = make_user(client, db, email="c@example.com", device="C")
    idc = client.get("/auth/me", headers=auth_header(tc)).json()["id"]

    # A friends B and C
    for owner, scanner in ((ta, tb), (ta, tc)):
        tok = client.post("/friends/qrcode", headers=auth_header(owner)).json()["token"]
        client.post("/friends/add-by-qrcode", json={"token": tok}, headers=auth_header(scanner))

    friends = client.get("/friends", headers=auth_header(ta)).json()["friends"]
    fs_b = [f for f in friends if f["friend_id"] == idb][0]["friendship_id"]
    fs_c = [f for f in friends if f["friend_id"] == idc][0]["friendship_id"]

    client.put(f"/friends/{fs_b}/data-sources", json={"allowed_sources": ["steps"]}, headers=auth_header(ta))
    client.put(
        f"/friends/{fs_c}/data-sources",
        json={"allowed_sources": ["steps", "charging", "headset"]},
        headers=auth_header(ta),
    )

    assert set(client.get(f"/friends/{fs_b}/data-sources", headers=auth_header(ta)).json()["allowed_sources"]) == {"steps"}
    assert set(client.get(f"/friends/{fs_c}/data-sources", headers=auth_header(ta)).json()["allowed_sources"]) == {
        "steps",
        "charging",
        "headset",
    }


def test_data_sources_invalid_rejected(client, db):
    ta, tb, _, _ = two_users(client, db)
    token = client.post("/friends/qrcode", headers=auth_header(ta)).json()["token"]
    client.post("/friends/add-by-qrcode", json={"token": token}, headers=auth_header(tb))
    fs_id = client.get("/friends", headers=auth_header(ta)).json()["friends"][0]["friendship_id"]
    resp = client.put(
        f"/friends/{fs_id}/data-sources", json={"allowed_sources": ["gps"]}, headers=auth_header(ta)
    )
    assert resp.status_code == 400


# --- auth ------------------------------------------------------------------

def test_friends_endpoints_require_auth(client):
    for method, path in [
        ("get", "/friends"),
        ("get", "/friends/notifications"),
        ("post", "/friends/qrcode"),
        ("get", "/friends/search?email=x@example.com"),
    ]:
        assert getattr(client, method)(path).status_code == 401
