from __future__ import annotations

import pytest


@pytest.mark.integration
def test_db_session_fixture_yields_session(db_session):
    from sqlalchemy.orm import Session
    assert isinstance(db_session, Session)


@pytest.mark.integration
def test_client_fixture_has_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.integration
def test_client_does_not_follow_redirects(client, db_session):
    from app.repositories.links import SqlAlchemyLinksRepository
    repo = SqlAlchemyLinksRepository(db_session)
    repo.create("abc12", "https://example.com")
    db_session.commit()

    resp = client.get("/abc12")
    assert resp.status_code == 302
    assert "Location" in resp.headers
