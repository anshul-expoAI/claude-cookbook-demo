from __future__ import annotations

from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.link import Link
from app.services.errors import CodeCollisionError


class LinksRepository(Protocol):
    def get_by_code(self, code: str) -> Link | None: ...
    def create(self, code: str, long_url: str) -> Link: ...


class SqlAlchemyLinksRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> Link | None:
        return self._session.query(Link).filter_by(code=code).first()

    def create(self, code: str, long_url: str) -> Link:
        link = Link(code=code, long_url=long_url)
        self._session.add(link)
        try:
            self._session.flush()
        except IntegrityError:
            self._session.rollback()
            raise CodeCollisionError(code)
        return link
