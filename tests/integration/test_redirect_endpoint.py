from __future__ import annotations

import pytest
from app.repositories.links import SqlAlchemyLinksRepository


@pytest.mark.integration
def test_redirect_happy_path(client, db_session):
    repo = SqlAlchemyLinksRepository(db_session)
    repo.create("abc12", "https://example.com/target")
    db_session.commit()

    resp = client.get("/abc12")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com/target"


@pytest.mark.integration
def test_redirect_returns_404_for_unknown_code(client):
    resp = client.get("/zzzzz")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "not found"


@pytest.mark.integration
@pytest.mark.parametrize("bad_code", ["aaa", "aaaaaaa", "aa!aa", "aa-bb"])
def test_redirect_returns_404_for_invalid_shape(client, bad_code):
    resp = client.get(f"/{bad_code}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_redirect_invalid_shape_does_not_hit_db(client, db_session):
    """Shape-invalid codes must return 404 without querying the DB."""
    call_count = []
    original = SqlAlchemyLinksRepository.get_by_code

    def spy(self, code):
        call_count.append(code)
        return original(self, code)

    SqlAlchemyLinksRepository.get_by_code = spy
    try:
        resp = client.get("/aa!")
        assert resp.status_code == 404
        assert len(call_count) == 0, "DB was queried for invalid-shape code"
    finally:
        SqlAlchemyLinksRepository.get_by_code = original
