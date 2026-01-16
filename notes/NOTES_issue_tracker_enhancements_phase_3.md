# Notes: Issue Tracker Enhancements Phase 3

## Summary

This phase adds subagent existence validation to the audit command. Now when running `debussy audit`, the auditor checks that any custom agents referenced in phase files actually exist in `.claude/agents/` before orchestration begins.

## Key Decisions

1. **Built-in Agents List**: Created a `BUILTIN_AGENTS` frozenset in auditor.py containing all Task tool's built-in agents (Bash, Explore, Plan, general-purpose, etc.). These are not flagged as missing.

2. **Three Detection Patterns**: Agent references are detected via:
   - `**AGENT:agent-name**` markers in Process Wrapper
   - `subagent_type: agent-name` (YAML-style)
   - `subagent_type="agent-name"` (JSON-style)

3. **Caching**: Agent directory scan is cached per audit run to avoid repeated file system operations.

4. **Error Message Format**: Missing agents are reported as errors with the expected file path, e.g., "Create the agent file at: .claude/agents/my-agent.md"

## Implementation Details

### Files Modified
- `src/debussy/core/auditor.py` - Added agent validation logic
  - `BUILTIN_AGENTS` constant with Task tool's built-in agents
  - `AGENT_MARKER_PATTERN`, `SUBAGENT_YAML_PATTERN`, `SUBAGENT_JSON_PATTERN` regex patterns
  - `__init__()` now accepts optional `agents_dir` parameter
  - `_extract_agent_references()` extracts agent names from phase content
  - `_get_available_agents()` scans `.claude/agents/` directory
  - `_check_custom_agents()` validates referenced agents exist
  - `get_detected_agents()` returns dict of agents to referencing files (for verbose mode)

### Files Created
- `tests/test_auditor_agents.py` - 36 comprehensive tests covering:
  - Valid custom agents recognized
  - Missing custom agents reported as errors
  - Built-in agents not flagged
  - Plans with no agents pass
  - Error messages include expected file paths
  - Verbose mode lists detected agents
  - Custom agents directory parameter
  - Edge cases (underscores, numbers, duplicates, code blocks, subdirectories)

## Test Results

- 36 new tests added for agent validation
- 1046 total tests passing
- All quality gates pass (ruff, pyright, pytest, bandit)

## Learnings

1. **Windows Path Separators**: Test assertions checking for `.claude/agents` in paths need to handle both Unix (`/`) and Windows (`\`) separators. Fixed by checking for `.claude` and `agents` separately.

2. **Regex Patterns**: Case-insensitive matching (`re.IGNORECASE`) ensures agent names like `My-Agent` match regardless of casing in the phase file.
