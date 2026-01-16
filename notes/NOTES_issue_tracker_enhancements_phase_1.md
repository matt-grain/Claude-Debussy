# Notes: Issue Tracker Enhancements Phase 1

## Phase Summary

**Phase:** 1 - Add pipe mechanism for plan-from-issues Q&A
**Status:** Completed
**GitHub Issues:** #17
**Date:** 2026-01-16

## Implementation Summary

This phase implemented a JSON-based IPC (Inter-Process Communication) protocol that enables the `plan-from-issues` command to route Q&A gap-filling questions through a parent process (like Claude Code) instead of prompting directly in the terminal.

### Key Changes

1. **New Pydantic Models** (`src/debussy/planners/models.py`):
   - `QAMode` enum: `TERMINAL` (default), `PIPE` (JSON IPC)
   - `QAQuestion`: Structured question with type discriminator, gap_type, question, options, context
   - `QAAnswer`: Structured answer with type discriminator, gap_type, answer

2. **Enhanced QAHandler** (`src/debussy/planners/qa_handler.py`):
   - Environment-based mode detection via `DEBUSSY_QA_PIPE=1`
   - Configurable timeout via `DEBUSSY_QA_TIMEOUT` (default: 30s)
   - `_prompt_terminal()`: Extracted terminal mode logic
   - `_emit_question_json()`: Write JSON questions to stdout
   - `_read_answer_json()`: Read JSON answers from stdin with timeout
   - `_ask_question_pipe()`: Full pipe mode with fallback to terminal on errors
   - New exceptions: `PipeTimeoutError`, `PipeProtocolError`

3. **Test Coverage** (`tests/`):
   - `test_qa_pipe_mode.py`: 22 tests for pipe mode functionality
   - `test_qa_terminal_mode.py`: 24 tests for terminal mode regression

4. **Documentation** (`docs/QA_PIPE_PROTOCOL.md`):
   - Complete protocol specification
   - JSON schema examples
   - Claude Code integration guidance
   - Error handling documentation

### Files Modified/Created

| File | Action | Lines Changed |
|------|--------|---------------|
| `src/debussy/planners/models.py` | Modified | +50 (new models) |
| `src/debussy/planners/qa_handler.py` | Modified | Significant refactor |
| `tests/test_qa_pipe_mode.py` | Created | ~580 lines |
| `tests/test_qa_terminal_mode.py` | Created | ~450 lines |
| `docs/QA_PIPE_PROTOCOL.md` | Created | ~200 lines |

## Validation Results

### Gate Results

| Gate | Status | Notes |
|------|--------|-------|
| ruff format | PASS | All files formatted |
| ruff check | PASS | No linting errors |
| pyright | PASS | 0 errors, 0 warnings |
| pytest | PASS | 978 tests passed, 67.85% coverage |
| bandit | PASS | No high severity issues (only pre-existing low severity) |

### Test Results

- All 978 tests pass
- Coverage maintained at 67.85% (above 60% threshold)
- New pipe mode tests: 22 tests
- New terminal mode regression tests: 24 tests

## Technical Decisions

1. **Explicit opt-in via environment variable**: Chose `DEBUSSY_QA_PIPE=1` over implicit detection to ensure backward compatibility and predictable behavior.

2. **JSON over plain text IPC**: Used Pydantic models for type safety and validation. The `type` discriminator field enables future message types.

3. **Fallback to terminal on errors**: Pipe mode gracefully degrades to terminal prompts if JSON parsing fails or timeouts occur.

4. **Stdout/stderr separation**: Questions go to stdout (machine-readable), logs go to stderr (human-readable) in pipe mode.

5. **Unix select() for timeout**: Used `select.select()` for non-blocking stdin reads with timeout. Falls back on Windows where select doesn't work on stdin.

## Learnings

1. **Environment variable fixtures in pytest**: Renamed fixture to `_clean_env` (underscore prefix) to indicate it's used for side effects only, avoiding ruff ARG002 warnings.

2. **Pydantic Literal fields for discriminators**: Using `Literal["question"]` as a field type provides automatic validation of the message type discriminator.

3. **Context managers for mock chaining**: Combined multiple `patch` calls using Python 3.10+ parenthesized context managers for cleaner test code.

4. **Exception chaining with `from`**: Used `raise ... from e` to preserve exception chains per B904 lint rule.

## Integration Notes for Claude Code

When Claude Code spawns `plan-from-issues`, it should:

1. Set `DEBUSSY_QA_PIPE=1` in the subprocess environment
2. Capture stdout and parse JSON lines
3. For each question, use `AskUserQuestion` tool
4. Write JSON answer to subprocess stdin
5. Repeat until all questions answered

Example question on stdout:
```json
{"type":"question","gap_type":"tech_stack","question":"Which database?","options":[],"context":"No DB mentioned"}
```

Example answer on stdin:
```json
{"type":"answer","gap_type":"tech_stack","answer":"PostgreSQL"}
```

## Rollback Instructions

If issues are found:
1. Unset `DEBUSSY_QA_PIPE` environment variable (terminal mode works as before)
2. Or revert the commit containing these changes

No database migrations or state changes - rollback is clean.

## Next Phase

Phase 2 should integrate this pipe mechanism into the actual Claude Code workflow, testing the full round-trip from Claude Code's perspective.
