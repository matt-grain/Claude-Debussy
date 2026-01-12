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
  cd frontend
  # Code quality
  pnpm lint --fix
  pnpm exec tsc --noEmit
  pnpm build
  pnpm audit

  # Architecture checks
  node scripts/check-api-usage.js        # Must use @/lib/api.ts
  node scripts/check-hardcoded-urls.js   # No localhost/IP URLs (CORS)
  ```
- [ ] i18n-translator-expert agent: verify FR/EN keys (REQUIRED)
- [ ] task-validator agent: full validation (REQUIRED)
- [ ] Fix loop: repeat pre-validation until clean
- [ ] doc-sync-manager agent: cleanup ACTIVE.md, BUGS.md, update plan status (REQUIRED)
- [ ] Write `notes/NOTES_{feature}_phase_{N}.md` (REQUIRED)

## Gates (must pass before completion)
- tsc: 0 errors
- eslint: 0 errors
- build: success
- audit: 0 high/critical vulnerabilities
- i18n: all strings translated (FR + EN)
- **architecture scripts: 0 violations** (centralized API, no hardcoded URLs)

---

## Overview

{Brief description of what this phase accomplishes}

## Dependencies
- Previous phase: {link or N/A}
- Backend endpoints: {list any required API endpoints}
- External: {any external dependencies}

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
| `frontend/src/components/{Name}.tsx` | Create | {purpose} |
| `frontend/src/app/{path}/page.tsx` | Modify | {purpose} |
| `frontend/src/lib/api.ts` | Modify | {purpose} |
| `frontend/src/i18n/locales/fr.json` | Modify | Add FR translations |
| `frontend/src/i18n/locales/en.json` | Modify | Add EN translations |

## Components to Create

| Component | Location | Props | Purpose |
|-----------|----------|-------|---------|
| `{ComponentName}` | `components/` | `{prop: type}` | {purpose} |

## i18n Keys to Add

| Key | FR | EN |
|-----|----|----|
| `{namespace}.{key}` | {French text} | {English text} |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| API calls | `lib/api.ts` | Centralized, never in components |
| State | `store/authStore.ts` | Zustand for global state |
| Types | `types/index.ts` | All interfaces here |
| Components | `components/Button.tsx` | Small, single responsibility |

## Accessibility Checklist
- [ ] Semantic HTML elements used
- [ ] ARIA labels where needed
- [ ] Keyboard navigation works
- [ ] Color contrast sufficient
- [ ] Focus states visible

## Acceptance Criteria
- [ ] All tasks completed
- [ ] All gates passing
- [ ] All i18n keys added (FR + EN)
- [ ] Responsive design works
- [ ] Accessibility requirements met

## Rollback Plan

{How to revert if something goes wrong}

---

## Agents to Use

| When | Agent | Purpose |
|------|-------|---------|
| After implementation | `code-review-expert` | Code quality review |
| After implementation | `i18n-translator-expert` | REQUIRED - translation check |
| After implementation | `task-validator` | REQUIRED - validation |
| Start + End | `doc-sync-manager` | REQUIRED - documentation |
| For UI components | `ux-ui-design-expert` | Design review |
| If auth/data touched | `cybersec-audit-expert` | Security review |

## Implementation Notes

{Any additional notes, decisions, or context for implementation}
