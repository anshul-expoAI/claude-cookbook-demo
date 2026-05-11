from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Re-exported so routes type-hint from app.deps, not sqlalchemy directly.
DBSession = Session

from app.config import Settings

_settings = Settings()
_engine = create_engine(_settings.database_url, connect_args={"check_same_thread": False})


def get_db() -> Generator[Session, None, None]:
    with Session(_engine) as session:
        yield session


def require_auth() -> None:
    """No-op JWT seam — replaced when auth lands."""
    return None
