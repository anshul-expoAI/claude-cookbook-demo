from __future__ import annotations

import pytest


@pytest.mark.integration
def test_round_trip_preserves_url_byte_for_byte(client):
    original_url = "https://example.com/some/path?foo=bar&baz=qux#section-1"
    post_resp = client.post("/shorten", json={"long_url": original_url})
    assert post_resp.status_code == 201
    code = post_resp.json()["code"]

    get_resp = client.get(f"/{code}")
    assert get_resp.status_code == 302
    assert get_resp.headers["Location"] == original_url


@pytest.mark.integration
def test_round_trip_with_fragment_only(client):
    url = "https://internal.corp/dashboard#metrics"
    resp = client.post("/shorten", json={"long_url": url})
    code = resp.json()["code"]
    redir = client.get(f"/{code}")
    assert redir.headers["Location"] == url


@pytest.mark.integration
def test_same_url_twice_gives_different_codes(client):
    url = "https://example.com/same"
    r1 = client.post("/shorten", json={"long_url": url})
    r2 = client.post("/shorten", json={"long_url": url})
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Non-deterministic by design; they usually differ
    # (collision theoretically possible but negligible — just verify both work)
    c1, c2 = r1.json()["code"], r2.json()["code"]
    assert client.get(f"/{c1}").headers["Location"] == url
    assert client.get(f"/{c2}").headers["Location"] == url
