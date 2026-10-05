# Auth routes (认证路由) — register / login / logout / me.
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.user import User
from app.services import auth_service, logging_service
from app.services.security_service import (
    AccountLockedError,
    PasswordPolicyError,
    login_throttle,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------- Request / response shapes (数据形状) ----------
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=3, max_length=255)
    password: str


class LoginRequest(BaseModel):
    identifier: str = Field(description="Username or email")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool


# ---------- Dependency: turn a Bearer token into the current user ----------
def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: DBSession = Depends(get_db),
) -> User:
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


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# ---------- Routes ----------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: DBSession = Depends(get_db)):
    try:
        user = auth_service.register_user(
            db, payload.username, payload.email, payload.password
        )
    except PasswordPolicyError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except ValueError as exc:  # duplicate username / email
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))

    logging_service.log_action(
        db, "user.register", user_id=user.id, entity="users", entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: DBSession = Depends(get_db)):
    ip = _client_ip(request)
    keys = [f"user:{payload.identifier.lower()}", f"ip:{ip}"]

    # Lockout check: a locked identity or IP cannot even try.
    for key in keys:
        try:
            login_throttle.check(key)
        except AccountLockedError as exc:
            logging_service.log_action(
                db, "login.locked", detail=payload.identifier, ip_address=ip,
                status="blocked",
            )
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many failed attempts, try again later.",
                headers={"Retry-After": str(exc.retry_after)},
            )

    user = auth_service.authenticate(db, payload.identifier, payload.password)
    if user is None:
        for key in keys:
            login_throttle.record_failure(key)
        logging_service.log_action(
            db, "login.failed", detail=payload.identifier, ip_address=ip,
            status="failure",
        )
        # Generic message: never reveal whether the identifier exists.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    for key in keys:
        login_throttle.reset(key)
    token = auth_service.create_session(db, user)
    logging_service.log_action(
        db, "login.success", user_id=user.id, entity="sessions",
        ip_address=ip,
    )
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    authorization: Optional[str] = Header(default=None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = authorization.split(" ", 1)[1].strip() if authorization else ""
    auth_service.revoke_session(db, token)
    logging_service.log_action(
        db, "logout", user_id=current_user.id, entity="sessions",
    )
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
