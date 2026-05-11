from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.mark.unit
def test_link_model_columns():
    from app.models.link import Link

    mapper = Link.__table__
    col_names = {c.name for c in mapper.columns}
    assert {"id", "code", "long_url", "created_at"} == col_names


@pytest.mark.unit
def test_link_code_column_unique():
    from sqlalchemy import UniqueConstraint
    from app.models.link import Link

    has_unique = any(
        isinstance(c, UniqueConstraint) and "code" in [col.name for col in c.columns]
        for c in Link.__table__.constraints
    )
    assert has_unique, "links.code must have a UNIQUE constraint"


@pytest.mark.unit
def test_repository_protocol_has_required_methods():
    import inspect
    from app.repositories.links import LinksRepository

    members = dir(LinksRepository)
    assert "get_by_code" in members
    assert "create" in members


@pytest.mark.unit
def test_sqlalchemy_repo_create_and_get(tmp_path):
    from app.models.link import Base
    from app.repositories.links import SqlAlchemyLinksRepository

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = SqlAlchemyLinksRepository(session)
        link = repo.create("abc12", "https://example.com")
        session.commit()
        assert link.code == "abc12"
        assert link.long_url == "https://example.com"
        assert link.id is not None

        found = repo.get_by_code("abc12")
        assert found is not None
        assert found.code == "abc12"


@pytest.mark.unit
def test_sqlalchemy_repo_get_missing_returns_none(tmp_path):
    from app.models.link import Base
    from app.repositories.links import SqlAlchemyLinksRepository

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = SqlAlchemyLinksRepository(session)
        assert repo.get_by_code("zzzzz") is None


@pytest.mark.unit
def test_sqlalchemy_repo_create_raises_on_collision(tmp_path):
    from app.models.link import Base
    from app.repositories.links import SqlAlchemyLinksRepository
    from app.services.errors import CodeCollisionError

    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repo = SqlAlchemyLinksRepository(session)
        repo.create("abc12", "https://a.com")
        session.commit()

    with Session(engine) as session:
        repo = SqlAlchemyLinksRepository(session)
        with pytest.raises(CodeCollisionError):
            repo.create("abc12", "https://b.com")


@pytest.mark.unit
def test_no_sqlalchemy_import_in_services_or_routes():
    """services/ and routes/ must not import sqlalchemy directly (models/ is allowed)."""
    import subprocess
    for pkg in ("src/app/services", "src/app/routes"):
        result = subprocess.run(
            ["grep", "-r", "from sqlalchemy", pkg, "--include=*.py"],
            capture_output=True, text=True,
        )
        assert result.stdout.strip() == "", (
            f"SQLAlchemy imported in {pkg}:\n{result.stdout}"
        )
