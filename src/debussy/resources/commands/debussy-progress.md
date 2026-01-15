# Log Phase Progress

Signal to the Debussy orchestrator that you're making progress on a phase. This helps detect stuck sessions.

## Usage

```
/debussy-progress <PHASE_ID> <STEP_NAME>
```

## Arguments

- `PHASE_ID` (required): The phase ID (e.g., "1", "2", "setup")
- `STEP_NAME` (required): A descriptive step name (e.g., "implementation:started", "tests:running")

## Examples

```
/debussy-progress 1 implementation:started
/debussy-progress 1 tests:running
/debussy-progress 2 gates:validating
```

## Implementation

```bash
uv run debussy progress --phase $ARGUMENTS
```

If the above fails, try activating the virtual environment first:
```bash
source .venv/bin/activate && debussy progress --phase $ARGUMENTS
```
