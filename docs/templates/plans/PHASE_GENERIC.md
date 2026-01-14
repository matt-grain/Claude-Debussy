# {feature} Phase {phase_num}: {phase_title}

**Status:** Pending
**Master Plan:** [{feature}-MASTER_PLAN.md]({feature_slug}-MASTER_PLAN.md)
**Depends On:** {prev_phase_link}

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `{prev_notes_path}`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Code quality - adjust for your project
  # Example for Python:
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/
  uv run pytest tests/ -v

  # Example for JavaScript/TypeScript:
  npm run lint --fix
  npm run type-check
  npm test
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `{notes_output_path}` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: 0 errors
- type-check: 0 errors
- tests: All tests pass
- security: No high severity issues

---

## Overview

{Brief description of what this phase accomplishes and why it's needed}

## Dependencies
- Previous phase: {prev_phase_link}
- External: {any external dependencies or N/A}

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| {Risk 1} | Low/Medium/High | Low/Medium/High | {How to mitigate} |
| {Risk 2} | Low/Medium/High | Low/Medium/High | {How to mitigate} |

---

## Tasks

### 1. {Task Group Name}
- [ ] 1.1: {Specific task description}
- [ ] 1.2: {Specific task description}

### 2. {Task Group Name}
- [ ] 2.1: {Specific task description}
- [ ] 2.2: {Specific task description}

### 3. {Task Group Name}
- [ ] 3.1: {Specific task description}

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `{file_path_1}` | Create/Modify | {Purpose of changes} |
| `{file_path_2}` | Create/Modify | {Purpose of changes} |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| {Pattern 1} | {Reference file or doc} | {How to apply it} |
| {Pattern 2} | {Reference file or doc} | {How to apply it} |

## Test Strategy

- [ ] Unit tests for new code
- [ ] Integration tests for modified functionality
- [ ] Regression tests for existing functionality
- [ ] Manual testing checklist (if applicable)

## Acceptance Criteria

**ALL must pass:**

- [ ] All tasks completed
- [ ] All gates passing
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced

## Rollback Plan

{Describe how to safely revert changes if something goes wrong. Include specific commands, backups, or database migrations to reverse.}

---

## Implementation Notes

{Space for additional notes, architectural decisions, or important context discovered during implementation}
