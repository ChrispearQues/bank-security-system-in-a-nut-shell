# Database (数据库) wiring — engine + session factory + Base, shared by the whole app.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./bank.db" # Relative path: the file is created in the project root.

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # SQLite only: let one connection be used from several threads (FastAPI).
)

# Factory of database sessions (数据库会话): one session per request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Parent class of every model; it collects the table definitions (metadata).
Base = declarative_base()