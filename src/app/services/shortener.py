from __future__ import annotations

import secrets
import string

from app.models.link import Link
from app.services.errors import CodeCollisionError, CodeGenerationExhausted

_BASE62 = string.ascii_letters + string.digits  # 62 chars: A-Za-z0-9


def _generate_code(length: int) -> str:
    return "".join(secrets.choice(_BASE62) for _ in range(length))


def create_short_link(long_url: str, repo: object, settings: object) -> Link:
    max_retries: int = settings.max_retries
    start_length: int = settings.code_length

    for length in (start_length, 6):
        for _ in range(max_retries):
            code = _generate_code(length)
            try:
                return repo.create(code, long_url)
            except CodeCollisionError:
                continue
        if length == 6:
            break

    raise CodeGenerationExhausted(
        f"Exhausted {max_retries} retries at lengths {start_length} and 6"
    )
