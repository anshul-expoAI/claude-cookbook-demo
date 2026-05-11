# TECH SPEC: Internal URL Shortener (v1)

Companion to `specs/PROJECT.md`. This document specifies architecture, data model, API contracts, and the security baseline. It does not contain implementation code; it contains the contracts an implementer must satisfy.

## 1. Architecture

Single-process FastAPI service backed by SQLite via SQLAlchemy. No cache, no queue, no background workers in v1.

```
              +-------------------+
   client --> |  FastAPI app      |
   (curl,     |                   |
    browser)  |  routes/          |
              |   - POST /shorten |
              |   - GET  /{code}  |
              |   - GET  /healthz |
              |                   |
              |  services/        |
              |   - shortener     | <-- code generation + retry loop
              |                   |
              |  repositories/    |
              |   - links_repo    | <-- SQLAlchemy session boundary
              +---------+---------+
                        |
                        v
                  +-----------+
                  |  SQLite   |
                  |  links    |
                  +-----------+
```

### Layering rules

- `routes/` -- HTTP only. Parses requests, calls a service, shapes the response. No business logic.
- `services/` -- pure business logic (code generation, retry policy, URL validation). Depends on a `Repository` Protocol, not on SQLAlchemy directly. This is the seam that lets us unit-test without a DB and swap storage backends later.
- `repositories/` -- the only place that imports SQLAlchemy. Implements the `LinksRepository` Protocol.

### Auth seam (v1 has no auth, but the seam is non-negotiable)

`POST /shorten` will be the protected endpoint when JWT lands. To make that a one-line change later:

- Define a no-op `require_auth` dependency in v1 (`Depends(require_auth)`) that returns `None` and does nothing.
- Wire it onto `POST /shorten` (and any future write endpoints) from day one.
- The JWT spec replaces the body of `require_auth` only -- routes do not change.

`GET /{code}` stays unauthenticated permanently (the whole point is anonymous redirects).

## 2. Data Model

Single table: `links`.

| Column        | Type           | Constraints                       | Notes                                                              |
|---------------|----------------|-----------------------------------|--------------------------------------------------------------------|
| `id`          | INTEGER        | PRIMARY KEY, AUTOINCREMENT        | Internal surrogate. Never exposed.                                 |
| `code`        | VARCHAR(8)     | NOT NULL, UNIQUE                  | 5 or 6 chars, base62 `[A-Za-z0-9]`. Indexed by the unique constraint. |
| `long_url`    | TEXT           | NOT NULL                          | Stored verbatim including query string and fragment.               |
| `created_at`  | TIMESTAMP      | NOT NULL, DEFAULT now() (UTC)     | Audit field; not exposed in v1 responses but available for ops.    |

### Notes

- No `expires_at` column in v1. Adding one later is an additive migration.
- No `user_id` column. JWT spec will add it as a nullable column with a backfill of `NULL` for pre-auth rows.
- Width is `VARCHAR(8)` not `VARCHAR(6)` to leave headroom for the JWT spec (or any later spec) to extend without a column-type migration.
- `code` is the natural lookup key. The UNIQUE constraint serves as both the integrity check and the index.

### Migrations

Use **Alembic**, even for v1's single table. This sets the migration habit before the schema gets non-trivial.

- Initial revision: `links` table as specified above.
- `alembic upgrade head` runs on app startup in dev (gated behind an env flag, default on for SQLite, off for Postgres).

## 3. API Contracts

All requests/responses are JSON unless noted. All errors follow the FastAPI default error envelope: `{"detail": "<message>"}` plus the HTTP status code.

### 3.1 POST /shorten

Create a short link.

**Request body:**

| Field      | Type    | Required | Constraints                                                |
|------------|---------|----------|------------------------------------------------------------|
| `long_url` | string  | yes      | Valid absolute URL. Scheme MUST be `http` or `https`. Max length 2048. |

**Response (201 Created):**

| Field        | Type   | Notes                                                  |
|--------------|--------|--------------------------------------------------------|
| `code`       | string | The generated short code (5-6 chars, base62).          |
| `short_url`  | string | Convenience: `{BASE_URL}/{code}`. Built server-side.   |
| `long_url`   | string | Echoed back verbatim.                                  |

**Error responses:**

| Status | When                                                                    |
|--------|-------------------------------------------------------------------------|
| 422    | `long_url` missing, malformed, exceeds 2048 chars, or has disallowed scheme. |
| 503    | Code generation exhausted retry budget (effectively impossible; logged loudly). |

