# Seed (初始化数据) — bootstrap roles, and optionally an admin from env vars.
#
#   ADMIN_USERNAME=root ADMIN_EMAIL=root@x.com ADMIN_PASSWORD='Aa1....' \
#       python -m app.db.seed
import os

from app import models  # noqa: F401  (register tables)
from app.db.database import Base, SessionLocal, engine
from app.models.role import Role
from app.models.user import User
from app.services import auth_service

DEFAULT_ROLES = [
    ("admin", "Full administrative access"),
    ("customer", "Standard account holder"),
]


def ensure_roles(db) -> list:
    created = []
    for name, description in DEFAULT_ROLES:
        if db.query(Role).filter(Role.name == name).first() is None:
            db.add(Role(name=name, description=description))
            created.append(name)
    db.commit()
    return created


def create_admin(db, username: str, email: str, password: str) -> User:
    ensure_roles(db)
    user = auth_service.get_user_by_identifier(db, username)
    if user is None:
        user = auth_service.register_user(db, username, email, password)
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role not in user.roles:
        user.roles.append(admin_role)
        db.commit()
        db.refresh(user)
    return user


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        created = ensure_roles(db)
        print(f"roles ensured (created: {created or 'none'})")
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        if username and email and password:
            user = create_admin(db, username, email, password)
            print(f"admin ready: {user.username} (id={user.id})")
        else:
            print("no ADMIN_* env set -> only roles were ensured")
    finally:
        db.close()


if __name__ == "__main__":
    main()
