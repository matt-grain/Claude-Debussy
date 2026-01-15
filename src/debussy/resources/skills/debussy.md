# Debussy Orchestrator Commands

This skill provides commands for interacting with the Debussy orchestrator during an orchestrated session.

## Overview

When you're running inside a Debussy-orchestrated phase, use these commands to signal progress and completion to the orchestrator.

## Commands

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

## Fallback

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
