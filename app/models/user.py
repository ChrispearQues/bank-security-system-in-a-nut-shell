# User (用户) model — the account holders of the bank.
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.models.role import user_roles # Link table (关联表) used by the roles relationship below.

class User(Base):
# One row = one registered user.
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique = True, index=True, nullable = False)
    email = Column(String, unique = True, index = True, nullable = False) # Login identity; unique because two users cannot share one email.
    password_hash = Column(String, nullable = False) # Never store the raw password, only its hash (bcrypt, see M2).
    is_active = Column(Boolean, default = True) # Soft switch: set False to disable a user instead of deleting the row.
    created_at = Column(DateTime, default = datetime.utcnow)

    # Navigation lines (关系), not real columns in the table.
    accounts = relationship("Account", back_populates="owner")
    roles = relationship("Role", secondary = user_roles, back_populates="users")
    sessions = relationship("UserSession", back_populates="user") # all tokens issued to this user
    otps = relationship("OTPCode", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")