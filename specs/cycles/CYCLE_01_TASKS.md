# Cycle 01 -- Task Breakdown

**Cycle:** Internal URL Shortener v1 -- End-to-End
**Dates:** 2026-05-12 -- 2026-05-13
**Total Tasks:** 12

---

> **Dependency Rule:** Execute tasks in order, respecting dependencies. A task cannot start until all its dependencies are Done. If a task is Blocked, escalate immediately -- do not skip it and start dependent tasks.

> **ID convention:** `URL-T-NNN` (workspace prefix `URL` + cycle-1 sequence). Maintain sequential numbering.

---

## Task Table

| Task ID   | Description | Complexity | Dependencies | Status | Assignee | Verification |
|-----------|-------------|-----------|-------------|--------|----------|-------------|
| URL-T-001 | Project scaffold + Pydantic Settings config module | S | None | Pending | -- | `uv sync` + `python -c "from app.config import Settings; print(Settings().database_url)"` prints `sqlite:///./shortener.db` |
| URL-T-002 | SQLAlchemy `Link` ORM model + `LinksRepository` Protocol + SQLAlchemy implementation | M | URL-T-001 | Pending | -- | `python -c "from app.repositories.links import LinksRepository, SqlAlchemyLinksRepository; assert isinstance(SqlAlchemyLinksRepository, type)"` succeeds; mypy/pyright confirms Protocol conformance |
| URL-T-003 | Alembic init + `0001_create_links` migration | S | URL-T-002 | Pending | -- | `uv run alembic upgrade head` exits 0; `sqlite3 shortener.db ".schema links"` shows all 4 columns + UNIQUE on `code` |
| URL-T-004 | Pydantic request/response schemas with `http`/`https` scheme allowlist and 2048-char cap | S | URL-T-001 | Pending | -- | `pytest tests/unit/test_schemas.py -v` passes (covers happy path + 5 rejection cases) |
| URL-T-005 | Shortener service: `create_short_link(long_url)` with random base62 gen, retry-on-collision, 5->6 char promotion, domain error on exhaustion | M | URL-T-002, URL-T-004 | Pending | -- | `pytest tests/unit/test_shortener_service.py -v` passes (happy path, retry path, exhaustion path) |
| URL-T-006 | `require_auth` no-op dependency + `POST /shorten` route | S | URL-T-005 | Pending | -- | `pytest tests/integration/test_shorten_endpoint.py::test_post_shorten_happy_path -v` passes; route inspection shows `Depends(require_auth)` |
| URL-T-007 | `GET /{code}` redirect route with regex shape validation + 302/404 handling | S | URL-T-002 | Pending | -- | `pytest tests/integration/test_redirect_endpoint.py -v` passes (happy, 404 unknown, 404 invalid shape, no-DB-query on invalid shape) |
| URL-T-008 | FastAPI app factory + `GET /healthz` + route registration in `app.main:app` | S | URL-T-006, URL-T-007 | Pending | -- | `uv run uvicorn app.main:app` starts without errors; `curl localhost:8000/healthz` returns `{"status":"ok"}` |
| URL-T-009 | `tests/conftest.py` with `db_session` (function-scoped tmpfile SQLite, schema via Alembic) + `client` (TestClient w/ dep override, `follow_redirects=False`) fixtures | M | URL-T-003, URL-T-008 | Pending | -- | `pytest tests/ --collect-only` lists all tests; fixtures resolve when invoked by a trivial smoke test |
| URL-T-010 | Unit test suite: code generation alphabet/length, retry loop behavior, schema validation matrix (all disallowed schemes + oversize + missing scheme) | M | URL-T-004, URL-T-005 | Pending | -- | `pytest tests/unit/ -v --cov=src/app/schemas --cov=src/app/services` passes with critical-path coverage >= 95% |
| URL-T-011 | Integration test suite: all 3 endpoints, 422 matrix, 404 matrix, round-trip preservation, log-redaction assertion | M | URL-T-009 | Pending | -- | `pytest tests/integration/ -v` passes; round-trip test confirms `Location` byte-equality |
| URL-T-012 | Logging config (redact long_url to scheme+host) + README with smoke test + full verification cascade green | M | URL-T-010, URL-T-011 | Pending | -- | Cascade: `ruff check src/ && ruff format --check src/ && bandit -r src/ && pytest --cov=src/ --cov-fail-under=80` all exit 0; bandit no HIGH/MEDIUM |

