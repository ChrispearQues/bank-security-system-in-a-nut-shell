# Package entry (包入口) — importing this file registers every model on Base.metadata.
# main.py only needs `from app import models`; a model missing here would silently get no table.
from app.models.account import Account
from app.models.audit_log import AuditLog
from app.models.otp import OTPCode
from app.models.role import Role
from app.models.session import UserSession
from app.models.transaction import Transaction
from app.models.user import User

# Declared so linters see these as intentional re-exports (importing them is the point).
__all__ = ["User", "Account", "Role", "UserSession", "OTPCode", "Transaction", "AuditLog"]
