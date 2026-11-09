import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Try loading .env from backend/.env or root .env if present
for parent in (Path(__file__).resolve().parents[1], Path(__file__).resolve().parents[2]):
    env_candidate = parent / ".env"
    if env_candidate.is_file():
        load_dotenv(dotenv_path=env_candidate, override=True)
        break

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("DB_URL")
    or os.getenv("RENDER_POSTGRES_INTERNAL_URL")
    or os.getenv("RENDER_POSTGRES_EXTERNAL_URL")
)

if not DATABASE_URL:
    if os.getenv("RENDER"):
        raise RuntimeError(
            "DATABASE_URL is missing in Render! Go to your Web Service -> Environment "
            "and add DATABASE_URL with your Render PostgreSQL connection string."
        )
    DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/internal_crm"

DATABASE_URL = DATABASE_URL.strip().strip("'\"")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Ensure sslmode=require for Render external Postgres if not already present
if "render.com" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