---

## Per-Task Detail

Each entry below augments the table row with: **Satisfies** (spec section), **Files affected**, and **Acceptance bullets** (the precise pass conditions).

### URL-T-001 -- Project scaffold + config module

- **Satisfies:** TECH_SPEC §6 (Configuration), §7 (Project Layout)
- **Files affected:** `pyproject.toml`, `.env.example`, `src/app/__init__.py`, `src/app/config.py`, `src/app/routes/__init__.py`, `src/app/services/__init__.py`, `src/app/repositories/__init__.py`, `src/app/models/__init__.py`, `src/app/schemas/__init__.py`
- **Acceptance:**
  - `pyproject.toml` declares deps: `fastapi`, `sqlalchemy`, `alembic`, `pydantic`, `pydantic-settings`, `python-dotenv`, `uvicorn[standard]`; dev deps: `pytest`, `pytest-cov`, `httpx`, `ruff`, `bandit`.
  - `pyproject.toml` has `[tool.ruff]`, `[tool.pytest.ini_options]` with custom marks (`unit`, `integration`), `[tool.bandit]` configuration blocks.
  - `app/config.py` exports a `Settings(BaseSettings)` Pydantic class with the five fields and defaults from TECH_SPEC §6, loading from `.env` via `pydantic-settings`.

### URL-T-002 -- ORM model + repository

- **Satisfies:** TECH_SPEC §1 (layering: `repositories/` is the only module that imports SQLAlchemy), §2 (Data model)
- **Files affected:** `src/app/models/__init__.py`, `src/app/models/link.py`, `src/app/repositories/links.py`
- **Acceptance:**
  - `Link` ORM model has columns matching §2: `id` (PK, autoincrement), `code` (VARCHAR(8), NOT NULL, UNIQUE), `long_url` (TEXT, NOT NULL), `created_at` (TIMESTAMP, NOT NULL, default UTC now).
  - `LinksRepository(Protocol)` declares `get_by_code(code: str) -> Link | None` and `create(code: str, long_url: str) -> Link`.
  - `SqlAlchemyLinksRepository(session: Session)` implements both methods; `create` raises a domain-typed `CodeCollisionError` on `IntegrityError`.
  - Nothing outside `repositories/` imports from `sqlalchemy` (verifiable via `grep -r 'from sqlalchemy' src/app/ | grep -v repositories` returning empty).

### URL-T-003 -- Alembic migration

- **Satisfies:** TECH_SPEC §2 (Migrations)
- **Files affected:** `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_create_links.py`
- **Acceptance:**
  - `alembic upgrade head` on an empty `shortener.db` creates the `links` table with all four columns + UNIQUE on `code`.
  - `alembic downgrade base` drops the table cleanly.
  - The migration is hand-reviewed (no auto-generation artifacts like leftover `op.f()` indexes that diverge from the spec).

### URL-T-004 -- Request/response schemas

- **Satisfies:** TECH_SPEC §3.1 (POST /shorten contract), §5.1 (scheme allowlist), §5.2 (length cap)
- **Files affected:** `src/app/schemas/link.py`, `tests/unit/test_schemas.py`
- **Acceptance:**
  - `ShortenRequest` Pydantic model: single field `long_url: str`, validator enforces scheme in {`http`, `https`}, length <= 2048, `model_config = ConfigDict(extra="forbid")`.
  - `ShortenResponse` Pydantic model: fields `code: str`, `short_url: str`, `long_url: str`.
  - Unit tests cover: happy `http://`, happy `https://`, rejected `javascript:`, `data:`, `file:`, `ftp:`, missing scheme, oversize URL, extra fields rejected.

### URL-T-005 -- Shortener service