**Idempotency:** none. Submitting the same `long_url` twice produces two distinct codes. Documented and intentional.

### 3.2 GET /{code}

Resolve a short code to its long URL and redirect.

**Path params:** `code` -- 5 or 6 base62 chars. The route must validate the shape (regex `^[A-Za-z0-9]{5,6}$`) before hitting the DB to avoid burning a query on garbage.

**Responses:**

| Status | Body | Headers                          | When                                  |
|--------|------|----------------------------------|---------------------------------------|
| 302    | (empty) | `Location: <long_url>`        | Code exists.                          |
| 404    | `{"detail": "not found"}` | -- | Code not found or shape invalid.      |

**Why 302, not 301:** 301s are aggressively cached by browsers and intermediaries. For an internal tool we want the freedom to invalidate or change a mapping later without fighting browser caches. (We won't in v1, but the choice is sticky.)

### 3.3 GET /healthz

Liveness probe.

**Response (200):** `{"status": "ok"}`. No DB check in v1.

## 4. Code Generation Algorithm (contract, not implementation)

The shortener service exposes a single operation: `create_short_link(long_url) -> Link`. Its required behavior:

1. Validate `long_url` (see Section 5 for the validation contract).
2. Generate a random base62 string of length `CODE_LENGTH` (default 5).
3. Attempt to insert `(code, long_url)` into `links`.
4. On UNIQUE-constraint violation on `code`: regenerate and retry. Up to `MAX_RETRIES` attempts (default 5).
5. If all 5-char attempts fail consecutively, promote to 6-char codes and retry up to `MAX_RETRIES` more times.
6. If still failing, raise a domain error that the route layer maps to HTTP 503.

Configurable via env: `CODE_LENGTH`, `MAX_RETRIES`. Both have safe defaults; neither is required for local run.

## 5. Security Baseline

This is an internal tool with no auth in v1. That makes input validation the only line of defense -- treat it accordingly.

### 5.1 URL scheme allowlist (CRITICAL)

`long_url` MUST be rejected unless its scheme is exactly `http` or `https`. This blocks:

- `javascript:` -- stored XSS via redirect.
- `data:` -- exfiltration / phishing vectors.
- `file:` -- local file probing if the redirect is followed by a desktop client.
- Any other scheme (`ftp:`, `gopher:`, `chrome:`, custom app schemes) -- not needed, expand the attack surface for nothing.

Validation happens in the Pydantic request model (`extra="forbid"`, constrained URL type with scheme allowlist). Reject at the boundary, not in the service layer.

### 5.2 Length cap

`long_url` MUST be <= 2048 chars. Practical browser limit, and a cheap DoS bound. Enforce in the Pydantic model.

### 5.3 SQL safety

All DB access through SQLAlchemy ORM or parameterized core expressions. No f-string or `%` formatting into raw SQL anywhere. This is also covered by the org coding-style rules, but called out here so the reviewer can verify.

### 5.4 Secrets

No secrets in v1 (no auth, no third-party APIs). When JWT lands, the signing key comes from `JWT_SECRET` env var loaded via python-dotenv, never hardcoded, never logged.

### 5.5 Logging

- Log every `POST /shorten` at INFO with the generated code and the **scheme + host** of the long URL (never the full URL with query string -- internal URLs frequently contain tokens in query params).
- Log every `GET /{code}` 404 at WARNING (helps surface bad links / scanning attempts).
- Never log the full `long_url` at any level.

### 5.6 Open redirect

`GET /{code}` is, by design, an open redirect to whatever `long_url` was stored. The scheme allowlist on POST is what prevents the dangerous classes; we accept that the service can redirect to any `http(s)` URL (that's the whole product).

## 6. Configuration

Loaded via python-dotenv from `.env` (gitignored). All have safe defaults so the service runs with no `.env` at all.

| Variable        | Default                  | Purpose                                   |
|-----------------|--------------------------|-------------------------------------------|
| `DATABASE_URL`  | `sqlite:///./shortener.db` | SQLAlchemy URL.                         |
| `BASE_URL`      | `http://localhost:8000`  | Used to construct `short_url` in responses. |
| `CODE_LENGTH`   | `5`                      | Starting code length.                     |
| `MAX_RETRIES`   | `5`                      | Per-length collision retry budget.        |
| `LOG_LEVEL`     | `INFO`                   | App log level.                            |

## 7. Project Layout

```
src/
  app/
    __init__.py
    main.py                 # FastAPI app factory + route registration
    config.py               # Pydantic Settings; loads .env
    deps.py                 # FastAPI dependencies (DB session, require_auth no-op)
    routes/
      __init__.py
      shorten.py            # POST /shorten
      redirect.py           # GET /{code}
      health.py             # GET /healthz
    services/
      __init__.py
      shortener.py          # create_short_link, code gen + retry
    repositories/
      __init__.py
      links.py              # LinksRepository protocol + SQLAlchemy impl
    models/
      __init__.py
      link.py               # SQLAlchemy ORM model
    schemas/
      __init__.py
      link.py               # Pydantic request/response models
migrations/
  env.py
  versions/
    0001_create_links.py
tests/
  conftest.py               # shared fixtures: app client, in-memory DB session
  unit/
    test_shortener_service.py
    test_code_generation.py
    test_schemas.py
  integration/
    test_shorten_endpoint.py
    test_redirect_endpoint.py
    test_health_endpoint.py
pyproject.toml
.env.example
README.md
```

Matches the project CLAUDE.md `File Structure` block. Tests mirror `src/`.

## 8. Testing Strategy

Per org testing rules (80% line coverage, TDD, real DB not mocks).

### Unit (services, schemas)

- Code generation produces strings of expected length, base62 alphabet only.
- Retry loop calls repo up to N times on collision, then promotes length, then raises.
- Pydantic request model accepts `http`/`https`, rejects `javascript:`, `data:`, `file:`, `ftp:`, missing scheme, malformed URLs, URLs over 2048 chars.

### Integration (routes against a real SQLite test DB)

- `POST /shorten` happy path returns 201 with valid `code`, `short_url`, `long_url`.
- `POST /shorten` rejects each disallowed scheme with 422.
- `POST /shorten` rejects oversize URL with 422.
- `GET /{code}` returns 302 with correct `Location` for a known code.
- `GET /{code}` returns 404 for an unknown code.
- `GET /{code}` returns 404 for a code of invalid shape (e.g. `aaa`, `aaaaaaa`, `aaa!a`).
- `GET /healthz` returns 200.
- Round-trip: shorten then redirect resolves to the originally submitted URL byte-for-byte.

### Fixtures

- `db_session` -- function-scoped, fresh SQLite (`sqlite:///:memory:` or a tmpfile), schema created via Alembic.
- `client` -- `TestClient(app)` with the `db_session` injected via dependency override.

### Coverage gate

`pytest --cov=src/ --cov-fail-under=80 --cov-report=term-missing` in CI. Critical paths (URL validation, redirect) should land at 95%+ naturally.

## 9. Local Run

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Smoke test:

```bash
curl -X POST http://localhost:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"long_url": "https://example.com/some/long/path?with=query"}'
# -> {"code": "aB3xZ", "short_url": "http://localhost:8000/aB3xZ", "long_url": "..."}

curl -i http://localhost:8000/aB3xZ
# -> HTTP/1.1 302 Found
# -> Location: https://example.com/some/long/path?with=query
```

## 10. Risks and Mitigations

| Risk                                                    | Likelihood | Impact | Mitigation                                                                 |
|---------------------------------------------------------|------------|--------|----------------------------------------------------------------------------|
| Code-generation collision storm exhausts retry budget   | Negligible | Low    | Fail loud with 503 + ERROR log; promote to 6-char; alert if seen in prod.  |
| Open redirect abused via `javascript:` / `data:` URLs   | Real if validation missed | High | Scheme allowlist in Pydantic model; integration test per disallowed scheme. |
| SQLite write contention under load                      | Low (v1 demo) | Medium | Documented as v1 limitation; swap to Postgres via `DATABASE_URL` is config-only. |
| Tokens leaked via long-URL logging                      | Real if devs log carelessly | High | Logging policy in 5.5; PR review checklist item.                           |
| JWT spec arrives and route signatures need to change    | Low        | Low    | `require_auth` no-op dependency in place from v1; JWT spec changes only its body. |

## 11. Acceptance Criteria (for the implementing dev)

The implementation is done when:

1. All three endpoints behave per Section 3.
2. All security validations in Section 5 are enforced and have tests in Section 8.
3. `uv run uvicorn app.main:app --reload` starts the service with zero config.
4. `pytest --cov=src/ --cov-fail-under=80` passes.
5. `ruff check` and `ruff format --check` pass with zero violations.
6. `bandit -r src/` reports no HIGH or MEDIUM findings.
7. The smoke test in Section 9 succeeds against a local instance.
