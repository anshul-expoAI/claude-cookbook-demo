from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call

BASE62 = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")


def _make_repo(side_effects=None, return_link=None):
    """Build a stub LinksRepository."""
    repo = MagicMock()
    if side_effects:
        repo.create.side_effect = side_effects
    else:
        link = MagicMock()
        link.code = "abc12"
        link.long_url = "https://example.com"
        repo.create.return_value = return_link or link
    return repo


def _settings(code_length=5, max_retries=5):
    s = MagicMock()
    s.code_length = code_length
    s.max_retries = max_retries
    return s


@pytest.mark.unit
def test_create_short_link_happy_path():
    from app.services.shortener import create_short_link
    link = MagicMock()
    link.code = "abc12"
    repo = _make_repo(return_link=link)
    result = create_short_link("https://example.com", repo, _settings())
    assert result is link
    repo.create.assert_called_once()
    code_arg = repo.create.call_args[0][0]
    assert len(code_arg) == 5
    assert all(c in BASE62 for c in code_arg)


@pytest.mark.unit
def test_create_short_link_uses_secrets_not_random():
    """Verify the service imports secrets, not random."""
    import inspect
    import app.services.shortener as mod
    src = inspect.getsource(mod)
    assert "import secrets" in src or "from secrets" in src
    assert "random.choices" not in src


@pytest.mark.unit
def test_create_short_link_retries_on_collision():
    from app.services.shortener import create_short_link
    from app.services.errors import CodeCollisionError

    link = MagicMock()
    # fail 3 times then succeed
    repo = _make_repo(side_effects=[
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        link,
    ])
    result = create_short_link("https://example.com", repo, _settings(max_retries=5))
    assert result is link
    assert repo.create.call_count == 4


@pytest.mark.unit
def test_create_short_link_promotes_to_6_chars_after_exhausting_5():
    from app.services.shortener import create_short_link
    from app.services.errors import CodeCollisionError

    link = MagicMock()
    # exhaust 5 retries at length 5, succeed on first 6-char attempt
    repo = _make_repo(side_effects=[
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        CodeCollisionError("x"),
        link,  # 6-char attempt succeeds
    ])
    result = create_short_link("https://example.com", repo, _settings(code_length=5, max_retries=5))
    assert result is link
    # last successful call should have used a 6-char code
    last_code = repo.create.call_args[0][0]
    assert len(last_code) == 6


@pytest.mark.unit
def test_create_short_link_raises_exhausted_when_all_retries_fail():
    from app.services.shortener import create_short_link
    from app.services.errors import CodeCollisionError, CodeGenerationExhausted

    repo = _make_repo(side_effects=CodeCollisionError("x"))
    with pytest.raises(CodeGenerationExhausted):
        create_short_link("https://example.com", repo, _settings(max_retries=3))
