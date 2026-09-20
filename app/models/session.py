# Login session (登录会话) model — records the tokens handed out to users.
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserSession(Base):
# One row = one issued token, i.e. one active login (一张已发出的通行证).
    __tablename__ = "sessions" # Class name is UserSession to avoid clashing with sqlalchemy.orm.Session (数据库会话).
    
    id = Column(Integer, primary_key= True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False, index = True) # Whose token this is.
    token = Column(String, unique = True, index = True, nullable = False) # The pass itself, generated with secrets.token_urlsafe(32) at login time.
    expires_at = Column(DateTime, nullable = False) # No default: computed at login as utcnow() + 24h.
    created_at = Column(DateTime, default = datetime.utcnow)
    revoked = Column(Boolean, default = False)
    
    user = relationship("User", back_populates="sessions")