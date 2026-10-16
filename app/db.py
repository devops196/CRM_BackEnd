import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Render's hosted PostgreSQL requires SSL for external connections.
# psycopg v3 needs sslmode passed via connect_args rather than a URL param.
# When running locally (localhost / 127.0.0.1) we skip SSL so the dev
# experience stays smooth with a plain Docker or local Postgres instance.
_db_url = settings.DATABASE_URL
_needs_ssl = (
    "render.com" in _db_url
    or "sslmode=require" in _db_url
    or os.getenv("DATABASE_REQUIRE_SSL", "").lower() in ("1", "true", "yes")
)
_connect_args = {"sslmode": "require"} if _needs_ssl else {}

engine = create_engine(
    _db_url,
    pool_pre_ping=True,   # cheaply recycles dead connections after idle
    pool_size=5,          # small pool suitable for Render's free tier
    max_overflow=10,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
