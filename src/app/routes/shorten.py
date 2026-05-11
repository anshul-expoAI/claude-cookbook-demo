from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.deps import DBSession, get_db, require_auth
from app.repositories.links import SqlAlchemyLinksRepository
from app.schemas.link import ShortenRequest, ShortenResponse
from app.services.errors import CodeGenerationExhausted
from app.services.shortener import create_short_link

router = APIRouter()
_settings = Settings()
logger = logging.getLogger("app.routes.shorten")


def _scheme_host(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten(
    body: ShortenRequest,
    _auth: None = Depends(require_auth),
    db: DBSession = Depends(get_db),
) -> ShortenResponse:
    repo = SqlAlchemyLinksRepository(db)
    try:
        link = create_short_link(body.long_url, repo, _settings)
        db.commit()
    except CodeGenerationExhausted as exc:
        raise HTTPException(status_code=503, detail="code generation exhausted") from exc

    logger.info("created code=%s target=%s", link.code, _scheme_host(link.long_url))
    short_url = f"{_settings.base_url}/{link.code}"
    return ShortenResponse(code=link.code, short_url=short_url, long_url=link.long_url)
