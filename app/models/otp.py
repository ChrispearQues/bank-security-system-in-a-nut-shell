from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class OTPCode(Base):
    __tablename__ = "otp_codes"
    
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False, index = True)
    code = Column(String(6), nullable = False)
    expires_at = Column(DateTime, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)
    used = Column(Boolean, default = False)
    purpose = Column(String, default = "login")
    attempts = Column(Integer, default = 0)
    
    user = relationship("User", back_populates="otps")