# Logging service (审计服务) — append-only trail of sensitive actions.
# The audit log is never updated or deleted: every line is evidence.
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.audit_log import AuditLog


def log_action(
    db: DBSession,
    action: str,
    *,
    user_id: Optional[int] = None,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
    status: str = "success",
) -> AuditLog:
    entry = AuditLog(
        action=action,
        user_id=user_id,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip_address,
        status=status,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
