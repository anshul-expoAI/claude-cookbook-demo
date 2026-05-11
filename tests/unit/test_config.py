from __future__ import annotations

import pytest


@pytest.mark.unit
def test_settings_defaults():
    from app.config import Settings

    s = Settings()
    assert s.database_url == "sqlite:///./shortener.db"
    assert s.base_url == "http://localhost:8000"
    assert s.code_length == 5
    assert s.max_retries == 5
    assert s.log_level == "INFO"
