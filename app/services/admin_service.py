# Admin service (管理服务) — user / role / account administration and audit reads.
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.account import Account
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User


class RoleNotFound(Exception):
    pass


def list_users(db: DBSession):
    return db.query(User).order_by(User.id).all()


def get_user(db: DBSession, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def set_user_active(db: DBSession, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def assign_role(db: DBSession, user: User, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        raise RoleNotFound(role_name)
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
    return role


def remove_role(db: DBSession, user: User, role_name: str) -> bool:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None or role not in user.roles:
        return False
    user.roles.remove(role)
    db.commit()
    db.refresh(user)
    return True


def list_accounts(db: DBSession):
    return db.query(Account).order_by(Account.id).all()


def list_audit_logs(db: DBSession, limit: int = 100):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .all()
    )
