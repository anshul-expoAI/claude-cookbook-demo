from __future__ import annotations

import pytest


@pytest.mark.unit
def test_app_is_fastapi_instance():
    from fastapi import FastAPI
    from app.main import app
    assert isinstance(app, FastAPI)


@pytest.mark.unit
def test_healthz_route_registered():
    from app.main import app
    routes = {r.path for r in app.routes}
    assert "/healthz" in routes


@pytest.mark.unit
def test_shorten_route_registered():
    from app.main import app
    routes = {r.path for r in app.routes}
    assert "/shorten" in routes


@pytest.mark.unit
def test_redirect_route_registered():
    from app.main import app
    routes = {r.path for r in app.routes}
    assert "/{code}" in routes
