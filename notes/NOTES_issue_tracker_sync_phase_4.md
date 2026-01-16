# Phase 4: Bidirectional Sync and State Reconciliation

## Summary

This phase implemented bidirectional synchronization and state reconciliation between Debussy and external issue trackers (GitHub, Jira). The implementation enables users to detect state drift and reconcile differences in either direction.

## What Was Implemented

### 1. Core Models (src/debussy/core/models.py)
Added new Pydantic models for issue sync:
- `IssueStatus` - Current status from external tracker (id, platform, state, labels, milestone)
- `DriftType` - Enum for types of drift (LABEL_MISMATCH, STATUS_MISMATCH, CLOSED_EXTERNALLY, REOPENED_EXTERNALLY)
- `DriftReport` - Report of drift for a single issue
- `SyncDirection` - Enum for sync direction (from-tracker, to-tracker)
- `ReconciliationAction` - A proposed action to fix drift
- `ReconciliationPlan` - Complete plan with actions and drift reports

### 2. Status Fetcher (src/debussy/sync/status_fetcher.py)
New module for fetching issue status with caching:
- `StatusCache` - TTL-based cache (default 5 minutes) to reduce API calls
- `CacheEntry` - Dataclass for cached status with timestamp
- `IssueStatusFetcher` - Async context manager that:
  - Initializes GitHub and Jira clients lazily
  - Caches issue statuses with configurable TTL
  - Fetches from both platforms in parallel
  - Handles API errors gracefully

### 3. Drift Detector (src/debussy/sync/drift_detector.py)
New module for detecting and reconciling state drift:
- `DriftDetector` - Detects drift between Debussy and trackers:
  - Computes expected state based on phase statuses
  - Checks GitHub state/labels for drift
  - Checks Jira status categories for drift
  - Creates reconciliation plans in either direction
- `StateSynchronizer` - Applies reconciliation plans:
  - Supports dry-run mode (default)
  - Executes actions to sync state

### 4. CLI Commands

#### Enhanced `debussy status` command:
```bash
debussy status --issues        # Show linked issue status
debussy status --issues --refresh  # Force refresh from API
debussy status --issues --format json  # JSON output
```

#### New `debussy sync` command:
```bash
debussy sync                              # Show drift and reconciliation plan (dry-run)
debussy sync --apply                      # Execute reconciliation
debussy sync --direction to-tracker       # Push Debussy state to tracker
debussy sync --direction from-tracker     # Update Debussy from tracker (default)
debussy sync --format json                # JSON output
```

### 5. Tests
Created 50 new tests across 3 files:
- `tests/test_status_fetcher.py` - 16 tests for cache and fetcher
- `tests/test_drift_detector.py` - 20 tests for drift detection and reconciliation
- `tests/test_bidirectional_sync.py` - 14 tests for CLI commands and models

## Key Decisions

1. **Cache-First Architecture**: Status fetcher uses TTL cache to minimize API calls. Default 5-minute TTL balances freshness with API rate limits.

2. **Lazy Client Initialization**: GitHub/Jira clients only initialize when credentials are available, allowing partial functionality.

3. **Dual Sync Direction**: Supports both "from-tracker" (conservative, tracker is truth) and "to-tracker" (push Debussy state) modes.

4. **Dry-Run by Default**: Reconciliation shows plan but doesn't execute without `--apply` flag.

5. **Type-Checking Imports**: StateManager import moved to TYPE_CHECKING block per ruff TC001.

## Files Modified

### New Files
- `src/debussy/sync/status_fetcher.py` (170 lines)
- `src/debussy/sync/drift_detector.py` (158 lines)
- `tests/test_status_fetcher.py`
- `tests/test_drift_detector.py`
- `tests/test_bidirectional_sync.py`

### Modified Files
- `src/debussy/core/models.py` - Added 6 new models
- `src/debussy/sync/__init__.py` - Exports new classes
- `src/debussy/cli.py` - Added status --issues flag and sync command

## Test Results

```
913 passed, 2 warnings in 152.81s
Coverage: 67.25%
```

All quality gates pass:
- ruff check: ✓
- ruff format: ✓
- pyright: ✓

## Learnings

1. **Cache Tests Need Mocked Clients**: Tests that use `fetch_github_status` need a mocked GitHub client even when testing cache behavior, because the method checks for client initialization before fetching.

2. **Lazy Import Pattern**: When imports are done inside async functions (like `from debussy.config import Config`), mock patches need to target the module where the import is called, not where the class is defined.

3. **zip() strict= Parameter**: ruff B905 requires explicit `strict=True` on zip() when iterating paired iterables to catch length mismatches.

4. **Exception Chaining**: ruff B904 requires `raise ... from err` in except clauses to preserve exception context.

5. **Ternary Operator Preference**: ruff SIM108 prefers ternary operators over if/else blocks for simple assignments.
