# Account routes (账户路由) — open / list / inspect / freeze.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.user import User
from app.routes.deps import get_current_user, is_admin
from app.schemas import AccountCreateRequest, AccountResponse
from app.services import account_service, logging_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def open_account(
    payload: AccountCreateRequest,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = account_service.create_account(
        db, current_user, payload.account_type, payload.currency
    )
    logging_service.log_action(
        db, "account.open", user_id=current_user.id, entity="accounts", entity_id=account.id,
    )
    return account


@router.get("", response_model=list[AccountResponse])
def list_my_accounts(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return account_service.list_accounts(db, current_user)


@router.get("/{account_number}", response_model=AccountResponse)
def get_account(
    account_number: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = account_service.get_account_by_number(db, account_number)
    # 404 (not 403) when it exists but is not yours: no resource enumeration.
    if account is None or (account.user_id != current_user.id and not is_admin(current_user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    return account


@router.post("/{account_number}/freeze", response_model=AccountResponse)
def freeze_account(
    account_number: str,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = account_service.get_account_by_number(db, account_number)
    if account is None or (account.user_id != current_user.id and not is_admin(current_user)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    if account.status != "frozen":
        account.status = "frozen"
        db.commit()
        db.refresh(account)
    logging_service.log_action(
        db, "account.freeze", user_id=current_user.id, entity="accounts",
        entity_id=account.id, status="success",
    )
    return account
