# Cycle [NUMBER] -- Task Breakdown

**Cycle:** [CYCLE_NAME]
**Dates:** [START_DATE] -- [END_DATE]
**Total Tasks:** [COUNT]

---

> **Dependency Rule:** Execute tasks in order, respecting dependencies. A task cannot start until all its dependencies are Done. If a task is Blocked, escalate immediately -- do not skip it and start dependent tasks.

---

## Task Table

| Task ID | Description | Complexity | Dependencies | Status | Assignee | Verification |
|---------|-------------|-----------|-------------|--------|----------|-------------|
| TASK-001 | [FILL_IN: e.g., Set up project scaffold with FastAPI, pyproject.toml, and directory structure] | S | None | Pending | [FILL_IN] | [FILL_IN: e.g., `uv run uvicorn app.main:app` starts without errors] |
| TASK-002 | [FILL_IN: e.g., Create User database model with SQLAlchemy and initial Alembic migration] | M | TASK-001 | Pending | [FILL_IN] | [FILL_IN: e.g., `alembic upgrade head` succeeds; User table exists in DB] |
| TASK-003 | [FILL_IN: e.g., Implement POST /api/v1/users registration endpoint with input validation] | M | TASK-002 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/api/test_users.py::test_register_user -v` passes] |
| TASK-004 | [FILL_IN: e.g., Implement POST /api/v1/auth/login with JWT token generation] | M | TASK-002 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/api/test_auth.py::test_login -v` passes] |
| TASK-005 | [FILL_IN: e.g., Add authentication middleware and protect user endpoints] | S | TASK-003, TASK-004 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/api/test_auth.py::test_protected_endpoint -v` passes] |
| TASK-006 | [FILL_IN: e.g., Implement GET /api/v1/users/me profile endpoint] | S | TASK-005 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/api/test_users.py::test_get_profile -v` passes] |
| TASK-007 | [FILL_IN: e.g., Implement PUT /api/v1/users/me profile update endpoint] | S | TASK-006 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/api/test_users.py::test_update_profile -v` passes] |
| TASK-008 | [FILL_IN: e.g., Add integration tests for full registration-login-profile flow] | M | TASK-007 | Pending | [FILL_IN] | [FILL_IN: e.g., `pytest tests/integration/ -v` passes with all tests green] |

<!-- Add more rows as needed. Maintain sequential TASK-IDs. -->

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
[FILL_IN: ASCII dependency visualization]

Example:
  TASK-001
      |
      v
  TASK-002
      |
      +-------+-------+
      |               |
      v               v
  TASK-003        TASK-004
      |               |
      +-------+-------+
              |
              v
          TASK-005
              |
              v
          TASK-006
              |
              v
          TASK-007
              |
              v
          TASK-008
```

## Notes

- Each task should be completable in a single Claude Code session.
- The Verification column defines exactly how to prove a task is done. If you cannot run the verification command and see it pass, the task is not done.
- When a task status changes, update this file immediately. This is the single source of truth for progress.
