# Cycle 01: Internal URL Shortener v1 -- End-to-End

**Dates:** 2026-05-12 -- 2026-05-13
**Status:** Planning
**Goal:** Ship the entire v1 spec from `specs/PROJECT.md` + `specs/TECH_SPEC.md` -- three endpoints (`POST /shorten`, `GET /{code}`, `GET /healthz`) backed by SQLite, runnable with one command, fully tested, ruff/bandit/coverage gates green.

> v1 is estimated S (under one day) in PROJECT.md. This cycle delivers it in three single-session stories that pipeline naturally: data -> API -> tests.

---

## User Stories

### Story 1: Scaffold the service and persistence layer

**As a** developer joining this repo,
**I want** the project layout, dependencies, settings, ORM model, repository seam, and Alembic migration to exist and be runnable,
**so that** anyone can `uv sync && uv run alembic upgrade head` against a fresh checkout and have a working empty service ready to add endpoints to.

**Priority:** Must
**Effort:** S
**Implements:** TECH_SPEC `§1 Architecture` (layering: routes / services / repositories), `§2 Data Model` (`links` table), `§6 Configuration` (env vars + defaults), `§7 Project Layout` (file tree).

**Acceptance Criteria:**

- [ ] **Given** a fresh clone with no `.env` file, **When** the developer runs `uv sync && uv run alembic upgrade head`, **Then** the command exits 0 and a `shortener.db` SQLite file appears at the repo root containing a `links` table with the four columns from TECH_SPEC §2 (`id`, `code`, `long_url`, `created_at`) and a UNIQUE constraint on `code`.
- [ ] **Given** the project structure on disk, **When** an importer runs `from app.repositories.links import LinksRepository`, **Then** the symbol resolves and is a `typing.Protocol` whose methods include `get_by_code(code: str) -> Link | None` and `create(code: str, long_url: str) -> Link`; **And** a concrete SQLAlchemy implementation `SqlAlchemyLinksRepository` also resolves and satisfies the Protocol structurally (mypy/pyright check passes).
- [ ] **Given** the configuration module, **When** `Settings()` is instantiated with no environment variables set, **Then** it returns `DATABASE_URL="sqlite:///./shortener.db"`, `BASE_URL="http://localhost:8000"`, `CODE_LENGTH=5`, `MAX_RETRIES=5`, `LOG_LEVEL="INFO"` -- exactly the defaults from TECH_SPEC §6.
- [ ] **Given** a fresh clone, **When** `ruff check src/` runs, **Then** it exits 0 with zero violations; **And** `ruff format --check src/` exits 0.

---

### Story 2: Build the three HTTP endpoints with security validation

**As a** developer or curl user,
**I want** `POST /shorten`, `GET /{code}`, and `GET /healthz` to work end-to-end against the persistence layer from Story 1,
**so that** the service delivers its core value (long URL in, short URL out, short URL redirects back) while rejecting the URL-scheme attack surface that is the v1 security baseline.

**Priority:** Must
**Effort:** M
**Implements:** TECH_SPEC `§3 API Contracts` (all three endpoints), `§4 Code Generation Algorithm` (random base62 + retry + length-promotion + 503 on exhaustion), `§5.1 URL scheme allowlist`, `§5.2 Length cap`, `§5.3 SQL safety`, and the `require_auth` no-op seam from `§1 Auth seam`.

**Acceptance Criteria:**

- [ ] **Given** the service is running locally, **When** a client `POST`s `{"long_url": "https://example.com/some/path?q=1#frag"}` to `/shorten`, **Then** the response is `201 Created` with JSON `{"code": "<5-or-6 base62 chars>", "short_url": "http://localhost:8000/<code>", "long_url": "https://example.com/some/path?q=1#frag"}`; **And** the fragment is preserved verbatim (per the Open Questions resolution); **And** a row exists in `links` with that code.
- [ ] **Given** a short code that exists in the database, **When** a client `GET`s `/{code}`, **Then** the response is `302 Found` with `Location` header set to the stored `long_url` byte-for-byte; **And** the response body is empty.
- [ ] **Given** an arbitrary code that does NOT exist in the database (e.g. `zzzzz`), **When** a client `GET`s `/zzzzz`, **Then** the response is `404` with body `{"detail": "not found"}`; **And given** a code of invalid shape (e.g. `aaa`, `aaaaaaa`, `aa!aa`), **When** the client `GET`s it, **Then** the response is `404` and no DB query is issued (verifiable via SQLAlchemy event listener or repo spy in the integration test).
- [ ] **Given** `POST /shorten` is reached, **When** the body contains `long_url` with scheme `javascript:`, `data:`, `file:`, `ftp:`, or any non-`http(s)` scheme, OR a URL longer than 2048 characters, OR missing/malformed `long_url`, **Then** the response is `422 Unprocessable Entity` with the FastAPI validation-error envelope; **And** no row is inserted in `links`.
- [ ] **Given** `POST /shorten` is wired in `app/routes/shorten.py`, **When** the route declaration is inspected, **Then** it uses `Depends(require_auth)` and `require_auth` is a no-op function returning `None` (the JWT seam from TECH_SPEC §1).
- [ ] **Given** the service is running, **When** a client `GET`s `/healthz`, **Then** the response is `200 OK` with body `{"status": "ok"}`.
- [ ] **Given** the smoke test from TECH_SPEC §9, **When** executed against a fresh local instance, **Then** every command in the block succeeds and produces output matching the documented shapes (status codes + Location header).

