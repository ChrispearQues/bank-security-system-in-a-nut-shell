from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from app.db.database import Base

user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key = True, index  =True)
    name = Column(String,unique = True, index = True, nullable = False)
    description = Column(String)
    created_at = Column(DateTime, default = datetime.utcnow)
    users = relationship("User", secondary = user_roles, back_populates = "roles")