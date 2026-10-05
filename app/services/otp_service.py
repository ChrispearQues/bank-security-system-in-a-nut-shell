# OTP service (一次性验证码服务) — the second factor.
#
# Attack-driven notes:
#   - short TTL + single-use        -> blocks replay of a captured code.
#   - per-code attempt cap          -> blocks online guessing of a 6-digit code.
#   - resend window limit           -> blocks SMS/email bombing & cost abuse.
#   - issuing a new code invalidates the previous one -> only one live code.
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.otp import OTPCode
from app.models.user import User

OTP_LENGTH = 6
OTP_TTL_SECONDS = 300          # a code lives 5 minutes
OTP_MAX_ATTEMPTS = 5           # wrong guesses allowed per issued code
OTP_RESEND_WINDOW_SECONDS = 900  # sliding window for the resend limit
OTP_MAX_PER_WINDOW = 3         # at most 3 codes per user+purpose per window


class OTPRateLimited(Exception):
    """Too many codes requested in the window -> 429 at the API layer."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Too many codes requested; retry in {retry_after}s")


def _generate_code() -> str:
    # secrets, not random: the code must not be predictable from a seed.
    return f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"


def _active_scope(db: DBSession, user_id: int, purpose: str):
    return db.query(OTPCode).filter(
        OTPCode.user_id == user_id,
        OTPCode.purpose == purpose,
    )


def issue_otp(db: DBSession, user: User, purpose: str = "login") -> str:
    """Create a fresh code, invalidate older ones, and enforce the resend limit.

    Returns the raw code (the caller "sends" it; we never persist plaintext
    sessions, but a 5-minute OTP is fine to store as-is).
    """
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=OTP_RESEND_WINDOW_SECONDS)

    recent = _active_scope(db, user.id, purpose).filter(
        OTPCode.created_at >= window_start
    ).order_by(OTPCode.created_at.asc()).all()
    if len(recent) >= OTP_MAX_PER_WINDOW:
        oldest = recent[0]
        retry_after = int(
            (oldest.created_at + timedelta(seconds=OTP_RESEND_WINDOW_SECONDS) - now)
            .total_seconds()
        ) + 1
        raise OTPRateLimited(max(retry_after, 1))

    # Only one code stays live at a time.
    _active_scope(db, user.id, purpose).filter(OTPCode.used.is_(False)).update(
        {"used": True}, synchronize_session=False
    )
    code = _generate_code()
    db.add(
        OTPCode(
            user_id=user.id,
            code=code,
            purpose=purpose,
            expires_at=now + timedelta(seconds=OTP_TTL_SECONDS),
        )
    )
    db.commit()
    return code


def verify_otp(db: DBSession, user: User, code: str, purpose: str = "login") -> bool:
    """Consume the latest active code. Single-use; wrong guesses burn attempts."""
    now = datetime.utcnow()
    row = (
        _active_scope(db, user.id, purpose)
        .filter(OTPCode.used.is_(False))
        .order_by(OTPCode.created_at.desc())
        .first()
    )
    if row is None:
        return False
    if row.expires_at < now or row.attempts >= OTP_MAX_ATTEMPTS:
        row.used = True
        db.commit()
        return False
    if not hmac.compare_digest(row.code, code):
        row.attempts += 1
        if row.attempts >= OTP_MAX_ATTEMPTS:
            row.used = True  # too many guesses: kill the code
        db.commit()
        return False
    row.used = True  # success -> single-use
    db.commit()
    return True
