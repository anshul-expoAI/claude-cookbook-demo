from __future__ import annotations

import pytest


@pytest.mark.integration
def test_healthz_returns_200_ok(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
