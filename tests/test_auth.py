from tests.util import auth, login, register


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_then_login(client):
    assert register(client, "alice").status_code == 201
    token = login(client, "alice")
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_weak_password_rejected(client):
    assert register(client, "alice", password="short").status_code == 400


def test_duplicate_registration(client):
    register(client, "alice")
    assert register(client, "alice").status_code == 409


def test_protected_route_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_wrong_password_is_generic_401(client):
    register(client, "alice")
    r = client.post("/auth/login", json={"identifier": "alice", "password": "Aa1Wrong0000"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"
