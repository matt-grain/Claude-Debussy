# Phase 3: Audit Improvements - Implementation Notes

**Date:** 2026-01-14 (Implementation) / 2026-01-15 (Verification)
**Status:** Completed and Verified

---

## Summary

Successfully implemented all audit improvements as specified in the phase plan:

1. **Verbose Mode (`--verbose` / `-v`)**: Added support for multiple verbosity levels
   - `-v` (level 1): Shows suggestions for each issue
   - `-vv` (level 2): Shows parsed plan structure including gates, dependencies, and notes output paths

2. **Fix Suggestions**: Added contextual suggestions for all error types
   - `MASTER_NOT_FOUND`: "Create a master plan file with a '## Phases' table..."
   - `MASTER_PARSE_ERROR`: "Check the master plan format..."
   - `PHASE_NOT_FOUND`: "Create the phase file at '...' or update the master plan..."
   - `MISSING_GATES`: "Add a '## Gates' section with validation commands..."
   - `NO_NOTES_OUTPUT`: "Add '- [ ] Write notes to: ...' to the Process Wrapper section"
   - `MISSING_DEPENDENCY`: "Either add phase X to the master plan, or remove the dependency..."
   - `CIRCULAR_DEPENDENCY`: "Remove/Break the cycle by removing one of the dependencies..."

3. **JSON Output (`--format json`)**: Added machine-readable JSON output for CI integration
   - Includes `passed`, `summary`, and `issues` fields
   - Issues include `severity`, `code`, `message`, `location`, and `suggestion`

---

## Files Modified

| File | Changes |
|------|---------|
| `src/debussy/core/audit.py` | Added `suggestion` field to `AuditIssue` model |
| `src/debussy/core/auditor.py` | Added suggestions for all issue types |
| `src/debussy/cli.py` | Added `--verbose`/`-v` and `--format`/`-f` options, `_display_issue()` and `_display_audit_structure()` helper functions |
| `tests/test_audit.py` | Added `TestAuditSuggestions` class (6 tests) and `TestAuditCLI` class (6 tests) |

---

## Technical Decisions

### 1. Type Checker Conflict Resolution
The file `src/debussy/notifications/desktop.py` had a known conflict between `ty` and `pyright` type checkers (documented in LOG_INSIGHTS.md). Fixed by changing `type: ignore[misc]` to `pyright: ignore[reportOptionalCall]` which satisfies both checkers.

### 2. JSON Output Implementation
Used `print()` directly instead of Rich's `console.print()` for JSON output to avoid markup processing issues with special characters in suggestion strings (like newlines).

### 3. Suggestion Formatting
Multi-line suggestions are supported and properly indented in text output mode. In JSON mode, they are preserved as-is with `\n` escape sequences.

---

## Test Coverage

- **New tests added:** 12 tests across 2 new test classes
- **All tests pass:** 325 tests total
- **Coverage:** 59.28% (exceeds 50% requirement)

### New Test Classes:
- `TestAuditSuggestions`: Tests for suggestion field and content
- `TestAuditCLI`: Tests for verbose output, JSON format, and CLI behavior

---

## Gates Verified

All gates pass:
- `uv run ruff check .` - 0 errors
- `uv run pyright src/debussy/` - 0 errors
- `uv run ty check src/debussy/` - 0 errors
- `uv run pytest tests/ -v` - 325 passed

---

## Example Usage

```bash
# Default output (backwards compatible)
debussy audit plan.md

# With suggestions shown
debussy audit -v plan.md

# With full structure
debussy audit -vv plan.md

# JSON output for CI
debussy audit --format json plan.md
```

---

## Verification Pass (2026-01-15)

Re-ran all validation gates to confirm phase completion:

| Gate | Command | Result |
|------|---------|--------|
| ruff format | `uv run ruff format .` | 47 files unchanged |
| ruff check | `uv run ruff check --fix .` | All checks passed |
| pyright | `uv run pyright src/debussy/` | 0 errors, 0 warnings |
| ty check | `uv run ty check src/debussy/` | All checks passed |
| pytest | `uv run pytest tests/ -x -v` | 325 passed in 21.72s |

Coverage: 59.28% (exceeds 50% requirement)
