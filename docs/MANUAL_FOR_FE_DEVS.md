# Debussy Manual for Frontend Developers

A practical guide to using Claude Debussy for orchestrating multi-phase frontend projects.

---

## What is Debussy?

Debussy is an orchestration tool that runs Claude AI through multi-phase implementation plans. Instead of manually prompting Claude for each task, you write a structured plan and Debussy executes it phase by phase, with quality gates ensuring each phase is complete before moving to the next.

**Think of it like CI/CD for AI-assisted development** - your plan is the pipeline, each phase is a job, and gates are your quality checks.

---

## Prerequisites

Before starting, ensure you have:

1. **Node.js 18+** and your package manager (npm, pnpm, yarn, or bun)
2. **Docker Desktop** (only for sandbox mode)
3. **Claude CLI** authenticated (`claude auth login`)
4. **Git** installed
5. **uv** - Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

> **Standard Mode vs Sandbox Mode:**
> - **Standard Mode**: Claude runs directly on your machine and uses your local Node.js, pnpm, etc. No Docker needed.
> - **Sandbox Mode**: Claude runs in Docker. The container only has npm by default - see [Customizing the Sandbox](#customizing-the-sandbox-for-your-stack) to add pnpm/yarn/bun.

---

## Installation (One-Time Setup)

### Option A: Standard Mode (Quick Start)

Run Claude directly on your machine. Best for trusted projects where you want fast iteration.

```bash
# In your frontend project folder
cd ~/projects/my-frontend-app

# Install Debussy (adds it to devDependencies via uv)
# If you don't have uv: https://docs.astral.sh/uv/getting-started/installation/
uv add --dev git+https://github.com/matt-grain/Claude-Debussy.git

# Initialize your project for Debussy
uv run debussy init .

# Verify installation
uv run debussy --help
```

### Option B: Sandbox Mode (Recommended for Safety)

Run Claude inside Docker containers with restricted network access. Best for:
- Working with untrusted code
- Projects with sensitive data
- Team environments where you want consistent isolation

```bash
# Clone Debussy to a tools folder (NOT inside your project)
git clone https://github.com/matt-grain/Claude-Debussy.git ~/tools/debussy
cd ~/tools/debussy

# Install dependencies
uv sync

# Build the sandbox Docker image (takes a few minutes)
uv run debussy sandbox-build

# Initialize YOUR project (from the debussy folder)
uv run debussy init ~/projects/my-frontend-app

# Verify sandbox is ready
uv run debussy sandbox-status
```

---

## Creating Your First Plan

First, create a folder for your plan:

```bash
cd ~/projects/my-frontend-app
mkdir -p plans/my-feature
```

### Option A: Ask Claude to Generate It (Recommended)

Don't write plans manually - let Claude (Opus recommended) generate them for you.

**Step 1:** Open Claude Code or claude.ai and use this prompt:

```
I need a Debussy-compliant multi-phase plan for: [describe your feature]

Project context:
- Framework: Next.js 14 with App Router
- State: Zustand
- Styling: Tailwind CSS
- i18n: next-intl (FR + EN)
- API: Centralized in src/lib/api.ts
- Package manager: pnpm

Requirements:
1. Create a MASTER_PLAN.md following Debussy format
2. Create phase files (phase-1.md, phase-2.md, etc.)
3. Each phase must have:
   - Process Wrapper section with checkboxes
   - Gates section (pnpm exec tsc, pnpm lint, pnpm build minimum)
   - Tasks section with numbered subtasks
   - Files to Create/Modify table
4. Gates must be actual shell commands that return exit code 0 on success

Use this frontend phase template as reference:
[paste the PHASE_FRONTEND.md template from docs/templates/plans/]
```

**Step 2:** Save the generated files to `plans/my-feature/`:
- `MASTER_PLAN.md`
- `phase-1.md`
- `phase-2.md`
- etc.

**Step 3:** Validate the plan:

```bash
uv run debussy audit plans/my-feature/MASTER_PLAN.md -v
```

Fix any issues Claude points out, then you're ready to run!

---

### Option B: Write It Manually

If you prefer to write plans by hand, follow this structure.

**Step 1:** Create the Master Plan

Create `plans/my-feature/MASTER_PLAN.md`:

```markdown
# User Dashboard - Master Plan

**Created:** 2026-01-16
**Status:** Draft

---

## Overview

Add a user dashboard showing activity metrics, recent actions, and quick navigation.

## Goals

1. **User Engagement** - Give users a personalized landing page
2. **Quick Actions** - Reduce clicks to common tasks
3. **Activity Visibility** - Show recent activity at a glance

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Data Layer](phase-1.md) | API integration, types, store | Low | Pending |
| 2 | [Components](phase-2.md) | Dashboard widgets | Low | Pending |
| 3 | [Integration](phase-3.md) | Page assembly, routing | Medium | Pending |

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| TypeScript errors | 0 | 0 |
| ESLint errors | 0 | 0 |
| Build passes | Yes | Yes |
| i18n coverage | 100% | 100% |

## Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3
```

Each phase must complete before the next can start.

## Out of Scope

- Backend API changes (assumed already deployed)
- Mobile-specific layouts (future phase)

---

## Quick Reference

**Key Files:**
- `src/app/dashboard/page.tsx` - Main dashboard page
- `src/lib/api.ts` - API client (all calls go here)
- `src/store/dashboardStore.ts` - Dashboard state

**Test Locations:**
- `src/__tests__/dashboard/`
```

**Step 2:** Create Phase Files

Create `plans/my-feature/phase-1.md`:

```markdown
# User Dashboard Phase 1: Data Layer

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A

---

## Process Wrapper (MANDATORY)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Write notes to: `notes/NOTES_dashboard_phase_1.md`

## Gates
- tsc: 0 errors
- eslint: 0 errors
- build: success

---

## Overview

Set up the data layer: TypeScript types, API endpoints, and Zustand store.

## Tasks

### 1. Type Definitions
- [ ] 1.1: Create `src/types/dashboard.ts` with DashboardData, ActivityItem, QuickAction interfaces
- [ ] 1.2: Export types from `src/types/index.ts`

### 2. API Integration
- [ ] 2.1: Add `getDashboardData()` to `src/lib/api.ts`
- [ ] 2.2: Add `getRecentActivity()` to `src/lib/api.ts`

### 3. State Management
- [ ] 3.1: Create `src/store/dashboardStore.ts` using Zustand
- [ ] 3.2: Add loading, error, and data states
- [ ] 3.3: Add fetch actions with error handling

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/types/dashboard.ts` | Create | Dashboard type definitions |
| `src/types/index.ts` | Modify | Export new types |
| `src/lib/api.ts` | Modify | Add dashboard API calls |
| `src/store/dashboardStore.ts` | Create | Dashboard state management |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| API calls | `src/lib/api.ts` | Centralized, never in components |
| State | `src/store/authStore.ts` | Zustand pattern with async actions |
| Types | `src/types/index.ts` | All interfaces exported from here |

## Acceptance Criteria
- [ ] All TypeScript compiles without errors
- [ ] All API calls go through `lib/api.ts`
- [ ] Store follows existing Zustand patterns
- [ ] No hardcoded URLs
```

Repeat for `phase-2.md` and `phase-3.md` following the same structure.

**Step 3:** Validate the plan:

```bash
uv run debussy audit plans/my-feature/MASTER_PLAN.md -v
```

---

## Running Debussy

### Validate Your Plan First (Dry Run)

```bash
# Standard mode (from your project folder)
uv run debussy run plans/my-feature/MASTER_PLAN.md --dry-run

# Sandbox mode (from debussy folder)
uv run debussy run --sandbox ~/projects/my-frontend-app/plans/my-feature/MASTER_PLAN.md --dry-run
```

This checks your plan structure without executing anything.

### Execute the Plan

```bash
# Standard mode - interactive dashboard
uv run debussy run plans/my-feature/MASTER_PLAN.md

# Sandbox mode - interactive dashboard
uv run debussy run --sandbox ~/projects/my-frontend-app/plans/my-feature/MASTER_PLAN.md

# YOLO mode - no dashboard (for CI or background execution)
uv run debussy run plans/my-feature/MASTER_PLAN.md --yolo
```

### Interactive Dashboard

When running in interactive mode, you'll see a live dashboard:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Debussy │ Phase 2/3: Components │ ● Running │ ⏱ 00:05:23           │
│  [s]tatus  [p]ause  [v]erbose (on)  [k]skip  [q]uit                 │
├─────────────────────────────────────────────────────────────────────┤
│ > Reading src/components/Dashboard/ActivityFeed.tsx                  │
│ > Edit: src/components/Dashboard/ActivityFeed.tsx:12-45             │
│ > Running gate: tsc --noEmit... ✓                                   │
│ > Running gate: eslint... ✓                                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Hotkeys:**
| Key | Action |
|-----|--------|
| `s` | Show detailed status |
| `p` | Pause/resume execution |
| `v` | Toggle verbose logging |
| `k` | Skip current phase (with confirmation) |
| `q` | Quit gracefully (can resume later) |

### Resume After Interruption

If you quit or it crashes, Debussy saves state:

```bash
# Resume from where you left off
uv run debussy run plans/my-feature/MASTER_PLAN.md --resume

# Start fresh (ignore previous progress)
uv run debussy run plans/my-feature/MASTER_PLAN.md --restart
```

---

## Quality Gates

Gates are shell commands that must pass before a phase is complete. Common frontend gates:

```markdown
## Gates
- tsc: 0 TypeScript errors
- eslint: 0 linting errors
- build: successful build
- test: all tests pass
```

Debussy runs these **independently** after Claude claims completion - it doesn't trust Claude's word, it verifies.

### Custom Architecture Gates

For frontend projects, add custom validation scripts:

```markdown
## Gates
- tsc: 0 errors
- eslint: 0 errors
- build: success
- node scripts/check-api-usage.js: all API calls centralized
- node scripts/check-hardcoded-urls.js: no localhost URLs
- node scripts/check-i18n-coverage.js: all strings translated
```

Example `scripts/check-api-usage.js`:
```javascript
#!/usr/bin/env node
// Fail if any component imports fetch directly instead of using lib/api.ts
const { execSync } = require('child_process');

try {
  const result = execSync('grep -r "fetch(" src/components/ --include="*.tsx" || true', { encoding: 'utf8' });
  if (result.trim()) {
    console.error('ERROR: Direct fetch() calls found in components. Use lib/api.ts instead.');
    console.error(result);
    process.exit(1);
  }
  console.log('OK: All API calls use lib/api.ts');
} catch (e) {
  process.exit(1);
}
```

---

## Troubleshooting

### "Cannot find module debussy"

You're in the wrong folder or haven't installed:

```bash
# Standard mode: run from your project folder where you did `uv add`
cd ~/projects/my-frontend-app
uv run debussy --help

# Sandbox mode: run from the debussy folder
cd ~/tools/debussy
uv run debussy --help
```

### "Docker not available" (Sandbox Mode)

1. Ensure Docker Desktop is running
2. Check with: `docker ps`
3. Rebuild if needed: `uv run debussy sandbox-build --no-cache`

### Gates Failing

Check the logs in `.debussy/logs/`:

```bash
# See latest log
cat .debussy/logs/run_*_phase_*.log | tail -100
```

Common issues:
- **tsc fails**: Check `tsconfig.json` is valid
- **eslint fails**: Run `pnpm lint --fix` manually first
- **build fails**: Check for missing dependencies

### Claude Gets Stuck or Loops

Press `k` to skip the phase, or `q` to quit. Then:

1. Check the notes file for what was completed
2. Manually fix any blocking issues
3. Resume with `--resume`

### Plan Validation Errors

Run audit to see detailed issues:

```bash
uv run debussy audit plans/my-feature/MASTER_PLAN.md -v
```

---

## Customizing the Sandbox for Your Stack

The default sandbox image includes **npm** only. If your project uses **pnpm**, **yarn**, or **bun**, you'll need to customize the Dockerfile.

### Where's the Dockerfile?

After cloning Debussy, the Dockerfile is at:

```
~/tools/debussy/src/debussy/docker/Dockerfile.sandbox
```

### Adding pnpm

Edit `Dockerfile.sandbox` and add pnpm installation after the Claude Code install:

```dockerfile
# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

# ADD THIS: Install pnpm globally
RUN npm install -g pnpm
```

### Adding Yarn (Classic or Berry)

For Yarn Classic (1.x):

```dockerfile
# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

# ADD THIS: Install Yarn Classic
RUN npm install -g yarn
```

For Yarn Berry (2.x+), it's usually committed to your repo via `.yarn/releases/`, so no Dockerfile change needed - just ensure your project has `yarn` in its repo.

### Adding Bun

```dockerfile
# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

# ADD THIS: Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/home/claude/.bun/bin:${PATH}"
```

**Note:** The Bun install runs as root, so you may need to adjust ownership or install as the `claude` user.

### Adding Multiple Tools

You can combine them:

```dockerfile
# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION}

# Frontend tooling
RUN npm install -g pnpm yarn
```

### Rebuild After Changes

After editing the Dockerfile, rebuild the image:

```bash
cd ~/tools/debussy
uv run debussy sandbox-build --no-cache
```

The `--no-cache` flag ensures Docker doesn't use cached layers from the old image.

### Verify Your Tools

Test that your tools are available in the sandbox:

```bash
# Start a shell in the sandbox container
docker run -it --rm debussy-sandbox:latest /bin/bash

# Inside the container, verify:
pnpm --version
yarn --version
node --version
npm --version
```

### Project-Specific Dockerfile (Advanced)

If you don't want to modify Debussy's Dockerfile, you can create your own image that extends it:

Create `Dockerfile.my-sandbox` in your project:

```dockerfile
FROM debussy-sandbox:latest

USER root
RUN npm install -g pnpm
USER claude
```

Build it:

```bash
docker build -f Dockerfile.my-sandbox -t my-project-sandbox:latest .
```

Then edit your `.debussy/config.yaml` to use the custom image:

```yaml
sandbox_image: my-project-sandbox:latest
```

> **Note:** Custom sandbox images via config are not yet implemented. For now, modify the main Dockerfile or rebuild the `debussy-sandbox:latest` image with your tools.

### Common Tooling Recipes

| Stack | Add to Dockerfile |
|-------|-------------------|
| pnpm | `RUN npm install -g pnpm` |
| Yarn Classic | `RUN npm install -g yarn` |
| Bun | `RUN curl -fsSL https://bun.sh/install \| bash` |
| Nx | `RUN npm install -g nx` |
| Turborepo | `RUN npm install -g turbo` |
| Angular CLI | `RUN npm install -g @angular/cli` |
| Vue CLI | `RUN npm install -g @vue/cli` |
| Create React App | Already works (uses npx) |
| Vite | Already works (uses npx) |

### Gates Must Match Your Package Manager

Remember to use the correct commands in your gates:

```markdown
## Gates (pnpm project)
- pnpm exec tsc --noEmit: 0 errors
- pnpm lint: 0 errors
- pnpm build: success
- pnpm test: all pass
```

```markdown
## Gates (yarn project)
- yarn tsc --noEmit: 0 errors
- yarn lint: 0 errors
- yarn build: success
- yarn test: all pass
```

```markdown
## Gates (bun project)
- bun run tsc --noEmit: 0 errors
- bun lint: 0 errors
- bun run build: success
- bun test: all pass
```

---

## Best Practices

### 1. Start Small
Your first plan should be 2-3 phases maximum. Learn the workflow before tackling big refactors.

### 2. Make Gates Specific
Bad: `test: tests pass`
Good: `pnpm test --coverage --passWithNoTests`

### 3. Include File Lists
Always include the "Files to Create/Modify" table - it helps Claude stay focused.

### 4. Use the Notes
Each phase should write to `notes/NOTES_{feature}_phase_{N}.md`. These help Claude in later phases understand decisions made earlier.

### 5. Commit Between Phases
Debussy auto-commits at phase boundaries by default. This makes rollback easy.

### 6. Review Before Merging
After Debussy completes, review the changes like any PR. It's AI-assisted, not AI-replaced.

---

## Templates Reference

### Master Plan Template

See: [`docs/templates/plans/MASTER_TEMPLATE.md`](templates/plans/MASTER_TEMPLATE.md)

### Frontend Phase Template

See: [`docs/templates/plans/PHASE_FRONTEND.md`](templates/plans/PHASE_FRONTEND.md)

Key sections for frontend phases:
- **Gates**: tsc, eslint, build (minimum)
- **i18n Keys to Add**: For internationalized apps
- **Components to Create**: With props and purpose
- **Patterns to Follow**: Reference existing code

---

## Quick Command Reference

| Command | Purpose |
|---------|---------|
| `debussy init .` | Initialize current project |
| `debussy run PLAN.md` | Execute a plan |
| `debussy run PLAN.md --dry-run` | Validate without executing |
| `debussy run PLAN.md --resume` | Resume interrupted run |
| `debussy run PLAN.md --restart` | Start fresh |
| `debussy run PLAN.md --yolo` | No interactive dashboard |
| `debussy run --sandbox PLAN.md` | Run in Docker isolation |
| `debussy status` | Show current run status |
| `debussy history` | Show past runs |
| `debussy audit PLAN.md` | Validate plan structure |
| `debussy sandbox-status` | Check Docker setup |
| `debussy sandbox-build` | Build Docker image |

---

## Getting Help

- **Debussy issues**: https://github.com/matt-grain/Claude-Debussy/issues
- **Plan validation errors**: Run `debussy audit PLAN.md -vv` for verbose output
- **Claude behavior issues**: Check `.debussy/logs/` for session transcripts
