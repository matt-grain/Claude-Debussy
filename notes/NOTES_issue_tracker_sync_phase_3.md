# Phase 3: Feature Completion Tracking & Re-run Protection

## Summary

Implemented a feature completion tracking system that records completed features with their linked issues, and warns users when they attempt to regenerate plans for already-completed work.

## Tasks Completed

### Task 1: Database Schema Extension
- Added `completed_features` table to `state.py` SCHEMA
- Columns: `id`, `name`, `completed_at`, `issues_json`, `plan_path`
- `issues_json` stores array of `{type: "github"|"jira", id: string}` objects

### Task 2: Completion Recording Integration
- Added `_record_feature_completion()` method to `Orchestrator` class
- Called after successful run completion (`RunStatus.COMPLETED`)
- Extracts issues from plan metadata (supports both list and string formats)
- Handles both GitHub (`#10, #11`) and Jira (`PROJ-123`) issue formats
- Logs feature recording to TUI

### Task 3: Detection Logic in plan-from-issues
- Added `_check_completed_features()` function
- Builds IssueRef list from fetched GitHub issues
- Queries StateManager for matching completions
- Returns list of CompletedFeature objects

### Task 4: TUI Confirmation (Skipped)
- `plan-from-issues` is a CLI-only command, so TUI modal was not needed
- The CLI confirmation prompt handles both interactive and non-interactive cases

### Task 5: CLI Confirmation Prompt
- Added `_confirm_regeneration()` function
- Shows detailed warning with:
  - Feature names and completion dates
  - Matching issue numbers
  - Full vs partial match classification
- Returns `False` in non-interactive mode (allows `--force` to override)
- Added `--force` flag to CLI command to bypass confirmation

### Task 6: Testing & Edge Cases
- Created `tests/test_completion_tracking.py` with 24 tests:
  - Schema creation and migration
  - Recording with mixed GitHub/Jira issues
  - UTC timestamp storage
  - Finding exact, partial, no overlap matches
  - Cross-platform (GitHub vs Jira) isolation
  - Empty search handling
  - JSON validation
  - Corrupted data graceful handling

- Created `tests/test_plan_from_issues_completion.py` with 10 tests:
  - Detection with no completions
  - Detection with overlapping issues
  - Empty issue set handling
  - User confirmation responses (y/n/Ctrl+C)
  - Non-interactive mode behavior
  - `--force` flag bypass
  - Result field validation

## Files Modified

### Core Implementation
- `src/debussy/core/state.py` - Added `completed_features` table schema and StateManager methods
- `src/debussy/core/models.py` - Added `IssueRef` and `CompletedFeature` Pydantic models
- `src/debussy/core/orchestrator.py` - Added `_record_feature_completion()` method
- `src/debussy/planners/command.py` - Added detection logic and confirmation prompt
- `src/debussy/cli.py` - Added `--force` flag to plan-from-issues command

### Tests
- `tests/test_completion_tracking.py` - New file (24 tests)
- `tests/test_plan_from_issues_completion.py` - New file (10 tests)

### Documentation
- `docs/COMPLETION_TRACKING.md` - Comprehensive documentation

## Key Design Decisions

1. **JSON storage for issues** - Flexible for future issue types, SQLite JSON support varies by version so filtering done in Python

2. **Non-blocking detection** - Completion check failures don't block plan generation, just log warnings

3. **Conservative defaults** - Non-interactive mode rejects by default, requires `--force` to override

4. **UTC timestamps** - Using `datetime.now(UTC)` for consistency across timezones

5. **Graceful corruption handling** - Invalid JSON records are skipped rather than crashing

## Learnings

1. **Test fixture mocking** - When mocking paths like `get_orchestrator_dir`, need to patch at the module where it's CALLED, not where it's defined (lazy imports)

2. **Database path conventions** - The code looks for `state.db` specifically, so tests need to create that filename in the temp directory

3. **datetime.utcnow() deprecated** - Python 3.12+ deprecates `datetime.utcnow()`, use `datetime.now(UTC)` instead

4. **ruff auto-imports UTC** - ruff fixed the UTC import automatically from `datetime.UTC`

## Test Results

- 863 tests passing
- All quality gates pass (ruff, pyright)
- 34 new tests for completion tracking
