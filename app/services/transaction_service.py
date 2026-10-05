# Transaction service (交易服务) — the money-moving core.
#
# Attack-driven design:
#   - balance check inside the same transaction as the debit -> no overdraft
#   - conditional UPDATE (balance >= amount) -> race-safe double-spend guard:
#     two concurrent transfers cannot both pass the check on the same balance
#   - client idempotency key -> a retried request never moves money twice
#   - append-only ledger rows -> every movement is reconstructable
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DBSession

from app.models.account import Account
from app.models.transaction import Transaction


class TransferError(Exception):
    """Business-rule violation -> 400 / 409 at the API layer."""


def _as_money(value) -> Decimal:
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    if amount <= 0:
        raise TransferError("Amount must be positive.")
    return amount


def transfer(
    db: DBSession,
    from_account: Account,
    to_account: Account,
    amount,
    idempotency_key: str,
    description: Optional[str] = None,
) -> Tuple[Transaction, bool]:
    """Move money atomically. Returns (transaction, was_new).

    `was_new=False` means the idempotency key was already used, so nothing moved.
    """
    money = _as_money(amount)
    if from_account.id == to_account.id:
        raise TransferError("Cannot transfer to the same account.")

    out_ref, in_ref = f"{idempotency_key}:OUT", f"{idempotency_key}:IN"

    # Idempotency: if this key was already processed, replay without moving money.
    existing = (
        db.query(Transaction)
        .filter(Transaction.reference.in_([out_ref, in_ref]))
        .order_by(Transaction.id)
        .first()
    )
    if existing is not None:
        return existing, False

    try:
        # Atomic debit: only succeeds while the balance still covers the amount.
        debit = db.execute(
            update(Account)
            .where(Account.id == from_account.id, Account.balance >= money)
            .values(balance=Account.balance - money, updated_at=datetime.utcnow())
        )
        if debit.rowcount != 1:
            db.rollback()
            raise TransferError("Insufficient funds.")

        db.execute(
            update(Account)
            .where(Account.id == to_account.id)
            .values(balance=Account.balance + money, updated_at=datetime.utcnow())
        )

        from_balance = db.execute(
            select(Account.balance).where(Account.id == from_account.id)
        ).scalar_one()
        to_balance = db.execute(
            select(Account.balance).where(Account.id == to_account.id)
        ).scalar_one()

        # Single-sided ledger: one row per account movement.
        tx = Transaction(
            account_id=from_account.id, type="transfer_out", amount=money,
            balance_after=from_balance, reference=out_ref, description=description,
        )
        db.add(tx)
        db.add(Transaction(
            account_id=to_account.id, type="transfer_in", amount=money,
            balance_after=to_balance, reference=in_ref, description=description,
        ))
        db.commit()
        db.refresh(from_account)
        db.refresh(to_account)
        return tx, True
    except Exception:
        db.rollback()
        raise


def total_balance(db: DBSession) -> Decimal:
    """Sum of every balance — must stay constant across transfers (invariant)."""
    total = db.execute(select(Account.balance)).scalars().all()
    return sum((Decimal(str(b)) for b in total), Decimal("0.00"))
