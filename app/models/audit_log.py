from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = True, index = True)
    action = Column(String, nullable = False)
    entity = Column(String)
    entity_id = Column(Integer)
    detail = Column(String)
    ip_address = Column(String)
    status = Column(String, default = "success")
    created_at = Column(DateTime, default = datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")