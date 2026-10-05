# Account service (账户服务) — open / list / freeze accounts.
import secrets

from sqlalchemy.orm import Session as DBSession

from app.models.account import Account
from app.models.user import User


def _generate_account_number(db: DBSession) -> str:
    """Ten random digits; retry on the (astronomically unlikely) collision."""
    while True:
        number = "".join(secrets.choice("0123456789") for _ in range(10))
        if db.query(Account).filter(Account.account_number == number).first() is None:
            return number


def create_account(db: DBSession, user: User, account_type: str = "savings", currency: str = "HKD") -> Account:
    account = Account(
        user_id=user.id,
        account_number=_generate_account_number(db),
        account_type=account_type,
        currency=currency,
        balance=0,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: DBSession, user: User):
    return db.query(Account).filter(Account.user_id == user.id).order_by(Account.id).all()


def get_account_by_number(db: DBSession, number: str):
    return db.query(Account).filter(Account.account_number == number).first()


class AccountNotFound(Exception):
    pass


class AccountNotActive(Exception):
    pass


def require_active_account(db: DBSession, number: str) -> Account:
    """Fetch an account and refuse if it is frozen/closed (transfer guard)."""
    account = db.query(Account).filter(Account.account_number == number).with_for_update().first()
    if account is None:
        raise AccountNotFound(number)
    if account.status != "active":
        raise AccountNotActive(number)
    return account
