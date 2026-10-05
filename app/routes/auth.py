# Auth routes (认证路由) — register / login (1st factor) / logout / me.
# The 2nd factor lives in routes/otp.py.
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.models.user import User
from app.routes.deps import client_ip, get_current_user
from app.schemas import (
    LoginRequest,
    OtpChallengeResponse,
    RegisterRequest,
    UserResponse,
)
from app.services import auth_service, logging_service, otp_service
from app.services.security_service import (
    AccountLockedError,
    PasswordPolicyError,
    login_throttle,
)
from app.services.otp_service import OTPRateLimited

router = APIRouter(prefix="/auth", tags=["auth"])


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
        ip_address=client_ip(request),
    )
    return user


@router.post("/login", response_model=OtpChallengeResponse)
def login(payload: LoginRequest, request: Request, db: DBSession = Depends(get_db)):
    """Step 1 — verify the password, then send a one-time code."""
    ip = client_ip(request)
    keys = [f"user:{payload.identifier.lower()}", f"ip:{ip}"]

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
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    for key in keys:
        login_throttle.reset(key)

    try:
        code = otp_service.issue_otp(db, user, "login")
    except OTPRateLimited as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many codes requested, try again later.",
            headers={"Retry-After": str(exc.retry_after)},
        )
    print(f"[OTP] login user={user.id} {user.email} code={code}")  # stands in for email/SMS
    logging_service.log_action(
        db, "otp.issued", user_id=user.id, entity="otp_codes", ip_address=ip,
    )
    return OtpChallengeResponse()


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
