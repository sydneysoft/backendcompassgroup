import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()
database_url = settings.database_url

# Vercel Functions have a read-only application filesystem. For the sandbox
# deployment, keep the local SQLite database in the writable /tmp directory.
# A production deployment should set DATABASE_URL to a persistent PostgreSQL DB.
if os.getenv("VERCEL") and database_url == "sqlite+pysqlite:///./busapp.db":
    database_url = "sqlite+pysqlite:////tmp/busapp.db"

engine_kwargs: dict = {"pool_pre_ping": True}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if ":memory:" in database_url:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
