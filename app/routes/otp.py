# OTP routes (一次性验证码路由) — the second factor at login.
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DBSession

from app.db.database import get_db
from app.routes.deps import client_ip
from app.schemas import OtpChallengeResponse, OtpResendRequest, OtpVerifyRequest, TokenResponse
from app.services import auth_service, logging_service, otp_service
from app.services.otp_service import OTPRateLimited
from app.services.security_service import AccountLockedError, login_throttle

router = APIRouter(prefix="/otp", tags=["otp"])


@router.post("/verify", response_model=TokenResponse)
def verify_otp(payload: OtpVerifyRequest, request: Request, db: DBSession = Depends(get_db)):
    """Step 2 — exchange a valid code for a session token."""
    ip = client_ip(request)
    key = f"otp:{payload.identifier.lower()}"

    try:
        login_throttle.check(key)
    except AccountLockedError as exc:
        logging_service.log_action(
            db, "otp.locked", detail=payload.identifier, ip_address=ip, status="blocked",
        )
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts, try again later.",
            headers={"Retry-After": str(exc.retry_after)},
        )

    user = auth_service.get_user_by_identifier(db, payload.identifier)
    if user is None or not otp_service.verify_otp(db, user, payload.code, "login"):
        login_throttle.record_failure(key)
        logging_service.log_action(
            db, "otp.failed", user_id=(user.id if user else None), detail=payload.identifier,
            ip_address=ip, status="failure",
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired code")

    login_throttle.reset(key)
    token = auth_service.create_session(db, user)
    logging_service.log_action(
        db, "login.success", user_id=user.id, entity="sessions", detail="2fa", ip_address=ip,
    )
    return TokenResponse(access_token=token)


@router.post("/resend", response_model=OtpChallengeResponse)
def resend_otp(payload: OtpResendRequest, request: Request, db: DBSession = Depends(get_db)):
    """Re-issue a code. Rate-limited; response is identical whether the user exists."""
    ip = client_ip(request)
    user = auth_service.get_user_by_identifier(db, payload.identifier)
    if user is not None:
        try:
            code = otp_service.issue_otp(db, user, "login")
        except OTPRateLimited as exc:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many codes requested, try again later.",
                headers={"Retry-After": str(exc.retry_after)},
            )
        print(f"[OTP] resend user={user.id} {user.email} code={code}")
        logging_service.log_action(
            db, "otp.resend", user_id=user.id, entity="otp_codes", ip_address=ip,
        )
    return OtpChallengeResponse(detail="If the account exists, a new code was sent.")
