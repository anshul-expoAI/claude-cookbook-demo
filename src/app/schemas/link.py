from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class ShortenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    long_url: str

    @field_validator("long_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2048:
            raise ValueError("URL exceeds 2048 characters")
        # parse scheme manually — Pydantic's AnyUrl is too permissive by default
        if "://" not in v:
            raise ValueError("URL must include a scheme (http:// or https://)")
        scheme = v.split("://", 1)[0].lower()
        if scheme not in {"http", "https"}:
            raise ValueError(f"URL scheme '{scheme}' is not allowed; use http or https")
        return v


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    long_url: str
