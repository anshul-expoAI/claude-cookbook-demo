# PROJECT: Internal URL Shortener (v1)

## Problem Statement

The team needs a small, self-hostable URL shortener for internal use -- pasting long internal links (dashboards, docs, build artifacts, ticket queries) into Slack and tickets is noisy and hard to read. v1 is a demo-grade tool: a service that accepts a long URL, returns a 5-6 character short code, and 302-redirects to the original URL when the short code is visited. No analytics, no user accounts, no custom aliases, no expiration. Auth (JWT) is explicitly deferred to a follow-up spec, but the design must leave a clear seam for it.

## Goals

- POST a long URL, get back a short code.
- GET the short code, get a 302 redirect to the long URL.
- Run locally with one command (`uv run uvicorn`), zero external dependencies.
- Match the team's FastAPI + SQLAlchemy patterns so a later migration to Postgres is a `DATABASE_URL` swap.

## Non-Goals (Out of Scope for v1)

- User accounts, JWT auth, or any authorization (separate spec).
- Custom / vanity aliases (user-supplied codes).
- Link expiration / TTL.
- Click analytics, geo, referrer tracking.
- Rate limiting beyond what FastAPI gives for free.
- Profanity / abuse filtering on generated codes.
- Bulk import, link editing, link deletion via API.
- Multi-tenancy.

## Solution Approaches

### Approach 1: Random base62, retry-on-collision (CHOSEN)

Generate a random 5-6 character base62 (`[A-Za-z0-9]`) code. Insert into the DB with a unique constraint on `code`; on `IntegrityError` (collision), regenerate and retry up to N times. Start at 5 chars; if the 5-char space starts to fill (or after N consecutive 5-char collisions), promote new codes to 6 chars.

- **Pros:** unguessable, no enumeration, simple, no external state. Collision probability is negligible at our volume (5 chars = 916M codes, 6 chars = 56.8B). Trivially testable.
- **Cons:** non-deterministic -- the same long URL can produce different short codes if submitted twice. For an internal tool, this is acceptable (and arguably desirable for privacy).
- **Effort:** S
- **Risk:** Low. The only sharp edge is the retry cap; we'll log and 503 if exceeded (effectively impossible at expected volume but failing loud is better than spinning).

### Approach 2: Hash-based (deterministic)

Hash the normalized long URL (e.g. SHA-256), base62-encode, take first 6 chars. Same input URL always yields the same code.

- **Pros:** deduplicates identical submissions for free. Idempotent.
- **Cons:** truncated hashes still collide -- and when they do, two different URLs would map to the same code, which is much worse than retrying a random code. Mitigating that requires the same retry/suffix logic as Approach 1, so we get the complexity without keeping the determinism property. URL normalization is also its own rabbit hole (trailing slash? query order? fragments?).
- **Effort:** M
- **Risk:** Medium. Determinism is a feature we don't actually need in v1; collision handling reintroduces the complexity it was meant to avoid.

### Approach 3: Sequential auto-increment, base62-encoded

Each row gets an integer primary key from a sequence; the short code is that integer base62-encoded.

- **Pros:** zero collisions by construction. Codes are short for small IDs.
- **Cons:** codes are **enumerable** -- visiting `/aaaaab` after `/aaaaaa` reveals neighboring URLs. For an internal tool that may contain links to private dashboards, this is a real concern even without formal auth. Also leaks volume (anyone can count links by visiting the latest code).
- **Effort:** S
- **Risk:** Medium. The enumeration property is the deal-breaker; the whole point of an internal tool is that "internal" is the access control until JWT lands.

### Approach 4: UUID-derived

Generate a UUIDv4 per link, base62-encode it, truncate to 6 chars.

- **Pros:** standard primitive, easy to reason about.
- **Cons:** truncating a UUID is functionally identical to Approach 1 with extra steps -- you still have a random 6-char string with collision retry. Doesn't add anything.
- **Effort:** S
- **Risk:** Low, but no upside over Approach 1.

## Recommendation: Approach 1

Random base62 with retry-on-collision is the cleanest match for v1's constraints: it gives unguessable codes (the only access control until JWT lands), avoids the deterministic-hash collision-handling trap, and avoids the enumeration leak of sequential IDs. It's also the smallest amount of code.

## Estimation

**Overall: S (under 1 day).** Single service, single table, three endpoints, well-trodden FastAPI patterns. The longest task will be writing the test matrix, not the implementation.

## Open Questions for Approver

1. Is "no rate limiting in v1" acceptable for an internal-only demo, or should we slot in a coarse per-IP cap (10 req/s) before merge?
2. Should we strip URL fragments (`#...`) on store, or preserve them verbatim? (Recommendation: preserve verbatim -- fragments are client-side and may be meaningful.)
3. Should `POST /shorten` reject non-`http(s)` schemes (e.g. `javascript:`, `data:`, `file:`)? (Strong recommendation: **yes**, allowlist `http` and `https` only -- open redirect to `javascript:` URLs is a real XSS vector even in an internal tool.)