- **Satisfies:** TECH_SPEC §4 (Code Generation Algorithm)
- **Files affected:** `src/app/services/shortener.py`, `src/app/services/errors.py`, `tests/unit/test_shortener_service.py`
- **Acceptance:**
  - `create_short_link(long_url: str, repo: LinksRepository, settings: Settings) -> Link`: generates random base62 of `settings.code_length`, calls `repo.create`, retries on `CodeCollisionError` up to `settings.max_retries`; on continued collision promotes length to 6 and retries again; raises `CodeGenerationExhausted` on final failure.
  - Random source is `secrets.token_urlsafe` (or equivalent CSPRNG) -- NOT `random.choices`. Tests confirm via mock.
  - Service depends on the `LinksRepository` Protocol, not the SQLAlchemy implementation directly.

### URL-T-006 -- POST /shorten route

- **Satisfies:** TECH_SPEC §1 (Auth seam), §3.1 (POST /shorten), §5.3 (SQL safety via repo layer)
- **Files affected:** `src/app/deps.py`, `src/app/routes/shorten.py`, `src/app/routes/__init__.py`
- **Acceptance:**
  - `deps.py` exports `require_auth() -> None` (no-op, returns None) and `get_db()` session generator.
  - `POST /shorten` route uses `Depends(require_auth)`, `Depends(get_db)`, and the shortener service; maps `CodeGenerationExhausted` -> `HTTPException(503)`.
  - Response status is `201 Created` with the `ShortenResponse` shape.

### URL-T-007 -- GET /{code} redirect route

- **Satisfies:** TECH_SPEC §3.2 (GET /{code}), §3.2 "302 not 301" decision
- **Files affected:** `src/app/routes/redirect.py`, `src/app/routes/__init__.py`
- **Acceptance:**
  - Route path: `/{code}` with FastAPI path-parameter regex `^[A-Za-z0-9]{5,6}$` (or equivalent Pydantic constraint that returns 404 -- NOT 422 -- on shape mismatch).
  - Returns `RedirectResponse(url=long_url, status_code=302)` on hit.
  - Returns `HTTPException(404, "not found")` on miss.
  - Invalid-shape paths return 404 without issuing a DB query (verifiable in integration test via a repo spy).

### URL-T-008 -- App factory + healthz + main

- **Satisfies:** TECH_SPEC §3.3 (GET /healthz), §7 (`app/main.py` is FastAPI app factory entry point)
- **Files affected:** `src/app/main.py`, `src/app/routes/health.py`, `src/app/routes/__init__.py`
- **Acceptance:**
  - `app.main:app` is a module-level `FastAPI()` instance with all three routes registered.
  - `GET /healthz` returns `200 {"status": "ok"}`.
  - `uv run uvicorn app.main:app --reload` starts cleanly with zero config (no `.env` required).

### URL-T-009 -- Test fixtures

- **Satisfies:** TECH_SPEC §8 (Fixtures subsection)
- **Files affected:** `tests/__init__.py`, `tests/conftest.py`, `tests/unit/__init__.py`, `tests/unit/conftest.py` (if needed), `tests/integration/__init__.py`, `tests/integration/conftest.py` (if needed)
- **Acceptance:**
  - `db_session` fixture (function-scoped): creates a tmpfile SQLite, runs `alembic upgrade head` against it, yields a Session, drops the tmpfile on teardown.
  - `client` fixture (function-scoped): builds `TestClient(app)`, overrides `get_db` to yield `db_session`, sets `follow_redirects=False`, yields client.
  - Both fixtures live in the root `tests/conftest.py` (shared across unit + integration per the project testing rules).

### URL-T-010 -- Unit test suite

- **Satisfies:** TECH_SPEC §8 (Unit subsection)
- **Files affected:** `tests/unit/test_schemas.py` (expanded from URL-T-004), `tests/unit/test_shortener_service.py` (expanded from URL-T-005), `tests/unit/test_code_generation.py`
- **Acceptance:**
  - Code-gen tests assert: length in {5, 6}; alphabet subset of `[A-Za-z0-9]`; distribution sanity (no obvious bias in 10k samples).
  - Service retry tests use a stub `LinksRepository` that raises `CodeCollisionError` N times then succeeds; assert correct retry count + length promotion at the 5->6 threshold.
  - Schema test matrix covers every disallowed scheme listed in TECH_SPEC §5.1 + oversize + missing scheme + extra field rejection.
  - All tests marked `@pytest.mark.unit`.

