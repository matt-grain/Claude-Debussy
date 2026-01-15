# Signal Phase Completion

Signal to the Debussy orchestrator that the current phase is complete.

## Usage

```
/debussy-done <PHASE_ID> [STATUS] [REASON]
```

## Arguments

- `PHASE_ID` (required): The phase ID (e.g., "1", "2", "setup")
- `STATUS` (optional): completed | blocked | failed (default: completed)
- `REASON` (optional): Explanation for blocked/failed status

## Examples

```
/debussy-done 1
/debussy-done 2 completed
/debussy-done 3 blocked "Waiting for API credentials"
```

## Implementation

```bash
uv run debussy done --phase $ARGUMENTS
```

If the above fails, try activating the virtual environment first:
```bash
source .venv/bin/activate && debussy done --phase $ARGUMENTS
```
