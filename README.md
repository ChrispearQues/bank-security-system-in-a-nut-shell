# Security Program

A homemade banking-security prototype — **for learning and testing only**.

## Project links

- Shared Perplexity session (notes & research): <https://www.perplexity.ai/projects/secured-area-JkVsgcn3R6yEDPL1PZf_rA>

## Tech stack

- **FastAPI** — web framework (routes, request handling, built-in `/docs` test page)
- **SQLAlchemy 2.0** — ORM: Python classes as database tables
- **SQLite** — the database, stored as the file `bank.db`
- **bcrypt** — password hashing

## Dependencies

All packages are pinned in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Local development & testing

Everything below is run from the project root (the folder that contains `app/`).

### 1. One-time setup

```bash
python3 -m venv .venv          # macOS / Linux
py -m venv .venv               # Windows

source .venv/bin/activate      # macOS / Linux  <- run again in every new terminal
.venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Run the app

```bash
uvicorn app.main:app --reload
```

- `--reload` restarts the server automatically when you save a file.
- Health check: <http://127.0.0.1:8000/health> -> `{"status": "ok"}`
- Interactive API docs (Swagger UI): <http://127.0.0.1:8000/docs> — click and send test requests from the browser.

### 3. Check the database

Importing `app.main` runs `Base.metadata.create_all()`, which creates `bank.db` (SQLite file in the project root) and any missing tables.

```bash
python -c "import app.main; from app.db.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

The current models produce:

```
['accounts', 'roles', 'sessions', 'user_roles', 'users']
```

To look at the rows visually, install the VS Code extension **SQLite Viewer** and click `bank.db`.

### 4. Reset the database

`create_all()` only creates tables that do not exist — it never alters an existing one. After editing a model, start over:

```bash
rm bank.db       # macOS / Linux
del bank.db      # Windows
```

Restart the app and `bank.db` is rebuilt from the current models.

### 5. Before you commit

- `.venv/` and `bank.db` are listed in `.gitignore` — never commit them.
- Run the app once: check `/health` and the table list above, then push.

## Project structure

```
app/
  main.py            FastAPI entry point: creates the app and the tables
  db/
    database.py      engine, SessionLocal, Base
  models/            one file per table (users, accounts, roles, sessions, ...)
  routes/            API endpoints (to be written)
  services/          business logic (to be written)
```

## Current status

Models implemented: `User`, `Account`, `Role` (+ `user_roles` link table), `UserSession`.

Still empty: `otp`, `transaction`, `audit_log` models; `routes/` and `services/` are placeholders.