# bank-security-system-in-a-nut-shell

> An attack-driven, minimal core-banking ledger — **every security control is
> justified by the attack it stops.**

A homemade banking-security prototype — **for learning and testing only**.
See [`SECURITY.md`](SECURITY.md) for the threat model.

## Project links

- Shared Perplexity session (notes & research): <https://www.perplexity.ai/projects/secured-area-JkVsgcn3R6yEDPL1PZf_rA>

## Tech stack

- **FastAPI** — web framework (routes, request handling, built-in `/docs` page)
- **SQLAlchemy 2.0** — ORM: Python classes as database tables
- **SQLite** — the database, stored as the file `bank.db` (dev)
- **bcrypt** — password hashing
- **pytest + ruff + GitHub Actions** — tests, lint, CI

## Quick start

Run everything from the project root (the folder that contains `app/`).

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health check: <http://127.0.0.1:8000/health> -> `{"status": "ok"}`
- Interactive API docs (Swagger UI): <http://127.0.0.1:8000/docs>

### Bootstrap roles & an admin

```bash
ADMIN_USERNAME=root ADMIN_EMAIL=root@example.com ADMIN_PASSWORD='Aa1Admin0001' \
  python -m app.db.seed
```

This creates the `admin` / `customer` roles and an admin account (idempotent).

### Reset the database

`create_all()` only creates missing tables — it never alters existing ones.
After editing a model, delete and rebuild:

```bash
rm bank.db        # Windows: del bank.db
```

### Tests & lint

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

## API overview

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | – | Create a user |
| POST | `/auth/login` | – | Verify password → **send OTP** (step 1) |
| POST | `/otp/verify` | – | Exchange OTP for a session token (step 2) |
| POST | `/otp/resend` | – | Re-send the OTP (rate-limited) |
| POST | `/auth/logout` | Bearer | Revoke the current token |
| GET | `/auth/me` | Bearer | Current user |
| POST | `/accounts` | Bearer | Open an account |
| GET | `/accounts` | Bearer | List my accounts |
| GET | `/accounts/{number}` | Bearer | One account (owner/admin) |
| POST | `/accounts/{number}/freeze` | Bearer | Freeze (owner/admin) |
| POST | `/transactions/transfer` | Bearer | Atomic, idempotent transfer |
| GET | `/transactions` | Bearer | My ledger entries |
| GET | `/admin/users` … | **admin** | User & role administration |
| GET | `/admin/accounts`, `/admin/audit-logs` | **admin** | Accounts & audit trail |

Login is two-step by design: the OTP is printed to the server console
(standing in for email/SMS) and never returned in the HTTP response.

## Security model at a glance

Each control maps to a concrete attack (full table in [`SECURITY.md`](SECURITY.md)):

- bcrypt password hashes & **SHA-256-hashed** session tokens → survive a DB leak
- login lockout (per identity + per IP) → stops brute force & credential stuffing
- single-use, short-lived OTP with attempt **and** resend caps → stops replay/guessing/bombing
- **atomic conditional debit + idempotency key** → no double-spend, no overdraft
- append-only audit log + role-gated admin routes → no repudiation, no privilege escalation

## Roadmap

- [x] **M0** — runnable skeleton
- [x] **M1** — data layer (8 tables)
- [x] **M2** — auth & security (bcrypt, token hashing, policy, lockout)
- [x] **M3** — OTP / 2FA second factor
- [x] **M4** — accounts & transactions (atomic, idempotent)
- [x] **M5** — admin & audit
- [x] **M6** — quality & delivery (pytest, ruff, CI, LICENSE, SECURITY.md)
- [ ] **M7** — showcase & distribution (technical write-up + demo)

## Project structure

```
app/
  main.py            FastAPI entry point: creates the app and the tables
  schemas.py         request / response models (pydantic)
  db/
    database.py      engine, SessionLocal, Base, get_db()
    seed.py          role + admin bootstrap
  models/            one file per table (users, accounts, roles, sessions,
                     otp_codes, transactions, audit_logs)
  routes/            auth, otp, accounts, transactions, admin, deps
  services/          auth, security, otp, account, transaction, admin, logging
tests/               pytest suite (auth, otp, accounts, admin)
```

## Data model

8 tables (7 models + the `user_roles` link table):

- `User` → `users` — account holders
- `Account` → `accounts` — bank accounts, owned by a user
- `Role` → `roles` (+ `user_roles`) — many-to-many with users
- `UserSession` → `sessions` — login tokens (stored hashed)
- `OTPCode` → `otp_codes` — one-time codes (login / transfer / reset)
- `Transaction` → `transactions` — ledger (single-sided: one row per movement)
- `AuditLog` → `audit_logs` — append-only audit trail
