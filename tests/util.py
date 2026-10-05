# Small helpers shared by the test modules.
from decimal import Decimal

from app.db.database import SessionLocal
from app.models.account import Account
from app.models.otp import OTPCode
from app.models.user import User

DEFAULT_PW = "Aa1Passw0rd!"


def register(client, username, email=None, password=DEFAULT_PW):
    return client.post(
        "/auth/register",
        json={"username": username, "email": email or f"{username}@example.com", "password": password},
    )


def latest_otp(identifier: str):
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter((User.username == identifier) | (User.email == identifier))
            .first()
        )
        row = (
            db.query(OTPCode)
            .filter(OTPCode.user_id == user.id, OTPCode.used.is_(False))
            .order_by(OTPCode.id.desc())
            .first()
        )
        return row.code if row else None
    finally:
        db.close()


def login(client, identifier, password=DEFAULT_PW):
    client.post("/auth/login", json={"identifier": identifier, "password": password})
    code = latest_otp(identifier)
    r = client.post("/otp/verify", json={"identifier": identifier, "code": code})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def credit(account_number: str, amount):
    """Test-only: put money in an account (a real system would have a deposit path)."""
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.account_number == account_number).first()
        account.balance = Decimal(str(amount))
        db.commit()
        return account.balance
    finally:
        db.close()


def balance(account_number: str):
    db = SessionLocal()
    try:
        return db.query(Account).filter(Account.account_number == account_number).first().balance
    finally:
        db.close()
