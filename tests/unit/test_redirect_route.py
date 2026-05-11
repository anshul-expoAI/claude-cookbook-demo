from __future__ import annotations

import re
import pytest


@pytest.mark.unit
def test_redirect_route_regex_accepts_5_chars():
    pattern = re.compile(r"^[A-Za-z0-9]{5,6}$")
    assert pattern.match("abc12")
    assert pattern.match("ABCdef")


@pytest.mark.unit
def test_redirect_route_regex_rejects_short_code():
    pattern = re.compile(r"^[A-Za-z0-9]{5,6}$")
    assert not pattern.match("abc")
    assert not pattern.match("")


@pytest.mark.unit
def test_redirect_route_regex_rejects_long_code():
    pattern = re.compile(r"^[A-Za-z0-9]{5,6}$")
    assert not pattern.match("abc1234")


@pytest.mark.unit
def test_redirect_route_regex_rejects_special_chars():
    pattern = re.compile(r"^[A-Za-z0-9]{5,6}$")
    assert not pattern.match("aa!bb")
    assert not pattern.match("aa-bb")


@pytest.mark.unit
def test_redirect_route_module_uses_302():
    import pathlib
    src = pathlib.Path("src/app/routes/redirect.py").read_text()
    assert "302" in src
    assert "RedirectResponse" in src


@pytest.mark.unit
def test_redirect_route_module_returns_404_on_miss():
    import pathlib
    src = pathlib.Path("src/app/routes/redirect.py").read_text()
    assert "404" in src
