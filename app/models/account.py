# Account (银行账户) model — one bank account owned by a user.
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Account(Base):
# One row = one bank account. A user can own several.
    __tablename__ = "accounts"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False, index = True) # Owner of this account.
    account_number = Column(String, unique = True, nullable = False) # The number shown to the customer.
    balance = Column(Numeric(12,2), default = 0) # Numeric, not Float: money must be exact (Decimal).
    account_type = Column(String, default = "savings") # savings / current ...
    currency = Column(String, default = "HKD")
    status = Column(String, default = "active") # active / frozen / closed
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow) # onupdate: refreshed on every UPDATE.
    owner = relationship("User", back_populates = "accounts")
    