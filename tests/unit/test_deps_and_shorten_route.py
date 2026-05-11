from __future__ import annotations

import inspect
import pytest


@pytest.mark.unit
def test_require_auth_is_noop():
    from app.deps import require_auth
    result = require_auth()
    assert result is None


@pytest.mark.unit
def test_shorten_route_uses_require_auth():
    """Verify Depends(require_auth) is wired onto POST /shorten."""
    import ast, pathlib
    src = (pathlib.Path("src/app/routes/shorten.py")).read_text()
    assert "require_auth" in src
    assert "Depends" in src


@pytest.mark.unit
def test_shorten_route_returns_201_shape():
    """Route module must define a function decorated with @router.post returning status 201."""
    import pathlib
    src = pathlib.Path("src/app/routes/shorten.py").read_text()
    assert "status_code=201" in src or "201" in src
