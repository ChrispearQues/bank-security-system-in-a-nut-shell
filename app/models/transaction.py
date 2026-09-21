from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key = True, index = True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable = False, index = True)
    type = Column(String, nullable = False)
    amount = Column(Numeric(12,2), nullable = False)
    balance_after = Column(Numeric(12,2))
    status = Column(String, default = "completed")
    reference = Column(String, unique = True, index = True)
    description = Column(String)
    currency = Column(String, default = "HKD")
    created_at = Column(DateTime, default = datetime.utcnow)
    
    account = relationship("Account", back_populates="transactions")