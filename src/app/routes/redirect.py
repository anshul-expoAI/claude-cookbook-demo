from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.deps import DBSession, get_db
from app.repositories.links import SqlAlchemyLinksRepository

router = APIRouter()

_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{5,6}$")


@router.get("/{code}")
def redirect(code: str, db: DBSession = Depends(get_db)) -> RedirectResponse:
    if not _CODE_PATTERN.match(code):
        raise HTTPException(status_code=404, detail="not found")
    repo = SqlAlchemyLinksRepository(db)
    link = repo.get_by_code(code)
    if link is None:
        raise HTTPException(status_code=404, detail="not found")
    return RedirectResponse(url=link.long_url, status_code=302)
