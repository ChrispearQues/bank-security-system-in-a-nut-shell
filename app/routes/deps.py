# Shared route dependencies (路由公共依赖).
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.user import User
from app.services import auth_service


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: DBSession = Depends(get_db),
) -> User:
    """Turn an `Authorization: Bearer <token>` header into the current user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    user = auth_service.get_user_by_token(db, token)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
