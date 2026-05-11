from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
def test_alembic_upgrade_creates_links_table(tmp_path):
    import subprocess, os
    db = tmp_path / "test.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True, text=True, env=env,
        cwd=str(Path(__file__).parents[2]),
    )
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}"
    conn = sqlite3.connect(db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='links'")
    assert cur.fetchone() is not None, "links table not created"
    cols = {row[1] for row in conn.execute("PRAGMA table_info(links)")}
    assert {"id", "code", "long_url", "created_at"} == cols
    conn.close()


@pytest.mark.unit
def test_alembic_upgrade_code_unique(tmp_path):
    import subprocess, os, sqlite3
    db = tmp_path / "test.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], env=env,
                   capture_output=True, cwd=str(Path(__file__).parents[2]))
    conn = sqlite3.connect(db)
    indexes = {row[1] for row in conn.execute("PRAGMA index_list(links)")}
    unique_on_code = any(
        "code" in [r[2] for r in conn.execute(f"PRAGMA index_info({idx})")]
        for idx in indexes
    )
    assert unique_on_code, "No unique index on links.code"
    conn.close()


@pytest.mark.unit
def test_alembic_downgrade_drops_table(tmp_path):
    import subprocess, os, sqlite3
    db = tmp_path / "test.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}"}
    cwd = str(Path(__file__).parents[2])
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], env=env,
                   capture_output=True, cwd=cwd)
    result = subprocess.run(["uv", "run", "alembic", "downgrade", "base"], env=env,
                            capture_output=True, text=True, cwd=cwd)
    assert result.returncode == 0, f"downgrade failed:\n{result.stderr}"
    conn = sqlite3.connect(db)
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='links'")
    assert cur.fetchone() is None, "links table still exists after downgrade"
    conn.close()
