from __future__ import annotations

import pytest


@pytest.mark.integration
def test_post_shorten_happy_path(client):
    resp = client.post("/shorten", json={"long_url": "https://example.com/path?q=1#frag"})
    assert resp.status_code == 201
    body = resp.json()
    assert "code" in body
    assert len(body["code"]) in (5, 6)
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
               for c in body["code"])
    assert body["short_url"].endswith(f"/{body['code']}")
    assert body["long_url"] == "https://example.com/path?q=1#frag"


@pytest.mark.integration
def test_post_shorten_fragment_preserved(client):
    url = "https://example.com/page#section-2"
    resp = client.post("/shorten", json={"long_url": url})
    assert resp.status_code == 201
    assert resp.json()["long_url"] == url


@pytest.mark.integration
@pytest.mark.parametrize("scheme_url", [
    "javascript:alert(1)",
    "data:text/html,<h>x</h>",
    "file:///etc/passwd",
    "ftp://ftp.example.com/file",
])
def test_post_shorten_rejects_disallowed_schemes(client, scheme_url):
    resp = client.post("/shorten", json={"long_url": scheme_url})
    assert resp.status_code == 422


@pytest.mark.integration
def test_post_shorten_rejects_oversize_url(client):
    url = "https://example.com/" + "a" * 2048
    resp = client.post("/shorten", json={"long_url": url})
    assert resp.status_code == 422


@pytest.mark.integration
def test_post_shorten_rejects_missing_long_url(client):
    resp = client.post("/shorten", json={})
    assert resp.status_code == 422
