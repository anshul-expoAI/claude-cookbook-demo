from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_db, require_auth
from app.repositories.links import SqlAlchemyLinksRepository
from app.schemas.link import ShortenRequest, ShortenResponse
from app.services.errors import CodeGenerationExhausted
from app.services.shortener import create_short_link

router = APIRouter()
_settings = Settings()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten(
    body: ShortenRequest,
    _auth: None = Depends(require_auth),
    db: Session = Depends(get_db),
) -> ShortenResponse:
    repo = SqlAlchemyLinksRepository(db)
    try:
        link = create_short_link(body.long_url, repo, _settings)
        db.commit()
    except CodeGenerationExhausted:
        raise HTTPException(status_code=503, detail="code generation exhausted")

    short_url = f"{_settings.base_url}/{link.code}"
    return ShortenResponse(code=link.code, short_url=short_url, long_url=link.long_url)
