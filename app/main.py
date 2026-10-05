# FastAPI entry point (入口) — create the app and its tables.
from fastapi import FastAPI

from app.db.database import Base, engine
from app import models # Side effect: registers every model on Base.metadata.
from app.routes.auth import router as auth_router
from app.routes.otp import router as otp_router

# Creates bank.db and any missing table (it never changes existing tables).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="bank-security-system-in-a-nut-shell")

app.include_router(auth_router)
app.include_router(otp_router)

@app.get("/health") # GET http://127.0.0.1:8000/health
def health_check():
    return {"status": "ok"}