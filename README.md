# Claude Orchestrator

A Python orchestrator for multi-phase Claude CLI sessions with compliance verification, state persistence, and real-time streaming output.

## Overview

Claude Orchestrator coordinates complex, multi-phase projects by:
- Spawning ephemeral Claude CLI sessions for each phase
- Tracking state and dependencies between phases
- Verifying compliance (gates, required agents, notes)
- Providing real-time streaming output
- Supporting automatic retries with remediation

## Installation

```bash
# Clone the repository
git clone https://github.com/matt-grain/Claude-Orchestrator.git
cd Claude-Orchestrator

# Install with uv
uv pip install -e .

# Or add to your project
uv add --dev "claude-orchestrator @ file:///path/to/Claude-Orchestrator"
```

## Quick Start

### 1. Create a Master Plan

Create `docs/master-plan.md`:

```markdown
# My Project - Master Plan

**Created:** 2026-01-12
**Status:** Draft

## Overview

Description of what you're building.

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Setup](phase1-setup.md) | Create base files | Low | Pending |
| 2 | [Implementation](phase2-impl.md) | Core logic | Medium | Pending |

## Dependencies

Phase 1 --> Phase 2
```

### 2. Create Phase Files

Create `docs/phase1-setup.md`:

```markdown
# Phase 1: Setup

**Status:** Pending
**Master Plan:** [master-plan.md](master-plan.md)
**Depends On:** N/A

---

## Process Wrapper (MANDATORY)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates
- echo: must pass

---

## Tasks

### 1. Create Base Structure
- [ ] 1.1: Create `src/module.py` with basic structure
- [ ] 1.2: Create `tests/test_module.py` placeholder
```

### 3. Run the Orchestrator

```bash
# Dry run - validate plan without executing
orchestrate run docs/master-plan.md --dry-run

# Full run with default model (sonnet)
orchestrate run docs/master-plan.md

# Use haiku for faster/cheaper execution
orchestrate run docs/master-plan.md --model haiku

# Use opus for complex tasks
orchestrate run docs/master-plan.md --model opus
```

## CLI Commands

### `orchestrate run`

Start orchestrating a master plan.

```bash
orchestrate run <master-plan.md> [options]

Options:
  --dry-run, -n     Parse and validate only, don't execute
  --phase, -p       Start from specific phase ID
  --model, -m       Claude model: haiku, sonnet, opus (default: sonnet)
```

### `orchestrate status`

Show current orchestration status.

```bash
orchestrate status [--run RUN_ID]
```

### `orchestrate history`

List past orchestration runs.

```bash
orchestrate history [--limit N]
```

### `orchestrate done`

Signal phase completion (called by Claude worker).

```bash
orchestrate done --phase 1 --status completed
orchestrate done --phase 1 --status blocked --reason "Missing dependency"
```

### `orchestrate resume`

Resume a paused orchestration run.

```bash
orchestrate resume
```

## Configuration

Create `.orchestrator/config.yaml`:

```yaml
timeout: 1800          # Phase timeout in seconds (default: 30 min)
max_retries: 2         # Max retry attempts per phase
model: sonnet          # Default model: haiku, sonnet, opus
strict_compliance: true

notifications:
  enabled: true
  provider: desktop    # desktop, ntfy, none
```

## Phase File Format

### Required Sections

```markdown
# Phase N: Title

**Status:** Pending
**Master Plan:** [link](master-plan.md)
**Depends On:** [Phase N-1](phaseN-1.md) or N/A

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_phase_N-1.md`  (if applicable)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Write notes to: `notes/NOTES_phase_N.md`

## Gates
- command: description

---

## Tasks
...
```

### Optional: Required Agents

```markdown
## Process Wrapper (MANDATORY)
- [ ] **AGENT:doc-sync-manager** - required agent
- [ ] **[IMPLEMENTATION]**
```

## Streaming Output

The orchestrator displays real-time output from Claude sessions:

```
[Read: phase1-setup.md]
[TodoWrite: 5 items]
[Write: calculator.py]
[Bash: echo "validation passed"]
[Edit: module.py]
[ERROR: Exit code 1...]
```

## State Persistence

State is stored in `.orchestrator/state.db` (SQLite) relative to your project root.

```bash
# Check current state
orchestrate status

# View history
orchestrate history
```

## Architecture

```
+-------------------------------------------------------------+
|                    Python Orchestrator                       |
|  - Parses master plan and phase files                       |
|  - Manages state in SQLite                                  |
|  - Coordinates phase execution                              |
|  - Verifies compliance after each phase                     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   Claude CLI Sessions                        |
|  - Fresh session per phase (no token limits)                |
|  - --dangerously-skip-permissions for automation            |
|  - --output-format stream-json for real-time output         |
|  - Calls `orchestrate done` when complete                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                  Compliance Checker                          |
|  - Re-runs all gates independently                          |
|  - Verifies required agents were invoked                    |
|  - Checks notes file exists with required sections          |
|  - Determines remediation strategy on failure               |
+-------------------------------------------------------------+
```

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
uv run pyright src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## License

MIT

## Credits

Built with Claude Code by @matt-grain and Anima (Claude).
