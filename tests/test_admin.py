from app.db.database import SessionLocal
from app.db.seed import create_admin
from tests.util import DEFAULT_PW, auth, login, register

ADMIN_PW = "Aa1Admin0001"


def _make_admin():
    db = SessionLocal()
    try:
        create_admin(db, "root", "root@example.com", ADMIN_PW)
    finally:
        db.close()


def _me(client, token):
    return client.get("/auth/me", headers=auth(token)).json()["id"]


def test_non_admin_forbidden(client):
    register(client, "alice")
    token = login(client, "alice")
    assert client.get("/admin/users", headers=auth(token)).status_code == 403


def test_admin_lists_users_and_deactivates(client):
    _make_admin()
    register(client, "alice")
    admin_token = login(client, "root", ADMIN_PW)
    user_token = login(client, "alice")
    uid = _me(client, user_token)
    assert client.get("/admin/users", headers=auth(admin_token)).status_code == 200
    r = client.post(f"/admin/users/{uid}/active", headers=auth(admin_token), json={"is_active": False})
    assert r.status_code == 200
    # a deactivated user can no longer log in
    r = client.post("/auth/login", json={"identifier": "alice", "password": DEFAULT_PW})
    assert r.status_code == 401


def test_admin_assigns_role(client):
    _make_admin()
    register(client, "alice")
    admin_token = login(client, "root", ADMIN_PW)
    uid = _me(client, login(client, "alice"))
    r = client.post(f"/admin/users/{uid}/roles", headers=auth(admin_token), json={"name": "customer"})
    assert r.status_code == 200
    assert [role["name"] for role in r.json()["roles"]] == ["customer"]