---

### Story 3: Lock the spec with a passing test matrix + verification cascade

**As a** reviewer / approver,
**I want** the full test matrix from TECH_SPEC §8 to exist and pass, the logging policy from §5.5 to be implemented, and the verification cascade (ruff + bandit + pytest --cov >= 80%) to be green,
**so that** the acceptance gates in TECH_SPEC §11 are mechanically demonstrated and the PR is ready to merge.

**Priority:** Must
**Effort:** M
**Implements:** TECH_SPEC `§5.5 Logging policy` (redact full long_url; log scheme+host only), `§8 Testing Strategy` (unit + integration + fixtures + coverage gate), `§9 Local Run` (README smoke test), `§11 Acceptance Criteria` (all 7 gates).

**Acceptance Criteria:**

- [ ] **Given** the test suite in `tests/`, **When** `pytest --cov=src/ --cov-fail-under=80 --cov-report=term-missing` runs, **Then** it exits 0 with no failures; **And** the report shows line coverage at >= 80% overall; **And** critical-path modules (`app/schemas/link.py`, `app/services/shortener.py`, `app/routes/redirect.py`) are >= 95%.
- [ ] **Given** every disallowed URL scheme listed in TECH_SPEC §5.1 (`javascript:`, `data:`, `file:`, `ftp:`) plus an oversize URL (>2048 chars) plus a missing-scheme URL, **When** the unit suite runs, **Then** each input has a dedicated test asserting Pydantic rejects it with `ValidationError`.
- [ ] **Given** a `POST /shorten` integration test that captures stdout/log output, **When** the request completes, **Then** the emitted INFO log line contains only the generated code and the scheme+host of the long URL (e.g. `https://example.com`); **And** does NOT contain the path, query string, or fragment; **And** a 404 on `GET /{code}` emits a WARNING log.
- [ ] **Given** a `pytest` round-trip test, **When** it `POST`s a URL containing a query string and fragment then immediately `GET`s the returned code, **Then** the `Location` header equals the originally-submitted URL byte-for-byte.
- [ ] **Given** the verification cascade from TECH_SPEC §11, **When** `ruff check src/`, `ruff format --check src/`, `bandit -r src/`, and `pytest --cov=src/ --cov-fail-under=80` run sequentially, **Then** each exits 0 and bandit reports zero HIGH or MEDIUM findings.
- [ ] **Given** the project README, **When** a new developer follows the "Local Run" section verbatim from a fresh clone, **Then** they reach a working service and successfully execute the curl smoke-test pair (POST then GET) inside 5 minutes.

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Pydantic v2 URL-validation behavior differs from spec assumption (e.g. accepts `javascript:` by default, or rejects URLs with fragments) | Medium | High | First task of Story 2 is to write the scheme-rejection unit tests; if Pydantic's built-in `HttpUrl` does not enforce the allowlist, fall back to a `field_validator` parsing scheme manually. Either way the unit tests are the contract. |
| Alembic auto-generated migration drifts from the hand-written model (e.g. forgets the UNIQUE constraint) | Low | Medium | Story 1 AC #1 asserts UNIQUE on `code` after `alembic upgrade head`; verified by inspecting `sqlite_master` in a test or by failing to insert duplicates. |
| Coverage gate trips on Pydantic/SQLAlchemy boilerplate that has no logic to test | Medium | Low | `# pragma: no cover` is allowed only on lines with no decision logic (e.g. `from __future__ import annotations`). If the cascade fails on coverage, audit the missing lines before lowering the threshold. |
| `TestClient` follows redirects by default and Story 2 AC #2 expects to inspect the `Location` header | Low | Low | Use `client = TestClient(app); client.get(path, follow_redirects=False)` in redirect tests. Document in conftest. |

## Dependencies on Other Teams / Systems

| Dependency | Team / System | What We Need | Status | Deadline |
|-----------|--------------|-------------|--------|----------|
| None | -- | This cycle is fully self-contained: SQLite + FastAPI + ruff + bandit + pytest are all in-process and require no external coordination. | Confirmed | N/A |
