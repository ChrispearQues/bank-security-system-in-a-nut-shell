# FastAPI entry point (入口) — create the app and its tables.
from fastapi import FastAPI

from app.db.database import Base, engine
from app import models # Side effect: registers every model on Base.metadata.

# Creates bank.db and any missing table (it never changes existing tables).
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health") # GET http://127.0.0.1:8000/health
def health_check():
    return {"status": "ok"}