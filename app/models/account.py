from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False, index = True)
    account_number = Column(String, unique = True, nullable = False)
    balance = Column(Numeric(12,2), default = 0)
    account_type = Column(String, default = "savings")
    currency = Column(String, default = "HKD")
    status = Column(String, default = "active")
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)
    owner = relationship("User", back_populates= "accounts")
    