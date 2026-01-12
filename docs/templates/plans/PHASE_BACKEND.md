# {Feature} Phase {N}: {Phase Title}

**Status:** Pending
**Master Plan:** [{feature}-master.md]({feature}-master.md)
**Depends On:** {Phase N-1 link or N/A}

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_{feature}_phase_{N-1}.md`
- [ ] doc-sync-manager agent: sync tasks to ACTIVE.md (REQUIRED)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  cd backend
  # Code quality
  uv run ruff format . && uv run ruff check --fix .
  uvx ty check . && uv run pyright
  uv run bandit -r . -x ./tests && uv run radon cc . -a
  uv run lint-imports

  # Architecture checks
  python scripts/check_service_db_access.py       # Services → repos
  python scripts/check_service_http_exceptions.py # No HTTPException in services
  python scripts/check_router_db_access.py        # Routers → services
  python scripts/check_layer_imports.py           # No cross-layer imports
  ```
- [ ] task-validator agent: full validation (REQUIRED)
- [ ] Fix loop: repeat pre-validation until clean
- [ ] doc-sync-manager agent: cleanup ACTIVE.md, BUGS.md, update plan status (REQUIRED)
- [ ] Write `notes/NOTES_{feature}_phase_{N}.md` (REQUIRED)

## Gates (must pass before completion)
- bandit: 0 HIGH/MEDIUM findings
- radon: no functions with complexity D+ (>20)
- coverage: >= 70%
- ruff: 0 errors
- ty/pyright: 0 errors
- **architecture scripts: 0 violations** (services use repos, no HTTPException, layer imports)

---

## Overview

{Brief description of what this phase accomplishes}

## Dependencies
- Previous phase: {link or N/A}
- External: {any external dependencies}

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {Risk 1} | Low/Medium/High | Low/Medium/High | {How to mitigate} |

---

## Tasks

### 1. {Task Group Name}
- [ ] 1.1: {description}
- [ ] 1.2: {description}

### 2. {Task Group Name}
- [ ] 2.1: {description}
- [ ] 2.2: {description}

### 3. {Task Group Name}
- [ ] 3.1: {description}

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/repositories/{name}.py` | Create | {purpose} |
| `backend/services/{name}.py` | Create | {purpose} |
| `backend/routers/{name}.py` | Modify | {purpose} |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Repository | `backend/repositories/idea_repository.py` | {how to apply} |
| Service | `backend/services/idea_service.py` | {how to apply} |

## Test Strategy
- [ ] Unit tests for new code
- [ ] Integration tests for modified endpoints
- [ ] Regression tests for existing functionality

## Acceptance Criteria
- [ ] All tasks completed
- [ ] All gates passing
- [ ] Tests written and passing
- [ ] No security vulnerabilities introduced

## Rollback Plan

{How to revert if something goes wrong}

---

## Agents to Use

| When | Agent | Purpose |
|------|-------|---------|
| Before implementation | `python-backend-architect` | Design review (if complex) |
| After implementation | `code-review-expert` | Code quality review |
| After implementation | `task-validator` | REQUIRED - validation |
| Start + End | `doc-sync-manager` | REQUIRED - documentation |
| If auth/data touched | `cybersec-audit-expert` | Security review |

## Implementation Notes

{Any additional notes, decisions, or context for implementation}
