"""Infraestrutura SQLAlchemy 2.0 (engine, Base declarativa tipada e sessão)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa SQLAlchemy 2.0 com tipagem nativa (Mapped/mapped_column)."""


_connect_args: dict[str, object] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Fornece uma sessão por requisição (dependência FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
