# Transaction routes (交易路由) — transfer + my ledger.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.routes.deps import get_current_user, is_admin
from app.schemas import TransactionResponse, TransferRequest, TransferResponse
from app.services import account_service, logging_service, transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/transfer", response_model=TransferResponse)
def transfer(
    payload: TransferRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = account_service.get_account_by_number(db, payload.from_account)
    # You may only move money out of an account you own.
    if source is None or (source.user_id != current_user.id and not is_admin(current_user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source account not found")

    target = account_service.get_account_by_number(db, payload.to_account)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Destination account not found")

    for account in (source, target):
        if account.status != "active":
            raise HTTPException(status.HTTP_409_CONFLICT, "Account is not active.")

    try:
        tx, was_new = transaction_service.transfer(
            db, source, target, payload.amount, payload.idempotency_key,
            payload.description,
        )
    except transaction_service.TransferError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    logging_service.log_action(
        db, "transfer", user_id=current_user.id, entity="transactions",
        entity_id=tx.id, detail=f"{payload.from_account}->{payload.to_account} {payload.amount}",
    )
    return TransferResponse(
        outcome="new" if was_new else "replayed",
        reference=f"{payload.idempotency_key}:OUT",
        amount=payload.amount,
        from_account=payload.from_account,
        to_account=payload.to_account,
    )


@router.get("", response_model=list[TransactionResponse])
def my_transactions(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == current_user.id)
        .order_by(Transaction.id.desc())
        .all()
    )
