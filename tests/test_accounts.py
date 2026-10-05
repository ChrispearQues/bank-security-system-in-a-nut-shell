from tests.util import auth, balance, credit, login, register


def _two_users(client):
    register(client, "alice")
    register(client, "bob")
    return login(client, "alice"), login(client, "bob")


def _open(client, token):
    return client.post("/accounts", headers=auth(token), json={}).json()["account_number"]


def test_open_account(client):
    register(client, "alice")
    token = login(client, "alice")
    r = client.post("/accounts", headers=auth(token), json={"account_type": "savings"})
    assert r.status_code == 201
    assert r.json()["balance"] == 0
    assert client.get("/accounts", headers=auth(token)).json()[0]["account_number"] == r.json()["account_number"]


def test_transfer_moves_money(client):
    ta, tb = _two_users(client)
    a, b = _open(client, ta), _open(client, tb)
    credit(a, 100)
    r = client.post(
        "/transactions/transfer",
        headers=auth(ta),
        json={"from_account": a, "to_account": b, "amount": 30, "idempotency_key": "key-0001-aaaa"},
    )
    assert r.status_code == 200 and r.json()["outcome"] == "new"
    assert balance(a) == 70 and balance(b) == 30


def test_transfer_is_idempotent(client):
    ta, tb = _two_users(client)
    a, b = _open(client, ta), _open(client, tb)
    credit(a, 100)
    body = {"from_account": a, "to_account": b, "amount": 30, "idempotency_key": "key-0002-bbbb"}
    assert client.post("/transactions/transfer", headers=auth(ta), json=body).json()["outcome"] == "new"
    assert client.post("/transactions/transfer", headers=auth(ta), json=body).json()["outcome"] == "replayed"
    assert balance(a) == 70 and balance(b) == 30  # money moved exactly once


def test_insufficient_funds(client):
    ta, tb = _two_users(client)
    a, b = _open(client, ta), _open(client, tb)
    credit(a, 10)
    r = client.post(
        "/transactions/transfer",
        headers=auth(ta),
        json={"from_account": a, "to_account": b, "amount": 999, "idempotency_key": "key-0003-cccc"},
    )
    assert r.status_code == 409
    assert balance(a) == 10 and balance(b) == 0


def test_cannot_send_from_someone_elses_account(client):
    ta, tb = _two_users(client)
    a, b = _open(client, ta), _open(client, tb)
    credit(b, 50)
    r = client.post(
        "/transactions/transfer",
        headers=auth(ta),  # alice, but b belongs to bob
        json={"from_account": b, "to_account": a, "amount": 10, "idempotency_key": "key-0004-dddd"},
    )
    assert r.status_code == 404


def test_frozen_account_blocks_outgoing_transfer(client):
    ta, tb = _two_users(client)
    a, b = _open(client, ta), _open(client, tb)
    credit(a, 100)
    assert client.post(f"/accounts/{a}/freeze", headers=auth(ta)).status_code == 200
    r = client.post(
        "/transactions/transfer",
        headers=auth(ta),
        json={"from_account": a, "to_account": b, "amount": 10, "idempotency_key": "key-0005-eeee"},
    )
    assert r.status_code == 409
