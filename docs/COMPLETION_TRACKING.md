# Completion Tracking & Re-run Protection

Debussy tracks completed features to prevent accidental regeneration of plans for work that has already been delivered.

## Overview

When a plan execution completes successfully, Debussy records:
- Feature name (from plan title or file path)
- Linked GitHub/Jira issues
- Completion timestamp
- Plan file path

When you run `plan-from-issues`, Debussy checks if any of the requested issues were part of a previously completed feature and prompts for confirmation before proceeding.

## How It Works

### Recording Completions

When `debussy run` completes successfully:

1. Extracts linked issues from the master plan metadata:
   - `**GitHub Issues:** #10, #11, #12`
   - `**Jira Issues:** PROJ-123, PROJ-124`

2. Stores the completion record in `.debussy/state.db`:
   - Feature name
   - Issue references (type + ID)
   - UTC timestamp
   - Plan file path

### Detection on Plan Generation

When `debussy plan-from-issues` runs:

1. Fetches issues from GitHub/Jira
2. Queries completion history for any matching issue IDs
3. If matches found:
   - Shows warning with completion details
   - Distinguishes full vs partial matches
   - Prompts for confirmation (interactive) or aborts (non-interactive)

## Usage

### Normal Flow (No Completions)

```bash
$ debussy plan-from-issues --milestone "v2.0"
Phase 1: Fetching issues...
  ✓ Fetched 5 issues
Phase 2: Analyzing issues...
...
```

### With Completion Warning

```bash
$ debussy plan-from-issues --milestone "v1.0"
Phase 1: Fetching issues...
  ✓ Fetched 3 issues

⚠️  COMPLETION WARNING

Some of these issues were part of previously completed features:

  User Authentication
    Completed: 2026-01-15 14:30
    Plan: auth-feature/MASTER_PLAN.md
    Matching issues: #10, #11

Partial match: 2/3 issues completed.
Some issues are new, but some overlap with completed work.

Continue anyway? [y/N]:
```

### Using --force Flag

Skip the confirmation prompt entirely:

```bash
$ debussy plan-from-issues --milestone "v1.0" --force
Phase 1: Fetching issues...
  ✓ Fetched 3 issues
  ⚠ --force: bypassing 1 completed feature(s)
...
```

Note: Even with `--force`, a warning is logged to `.debussy/debussy.log` for audit purposes.

## Match Types

### Full Match

All requested issues are already part of completed features:

```
Full match: All requested issues are already completed.
Regenerating may duplicate work already done.
```

This typically indicates the user is trying to regenerate the same plan.

### Partial Match

Some issues overlap with completed features, but some are new:

```
Partial match: 2/5 issues completed.
Some issues are new, but some overlap with completed work.
```

This may indicate:
- Extending an existing feature with new issues (valid)
- Accidentally including old issues (may need cleanup)

## Non-Interactive Mode

In CI/CD or scripted environments (`!sys.stdin.isatty()`):

- Completion warnings abort by default
- Use `--force` to proceed anyway

```bash
# CI pipeline example
debussy plan-from-issues --milestone "v2.0" --force
```

## Database Schema

The completion data is stored in `.debussy/state.db`:

```sql
CREATE TABLE completed_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    issues_json TEXT NOT NULL,
    plan_path TEXT NOT NULL
);
```

Where `issues_json` stores references like:
```json
[
  {"type": "github", "id": "10"},
  {"type": "github", "id": "11"},
  {"type": "jira", "id": "PROJ-123"}
]
```

## Rollback

If completion tracking causes issues, you can:

### Drop the table entirely

```bash
sqlite3 .debussy/state.db "DROP TABLE IF EXISTS completed_features;"
```

### Remove specific entries

```bash
# List completions
sqlite3 .debussy/state.db "SELECT id, name, completed_at FROM completed_features;"

# Delete a specific entry
sqlite3 .debussy/state.db "DELETE FROM completed_features WHERE id = 1;"
```

## Limitations

- Only records completions from `debussy run`, not manual execution
- Requires issues to be linked in plan metadata
- Detection is based on issue ID matching only (no semantic analysis)
- No automatic cleanup of old/stale completion records

## Future Improvements

- Config option to disable completion tracking
- Command to list/manage completion records
- TTL-based automatic expiration of old records
- Integration with GitHub/Jira API to check actual issue status
