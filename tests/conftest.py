from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).parents[1]


@pytest.fixture()
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    env = {**os.environ, "DATABASE_URL": db_url}
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        env=env,
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True,
    )
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    from app.main import app
    from app.deps import get_db

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, follow_redirects=False) as c:
        yield c
    app.dependency_overrides.clear()
