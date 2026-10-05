# FastAPI entry point (入口) — create the app and its tables.
from fastapi import FastAPI

from app.db.database import Base, engine
from app.routes.accounts import router as accounts_router
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.otp import router as otp_router
from app.routes.transactions import router as transactions_router

# Creates bank.db and any missing table (it never changes existing tables).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="bank-security-system-in-a-nut-shell")

app.include_router(auth_router)
app.include_router(otp_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(admin_router)

@app.get("/health") # GET http://127.0.0.1:8000/health
def health_check():
    return {"status": "ok"}
