from tests.util import DEFAULT_PW, latest_otp, register


def _start_login(client, identifier="alice"):
    return client.post("/auth/login", json={"identifier": identifier, "password": DEFAULT_PW})


def test_login_returns_otp_challenge_not_token(client):
    register(client, "alice")
    r = _start_login(client)
    assert r.status_code == 200
    assert r.json()["otp_required"] is True
    assert "access_token" not in r.json()


def test_wrong_otp_rejected(client):
    register(client, "alice")
    _start_login(client)
    r = client.post("/otp/verify", json={"identifier": "alice", "code": "000000"})
    assert r.status_code == 401


def test_otp_is_single_use(client):
    register(client, "alice")
    _start_login(client)
    code = latest_otp("alice")
    assert client.post("/otp/verify", json={"identifier": "alice", "code": code}).status_code == 200
    # replaying the same (now consumed) code must fail
    assert client.post("/otp/verify", json={"identifier": "alice", "code": code}).status_code == 401


def test_resend_is_rate_limited(client):
    register(client, "alice")
    _start_login(client)  # 1st code
    assert client.post("/otp/resend", json={"identifier": "alice"}).status_code == 200  # 2nd
    assert client.post("/otp/resend", json={"identifier": "alice"}).status_code == 200  # 3rd
    assert client.post("/otp/resend", json={"identifier": "alice"}).status_code == 429  # over limit