### URL-T-011 -- Integration test suite

- **Satisfies:** TECH_SPEC §8 (Integration subsection)
- **Files affected:** `tests/integration/test_shorten_endpoint.py`, `tests/integration/test_redirect_endpoint.py`, `tests/integration/test_health_endpoint.py`, `tests/integration/test_round_trip.py`, `tests/integration/test_logging.py`
- **Acceptance:**
  - Each endpoint test exercises happy + each error path documented in TECH_SPEC §3.
  - Round-trip test: POST a URL with query+fragment, GET the returned code, assert `Location` equals submitted URL byte-for-byte.
  - Logging test captures `caplog`, posts a URL, asserts the INFO record contains scheme+host only and does NOT contain the path, query, or fragment.
  - All tests marked `@pytest.mark.integration`.

### URL-T-012 -- Logging config + README + final cascade

- **Satisfies:** TECH_SPEC §5.5 (Logging), §9 (Local Run), §11 (Acceptance Criteria 1-7)
- **Files affected:** `src/app/logging.py` (or `app/main.py` if minimal), `README.md`, `.gitignore` (add `.env`, `shortener.db`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`)
- **Acceptance:**
  - Logger emits redacted format: code + scheme+host only on `POST /shorten`; WARNING on `GET /{code}` 404; never logs full `long_url`.
  - README has: stack summary, Build/Run section verbatim from TECH_SPEC §9, smoke-test curl pair, Test section running the cascade, link to `specs/PROJECT.md` and `specs/TECH_SPEC.md`.
  - Final cascade run (all four commands) exits 0; bandit reports zero HIGH/MEDIUM; coverage >= 80% overall and >= 95% on `schemas/link.py`, `services/shortener.py`, `routes/redirect.py`.
  - All seven items of TECH_SPEC §11 are demonstrably satisfied (annotate the README or a `CHANGELOG.md` with a checklist).

---

## Complexity Key

| Size | Estimated Duration | Guideline |
|------|--------------------|-----------|
| S | < 2 hours | Single file, straightforward logic, minimal testing |
| M | 2-8 hours | Multiple files, moderate logic, requires thorough testing |
| L | 1-2 days | Cross-cutting concern, complex logic, significant testing |

## Status Key

| Status | Meaning |
|--------|---------|
| Pending | Not started; dependencies may or may not be met |
| In Progress | Actively being worked on |
| Done | Complete and verified |
| Blocked | Cannot proceed; dependency is stuck or external blocker exists |

## Dependency Graph

```
                          URL-T-001 (scaffold + config)
                         /                              \
                        v                                v
              URL-T-002 (model + repo)             URL-T-004 (schemas)
                        |                                |
              +---------+---------+                      |
              |                   |                      |
              v                   v                      |
       URL-T-003 (migration)  URL-T-007 (GET /{code})    |
              |                   |                      |
              |                   |                      |
              |             +-----+----------------------+
              |             |
              |             v
              |       URL-T-005 (shortener service)
              |             |
              |             v
              |       URL-T-006 (POST /shorten)
              |             |
              |             v
              |       URL-T-008 (app factory + /healthz)
              |             |
              +-------------+
                            |
                            v
                      URL-T-009 (test fixtures)
                            |
                            +-----------------+
                            |                 |
                            v                 v
                      URL-T-011 (integ)  URL-T-010 (unit) [also needs T-004, T-005]
                            |                 |
                            +--------+--------+
                                     |
                                     v
                          URL-T-012 (logging + README + cascade)
```

Note: URL-T-010 (unit) lists `URL-T-004, URL-T-005` as dependencies in the table; the graph above shows it downstream of URL-T-009 only for visual simplicity, because conftest.py existing makes the test collection cleaner. The hard build-order constraint is what's in the table.

## Notes

- Each task is sized to a single Claude Code session.
- The Verification column is mechanically checkable -- if you cannot run the command and see it pass, the task is not done.
- When a task status changes, update this file immediately. This is the single source of truth for progress.
- Linear ticket SAP-105 tracks the parent cycle; child task tickets are not created automatically for this workspace (per `CLAUDE.local.md`, the planner global "create child Linear tickets" step is deferred unless explicitly requested).
