# Auth service (认证服务) — password hashing plus the login / session lifecycle.
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from sqlalchemy.orm import Session as DBSession

from app.models.session import UserSession
from app.models.user import User
from app.services import security_service as security

SESSION_TTL_HOURS = 24


def hash_password(password: str) -> str:
    """bcrypt hash with a per-password salt. Users never store a raw password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed / legacy hash -> treat as a failed login, never crash.
        return False


def get_user_by_identifier(db: DBSession, identifier: str) -> Optional[User]:
    """Look a user up by username *or* email (both are unique login identities)."""
    return (
        db.query(User)
        .filter((User.username == identifier) | (User.email == identifier))
        .first()
    )


def register_user(db: DBSession, username: str, email: str, password: str) -> User:
    security.validate_password_strength(password)
    if get_user_by_identifier(db, username) or get_user_by_identifier(db, email):
        raise ValueError("Username or email already registered.")
    user = User(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: DBSession, identifier: str, password: str) -> Optional[User]:
    user = get_user_by_identifier(db, identifier)
    if user is None or not user.is_active:
        # Same result for "no such user" and "wrong password" -> no user enumeration.
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: DBSession, user: User) -> str:
    """Issue a token and persist only its hash. Returns the raw token once."""
    token = security.generate_token()
    db.add(
        UserSession(
            user_id=user.id,
            token=security.hash_token(token),  # stored hashed, never plaintext
            expires_at=datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
        )
    )
    db.commit()
    return token


def get_user_by_token(db: DBSession, token: str) -> Optional[User]:
    if not token:
        return None
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token == security.hash_token(token),
            UserSession.revoked.is_(False),
        )
        .first()
    )
    if session is None:
        return None
    if session.expires_at < datetime.utcnow():
        session.revoked = True  # lazy cleanup of the expired token
        db.commit()
        return None
    return session.user


def revoke_session(db: DBSession, token: str) -> bool:
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token == security.hash_token(token),
            UserSession.revoked.is_(False),
        )
        .first()
    )
    if session is None:
        return False
    session.revoked = True
    db.commit()
    return True
