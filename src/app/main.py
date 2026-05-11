from __future__ import annotations

from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.redirect import router as redirect_router
from app.routes.shorten import router as shorten_router

app = FastAPI(title="URL Shortener", version="1.0.0")

app.include_router(health_router)
app.include_router(shorten_router)
app.include_router(redirect_router)
