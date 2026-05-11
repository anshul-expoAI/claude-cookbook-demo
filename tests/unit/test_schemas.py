from __future__ import annotations

import pytest
from pydantic import ValidationError


@pytest.mark.unit
@pytest.mark.parametrize("url", [
    "http://example.com",
    "https://example.com/path?q=1#frag",
    "http://internal.corp/dashboard",
    "https://a.b.c/d?e=f&g=h",
])
def test_shorten_request_accepts_valid_urls(url):
    from app.schemas.link import ShortenRequest
    req = ShortenRequest(long_url=url)
    assert req.long_url == url


@pytest.mark.unit
@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "data:text/html,<h1>hi</h1>",
    "file:///etc/passwd",
    "ftp://ftp.example.com/file",
    "//no-scheme.example.com",
    "not-a-url-at-all",
    "chrome://settings",
])
def test_shorten_request_rejects_disallowed_schemes(url):
    from app.schemas.link import ShortenRequest
    with pytest.raises(ValidationError):
        ShortenRequest(long_url=url)


@pytest.mark.unit
def test_shorten_request_rejects_oversize_url():
    from app.schemas.link import ShortenRequest
    url = "https://example.com/" + "a" * 2048
    with pytest.raises(ValidationError):
        ShortenRequest(long_url=url)


@pytest.mark.unit
def test_shorten_request_rejects_extra_fields():
    from app.schemas.link import ShortenRequest
    with pytest.raises(ValidationError):
        ShortenRequest(long_url="https://example.com", extra_field="bad")


@pytest.mark.unit
def test_shorten_request_rejects_missing_long_url():
    from app.schemas.link import ShortenRequest
    with pytest.raises(ValidationError):
        ShortenRequest()


@pytest.mark.unit
def test_shorten_response_fields():
    from app.schemas.link import ShortenResponse
    resp = ShortenResponse(
        code="abc12",
        short_url="http://localhost:8000/abc12",
        long_url="https://example.com",
    )
    assert resp.code == "abc12"
    assert resp.short_url == "http://localhost:8000/abc12"
    assert resp.long_url == "https://example.com"
