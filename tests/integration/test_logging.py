from __future__ import annotations

import logging
import pytest


@pytest.mark.integration
def test_post_shorten_logs_code_and_scheme_host_only(client, caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        resp = client.post(
            "/shorten",
            json={"long_url": "https://example.com/secret/path?token=abc123#frag"},
        )
    assert resp.status_code == 201
    code = resp.json()["code"]

    info_msgs = [r.message for r in caplog.records if r.levelno == logging.INFO]
    assert any(code in m for m in info_msgs), f"code {code!r} not in logs: {info_msgs}"
    assert any("https://example.com" in m for m in info_msgs)
    # Must NOT contain path, query, or fragment
    for m in info_msgs:
        if code in m:
            assert "/secret/path" not in m, f"Path leaked in log: {m!r}"
            assert "token=abc123" not in m, f"Query leaked in log: {m!r}"
            assert "frag" not in m, f"Fragment leaked in log: {m!r}"


@pytest.mark.integration
def test_redirect_404_emits_warning(client, caplog):
    with caplog.at_level(logging.WARNING, logger="app"):
        resp = client.get("/zzzzz")
    assert resp.status_code == 404
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("zzzzz" in r.message for r in warnings), \
        f"No WARNING log for 404: {[r.message for r in warnings]}"
