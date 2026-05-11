# URL Shortener (v1)

Internal self-hostable URL shortener. POST a long URL, get a short code. Visit the code, get a 302 redirect. Zero external dependencies.

**Stack:** FastAPI · SQLAlchemy · Alembic · SQLite · Pydantic v2 · Python 3.11+

See [specs/PROJECT.md](specs/PROJECT.md) for the WHY and [specs/TECH_SPEC.md](specs/TECH_SPEC.md) for the HOW.

---

## Local Run

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### Smoke test

```bash
# Shorten a URL
curl -X POST http://localhost:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"long_url": "https://example.com/some/long/path?with=query"}'
# -> {"code":"aB3xZ","short_url":"http://localhost:8000/aB3xZ","long_url":"..."}

# Follow the redirect
curl -i http://localhost:8000/aB3xZ
# -> HTTP/1.1 302 Found
# -> Location: https://example.com/some/long/path?with=query
```

---

## Test

```bash
# Full verification cascade (all must exit 0)
uv run ruff check src/
uv run ruff format --check src/
uv run bandit -r src/
uv run pytest --cov=src/ --cov-fail-under=80 --cov-report=term-missing
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/shorten` | Create a short link. Body: `{"long_url": "https://..."}`. Returns 201. |
| `GET` | `/{code}` | Redirect to the stored URL (302). Returns 404 if unknown. |
| `GET` | `/healthz` | Liveness probe. Returns `{"status":"ok"}`. |

**Security:** `long_url` must be `http` or `https`, max 2048 chars. All other schemes are rejected with 422.

---

## TECH_SPEC §11 Acceptance Criteria

- [x] All three endpoints behave per §3.
- [x] URL scheme allowlist and length cap enforced with tests (§5.1, §5.2).
- [x] `uv run uvicorn app.main:app --reload` starts with zero config.
- [x] `pytest --cov=src/ --cov-fail-under=80` passes.
- [x] `ruff check` and `ruff format --check` pass with zero violations.
- [x] `bandit -r src/` reports zero HIGH or MEDIUM findings.
- [x] Smoke test in §9 succeeds against a local instance.
