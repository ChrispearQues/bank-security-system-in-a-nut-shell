# Security model — threats, controls, and what's still missing

This project is **attack-driven**: every control below exists to stop a specific,
named attack. If a control has no attack behind it, it does not belong here.

> Prototype for learning only. It is **not** production-ready — see
> [Known gaps](#known-gaps) for the honest list of what is missing.

## Scope & trust boundaries

- **Assets:** user credentials, session tokens, account balances, the audit trail.
- **Entry points:** the HTTP API (`/auth`, `/otp`, `/accounts`, `/transactions`, `/admin`).
- **Trust boundary:** everything arriving over HTTP is untrusted; the database is
  trusted storage, but a leak of it must **not** hand over usable secrets.
- **Out of scope:** network/TLS, host hardening, the email/SMS channel that would
  deliver OTPs (stubbed here by a server-side print).

## Controls → attacks they stop

| Control | Where | Attack it stops |
| --- | --- | --- |
| Passwords stored as **bcrypt** hashes (per-password salt) | `auth_service.hash_password` | Offline cracking after a database leak |
| Session tokens stored as **SHA-256 hashes**, never plaintext | `auth_service.create_session` | Session theft via a database leak — a stolen row is useless |
| Passwords require length + letters + digits, ≤ 72 bytes | `security_service.validate_password_strength` | Weak/guessable passwords; bcrypt 72-byte truncation abuse |
| **Login lockout** — 5 failures, per identity *and* per IP, 15 min | `security_service.LoginThrottle` | Online brute force and credential stuffing |
| Generic `401 Invalid credentials` for any bad login | `routes/auth` | Username/email enumeration |
| OTP: **6 digits, 5-min TTL, single-use** | `otp_service.verify_otp` | Replay of a captured/observed code |
| OTP: **5-attempt cap** per issued code | `otp_service.verify_otp` | Online guessing of a 6-digit code |
| OTP: **resend limit** (max 3 / 15 min) + new code invalidates the old | `otp_service.issue_otp` | SMS/email bombing and cost abuse; multiple live codes |
| Resource not owned → **404, not 403** | `routes/accounts`, `routes/transactions` | Resource enumeration / confirming an account exists |
| **Atomic, conditional debit** (`balance >= amount`) in one transaction | `transaction_service.transfer` | Double-spend and race conditions (overdraft) |
| **Idempotency key** on transfers | `transaction_service.transfer` | A retried request moving money twice |
| **Append-only audit log** on every sensitive action | `logging_service.log_action` | Repudiation — who did what, when, from where |
| Role-gated admin routes (`403` without `admin`) | `routes/admin` | Horizontal/vertical privilege escalation |

## Known gaps

Not (yet) addressed — deliberately left visible:

- No TLS / rate limiting at the edge; throttling is **in-process** (single worker).
  A multi-worker deployment needs a shared store (e.g. Redis).
- No account-lockout notification, no password reset flow.
- OTP delivery is stubbed (server log) — no real email/SMS integration.
- SQLite is dev-only; balance locking relies on the conditional `UPDATE` + SQLite's
  writer serialization, not on row-level `SELECT ... FOR UPDATE`.
- No secrets management: `DATABASE_URL` and admin bootstrap come from environment variables.
- Tokens have a fixed 24-hour TTL and no refresh/rotation.

## Reporting

This is a personal learning project. Found something? Open an issue.
