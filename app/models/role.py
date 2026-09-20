# Role (角色) model — what a user is allowed to do (admin, teller, customer...).
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from app.db.database import Base

# Link table (关联表) for the many-to-many relation users <-> roles.
# It has no columns of its own, so a plain Table is enough (no class needed).
user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True), # Composite primary key (联合主键): the pair (user, role) must be unique.
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

class Role(Base):
# One row = one role. roles is the dictionary of identities; user_roles records who has which.
    __tablename__ = "roles"
    id = Column(Integer, primary_key = True, index  =True)
    name = Column(String,unique = True, index = True, nullable = False) # e.g. "admin", "customer"
    description = Column(String)
    created_at = Column(DateTime, default = datetime.utcnow)
    users = relationship("User", secondary = user_roles, back_populates = "roles")