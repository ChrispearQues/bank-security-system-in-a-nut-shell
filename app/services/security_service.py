# Security service (安全服务) — the defensive controls, each one justified by the
# attack it stops (attack-driven design):
#   - validate_password_strength -> blocks weak / guessable passwords (brute force).
#   - LoginThrottle              -> blocks credential stuffing & online brute force.
#   - hash_token / verify_token  -> blocks session theft from a leaked database:
#                                   the DB only ever holds an irreversible hash.
import hashlib
import hmac
import re
import secrets
import time

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # bcrypt only hashes the first 72 bytes, so we reject longer.

_LETTER = re.compile(r"[A-Za-z]")
_DIGIT = re.compile(r"\d")


class PasswordPolicyError(ValueError):
    """Password fails the policy -> 400 at the API layer."""


class AccountLockedError(Exception):
    """Too many failed logins -> 429 at the API layer."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Too many failed attempts; retry in {retry_after}s")


def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise PasswordPolicyError(
            f"Password must be at most {MAX_PASSWORD_BYTES} bytes."
        )
    if not _LETTER.search(password) or not _DIGIT.search(password):
        raise PasswordPolicyError("Password must contain both letters and digits.")


def generate_token() -> str:
    """High-entropy session token (通行证). 32 random bytes, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Deterministic hash so we can look a token up by primary position.

    SHA-256 (not bcrypt) is the right tool here: the token is already 256 bits
    of randomness, so it is not brute-forceable, and we need a fast, indexable,
    constant lookup on every authenticated request.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), token_hash)


class LoginThrottle:
    """Sliding-window lockout, keyed per identity and per client IP.

    Kept in memory so the demo has zero extra dependencies; production would
    move these counters to Redis so every worker shares them.
    """

    def __init__(self, max_failures: int = 5, window_seconds: int = 900, lock_seconds: int = 900):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}

    def check(self, key: str) -> None:
        """Raise AccountLockedError if `key` is currently locked out."""
        until = self._locked_until.get(key)
        if until is None:
            return
        remaining = until - time.monotonic()
        if remaining > 0:
            raise AccountLockedError(int(remaining) + 1)
        self._locked_until.pop(key, None)

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        stamps = [t for t in self._failures.get(key, []) if now - t < self.window_seconds]
        stamps.append(now)
        self._failures[key] = stamps
        if len(stamps) >= self.max_failures:
            self._locked_until[key] = now + self.lock_seconds

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
        self._locked_until.pop(key, None)

    def retry_after(self, key: str) -> int:
        until = self._locked_until.get(key)
        if until is None:
            return 0
        return max(0, int(until - time.monotonic()) + 1)


# One shared instance for the whole process.
login_throttle = LoginThrottle()
