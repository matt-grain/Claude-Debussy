# Debussy Orchestrator

Debussy orchestrates multi-phase Claude CLI sessions with compliance verification. Named after Claude Debussy, the composer who orchestrates beautiful music - just like this tool orchestrates your implementation plans.

## Running Debussy

### Basic Usage

```bash
# Run an orchestration plan (interactive TUI with dashboard)
debussy run path/to/MASTER_PLAN.md

# Run with a specific model (default: haiku)
debussy run MASTER_PLAN.md --model opus
debussy run MASTER_PLAN.md -m sonnet
```

### Execution Modes

```bash
# Interactive mode (default) - TUI dashboard with hotkeys
debussy run MASTER_PLAN.md

# YOLO mode - non-interactive for CI/automation (requires --accept-risks)
debussy run MASTER_PLAN.md --no-interactive --accept-risks

# With file logging (logs saved to .debussy/logs/)
debussy run MASTER_PLAN.md --output both

# Output modes: terminal (default), file, both
debussy run MASTER_PLAN.md -o file
```

### Sandbox Mode (Recommended)

Run Claude workers inside Docker containers for isolation:

```bash
# Build sandbox image first (one-time setup)
debussy sandbox-build

# Check sandbox is ready
debussy sandbox-status

# Run with sandbox
debussy run MASTER_PLAN.md --sandbox

# Without sandbox (shows security warning, requires confirmation)
debussy run MASTER_PLAN.md --no-sandbox
```

### Resume & Control

```bash
# Resume previous run (skip completed phases)
debussy run MASTER_PLAN.md --resume

# Start fresh (ignore previous progress)
debussy run MASTER_PLAN.md --restart

# Start from specific phase
debussy run MASTER_PLAN.md --phase 3

# Dry run - validate plan without executing
debussy run MASTER_PLAN.md --dry-run
```

### LTM Learnings

Enable workers to save/recall learnings across runs:

```bash
debussy run MASTER_PLAN.md --learnings
debussy run MASTER_PLAN.md -L
```

## Plan Management

```bash
# Validate plan structure before running
debussy audit path/to/MASTER_PLAN.md
debussy audit MASTER_PLAN.md --verbose
debussy audit MASTER_PLAN.md --format json

# Create new plan from templates
debussy plan-init my-feature --phases 3
debussy plan-init api-refactor --template backend --output plans/api/

# Convert freeform plan to Debussy format
debussy convert my-notes.md --output plans/structured/
```

## Status & History

```bash
# View current run status
debussy status

# View run history
debussy history
```

---

## Worker Commands (During Orchestration)

When you're running inside a Debussy-orchestrated phase, use these commands to signal progress and completion.

### Signal Phase Completion

When you've completed all tasks for the current phase:

```
/debussy-done <PHASE_ID> [STATUS] [REASON]
```

Examples:
```
/debussy-done 1
/debussy-done 2 completed
/debussy-done 3 blocked "Waiting for API credentials"
```

Status options:
- `completed`: Phase finished successfully (default)
- `blocked`: Phase cannot proceed (external dependency)
- `failed`: Phase failed and needs intervention

### Log Progress

Signal that you're making progress (helps the orchestrator detect stuck sessions):

```
/debussy-progress <PHASE_ID> <STEP_NAME>
```

Examples:
```
/debussy-progress 1 implementation:started
/debussy-progress 1 tests:running
/debussy-progress 1 gates:validating
```

### Check Status

View the current orchestration status:

```
/debussy-status
```

### Fallback CLI Commands

If the slash commands aren't available, use `uv run debussy` directly:

```bash
uv run debussy done --phase 1 --status completed
uv run debussy progress --phase 1 --step "tests:running"
uv run debussy status
```

## Important Notes

1. **Always signal completion** - When you finish a phase's tasks, you MUST call `/debussy-done` to let the orchestrator know. Without this signal, the orchestrator will wait indefinitely.

2. **Check the phase file** - Your tasks are defined in the phase markdown file. Complete all required tasks and pass all gates before signaling completion.

3. **Use progress logging** - For long-running phases, periodically call `/debussy-progress` to show you're not stuck.

4. **Phases marked Completed in plan are skipped** - If a phase has `Status: Completed` in the master plan table, Debussy will skip it automatically.

5. **Logs are saved** - When using `--output both` or `--output file`, human-readable logs (`.log`) and raw JSONL logs (`.jsonl`) are saved to `.debussy/logs/`.
