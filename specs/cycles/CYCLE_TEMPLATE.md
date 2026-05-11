# Cycle [NUMBER]: [CYCLE_NAME]

**Dates:** [START_DATE] -- [END_DATE]
**Status:** Planning | In Progress | Complete
**Goal:** [One sentence describing what this cycle delivers. e.g., "Users can sign up, log in, and manage their profile."]

---

## User Stories

### Story 1: [SHORT_TITLE]

**As a** [role],
**I want** [action],
**so that** [benefit].

**Priority:** Must / Should / Could
**Effort:** S / M / L

**Acceptance Criteria:**

- [ ] [FILL_IN: Specific, testable criterion]
  - Good: "Clicking 'Login with Google' redirects to Google consent screen within 2 seconds"
  - Bad: "Login works"
- [ ] [FILL_IN: Specific, testable criterion]
  - Good: "Submitting the form with an empty email field shows 'Email is required' inline error without page reload"
  - Bad: "Validation works"
- [ ] [FILL_IN: Specific, testable criterion]
  - Good: "After successful registration, user receives a welcome email within 60 seconds containing a verification link"
  - Bad: "Email is sent"

---

### Story 2: [SHORT_TITLE]

**As a** [role],
**I want** [action],
**so that** [benefit].

**Priority:** Must / Should / Could
**Effort:** S / M / L

**Acceptance Criteria:**

- [ ] [FILL_IN: Specific, testable criterion]
- [ ] [FILL_IN: Specific, testable criterion]
- [ ] [FILL_IN: Specific, testable criterion]

---

### Story 3: [SHORT_TITLE]

**As a** [role],
**I want** [action],
**so that** [benefit].

**Priority:** Must / Should / Could
**Effort:** S / M / L

**Acceptance Criteria:**

- [ ] [FILL_IN: Specific, testable criterion]
- [ ] [FILL_IN: Specific, testable criterion]
- [ ] [FILL_IN: Specific, testable criterion]

---

<!-- Add more stories as needed. Copy the block above. -->

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [FILL_IN: e.g., Third-party OAuth provider has downtime during integration] | [High/Medium/Low] | [High/Medium/Low] | [FILL_IN: e.g., Implement retry logic with exponential backoff; have fallback email/password auth] |
| [FILL_IN: e.g., Data model changes break existing API consumers] | [High/Medium/Low] | [High/Medium/Low] | [FILL_IN: e.g., Version the API; run old and new in parallel during migration window] |
| [FILL_IN] | [High/Medium/Low] | [High/Medium/Low] | [FILL_IN] |

## Dependencies on Other Teams / Systems

| Dependency | Team / System | What We Need | Status | Deadline |
|-----------|--------------|-------------|--------|----------|
| [FILL_IN: e.g., SSO configuration] | [FILL_IN: e.g., Identity team] | [FILL_IN: e.g., OAuth client credentials and redirect URI approved] | [Pending / Confirmed / Blocked] | [FILL_IN] |
| [FILL_IN: e.g., Email service access] | [FILL_IN: e.g., Platform team] | [FILL_IN: e.g., SendGrid API key with transactional email permissions] | [Pending / Confirmed / Blocked] | [FILL_IN] |
| [FILL_IN] | [FILL_IN] | [FILL_IN] | [Pending / Confirmed / Blocked] | [FILL_IN] |
