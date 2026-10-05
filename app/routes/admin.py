# Admin routes (管理路由) — user / role / account administration + audit trail.
# Every route requires the 'admin' role and writes to the audit log.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.user import User
from app.routes.deps import require_admin
from app.schemas import (
    AdminAccountResponse,
    AdminUserResponse,
    AuditLogResponse,
    RoleAssignRequest,
    UserActiveRequest,
)
from app.services import admin_service, logging_service
from app.services.admin_service import RoleNotFound

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_user_or_404(db, user_id):
    user = admin_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(db: DBSession = Depends(get_db), admin: User = Depends(require_admin)):
    return admin_service.list_users(db)


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, db: DBSession = Depends(get_db), admin: User = Depends(require_admin)):
    return _get_user_or_404(db, user_id)


@router.post("/users/{user_id}/active", response_model=AdminUserResponse)
def set_active(
    user_id: int,
    payload: UserActiveRequest,
    db: DBSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    admin_service.set_user_active(db, user, payload.is_active)
    logging_service.log_action(
        db, "admin.user_active", user_id=admin.id, entity="users", entity_id=user.id,
        detail=f"is_active={payload.is_active}",
    )
    return user


@router.post("/users/{user_id}/roles", response_model=AdminUserResponse)
def assign_role(
    user_id: int,
    payload: RoleAssignRequest,
    db: DBSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    try:
        admin_service.assign_role(db, user, payload.name)
    except RoleNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    logging_service.log_action(
        db, "admin.role_assign", user_id=admin.id, entity="users", entity_id=user.id,
        detail=payload.name,
    )
    return user


@router.delete("/users/{user_id}/roles/{role_name}", response_model=AdminUserResponse)
def remove_role(
    user_id: int,
    role_name: str,
    db: DBSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    admin_service.remove_role(db, user, role_name)
    logging_service.log_action(
        db, "admin.role_remove", user_id=admin.id, entity="users", entity_id=user.id,
        detail=role_name,
    )
    return user


@router.get("/accounts", response_model=list[AdminAccountResponse])
def list_accounts(db: DBSession = Depends(get_db), admin: User = Depends(require_admin)):
    return admin_service.list_accounts(db)


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def audit_logs(
    limit: int = 100,
    db: DBSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    limit = max(1, min(limit, 500))
    return admin_service.list_audit_logs(db, limit)
