# Phase 1: Audit Command

**Status:** Completed
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A (first phase)

---

## CRITICAL: Read These First

Before implementing ANYTHING, read these files to understand project patterns:

1. **Project structure**: `src/debussy/` - all source code lives here
2. **Existing models**: `src/debussy/core/models.py` - Pydantic models pattern
3. **Existing parsers**: `src/debussy/parsers/master.py` and `phase.py` - how we parse markdown
4. **CLI patterns**: `src/debussy/cli.py` - Typer CLI structure with Rich output
5. **Test patterns**: `tests/test_parsers.py` - how we structure tests

**DO NOT** deviate from existing patterns without explicit justification.

---

## Process Wrapper (MANDATORY)
- [ ] Read the files listed in "CRITICAL: Read These First" section
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Code quality - run from project root
  uv run ruff format . && uv run ruff check --fix .

  # Type checking
  uv run pyright src/debussy/

  # Tests - ALL tests must pass, not just new ones
  uv run pytest tests/ -x -v
  ```
- [ ] Fix loop: repeat pre-validation until ALL pass with 0 errors
- [ ] Write `notes/NOTES_phase3_templates_phase_1.md` with:
  - Summary of what was implemented
  - Any design decisions made
  - Issues encountered and how resolved
  - Files created/modified
- [ ] Signal completion: `debussy done --phase 1`

## Gates (must pass before completion)

**ALL gates are BLOCKING. Do not signal completion until ALL pass.**

- ruff: 0 errors (command: `uv run ruff check .`)
- pyright: 0 errors in src/debussy/ (command: `uv run pyright src/debussy/`)
- tests: ALL tests pass (command: `uv run pytest tests/ -v`)
- new_tests: audit tests exist and pass (command: `uv run pytest tests/test_audit.py -v`)

---

## Overview

Implement `debussy audit <plan_path>` command that validates plan structure deterministically (no AI). This provides fast feedback before `debussy run` and serves as the quality gate for the `convert` command.

## Dependencies
- Previous phase: N/A
- External: Existing parsers in `src/debussy/parsers/`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Parser edge cases | Medium | Low | Test with real Grain_API plans |
| Missing validation rules | Low | Medium | Start strict, loosen if needed |

---

## Tasks

### 1. Create Audit Models

- [ ] 1.1: Create `src/debussy/core/audit.py` with models:
  ```python
  class AuditSeverity(str, Enum):
      ERROR = "error"      # Plan cannot run
      WARNING = "warning"  # Plan may have issues
      INFO = "info"        # Suggestions

  class AuditIssue(BaseModel):
      severity: AuditSeverity
      code: str           # e.g., "MISSING_GATES", "PHASE_NOT_FOUND"
      message: str
      location: str | None  # e.g., "phase-1.md:45"

  class AuditResult(BaseModel):
      passed: bool
      issues: list[AuditIssue]
      summary: AuditSummary

  class AuditSummary(BaseModel):
      master_plan: str
      phases_found: int
      phases_valid: int
      gates_total: int
      errors: int
      warnings: int
  ```

### 2. Implement Audit Logic

- [ ] 2.1: Create `src/debussy/core/auditor.py` with `PlanAuditor` class:
  ```python
  class PlanAuditor:
      def audit(self, master_plan_path: Path) -> AuditResult:
          """Run all audit checks on a master plan."""

      def _check_master_plan(self, path: Path) -> list[AuditIssue]:
          """Validate master plan structure."""

      def _check_phase(self, phase: Phase) -> list[AuditIssue]:
          """Validate individual phase file."""

      def _check_gates(self, phase: Phase) -> list[AuditIssue]:
          """Validate phase has gates defined."""

      def _check_notes_paths(self, phase: Phase) -> list[AuditIssue]:
          """Validate notes paths are specified."""

      def _check_dependencies(self, phases: list[Phase]) -> list[AuditIssue]:
          """Validate dependency graph is valid (no cycles, refs exist)."""
  ```

- [ ] 2.2: Implement validation rules:
  - ERROR: Master plan not found
  - ERROR: Master plan has no phases table
  - ERROR: Phase file referenced but not found
  - ERROR: Phase file cannot be parsed
  - ERROR: No gates defined (critical for Debussy's value prop)
  - WARNING: No notes output path specified
  - WARNING: Phase depends on non-existent phase
  - INFO: Phase has no tasks defined (might be intentional)

### 3. Add CLI Command

- [ ] 3.1: Add `audit` command to `src/debussy/cli.py`:
  ```python
  @app.command()
  def audit(
      plan_path: Annotated[Path, typer.Argument(help="Path to master plan")],
      strict: Annotated[bool, typer.Option(help="Fail on warnings too")] = False,
  ):
      """Validate plan structure before running."""
  ```

- [ ] 3.2: Implement Rich output for audit results:
  ```
  debussy audit plans/my-feature/MASTER_PLAN.md

  Auditing: plans/my-feature/MASTER_PLAN.md

  ✓ Master plan parsed: "My Feature"
  ✓ Phase 1: phase-1.md
    ✓ Gates section found (3 gates)
    ✓ Notes output path specified
  ✗ Phase 2: phase-2.md
    ✗ ERROR: Gates section missing
    ⚠ WARNING: No notes output path
  ✓ Phase 3: phase-3.md
    ✓ Gates section found (2 gates)
    ✓ Notes output path specified

  Summary: 1 error, 1 warning
  Result: FAIL

  Run `debussy convert` to fix issues or edit manually.
  ```

### 4. Integrate with `debussy run`

- [ ] 4.1: Add audit as pre-flight check in `debussy run`:
  ```python
  # In debussy.py or cli.py
  def run(master_plan: Path, ...):
      # Pre-flight audit
      auditor = PlanAuditor()
      result = auditor.audit(master_plan)

      if not result.passed:
          console.print("[red]Plan failed audit. Fix issues or use --skip-audit[/red]")
          raise typer.Exit(1)

      # Continue with normal run...
  ```

- [ ] 4.2: Add `--skip-audit` flag for `debussy run` (escape hatch)

### 5. Write Tests

- [ ] 5.1: Create `tests/test_audit.py` with test fixtures:
  - `tests/fixtures/audit/valid_plan/` - Complete, valid plan
  - `tests/fixtures/audit/missing_gates/` - Plan without gates
  - `tests/fixtures/audit/missing_phase/` - Master refs non-existent phase
  - `tests/fixtures/audit/circular_deps/` - Circular dependencies

- [ ] 5.2: Test cases:
  - Valid plan passes audit
  - Missing gates = ERROR
  - Missing phase file = ERROR
  - Missing notes path = WARNING
  - Circular dependencies = ERROR
  - Empty tasks = INFO (not error)

- [ ] 5.3: Test with real Grain_API plan (copy to fixtures):
  - `tests/fixtures/audit/grain_api_sample/` - Real-world example

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/debussy/core/audit.py` | Create | Audit models |
| `src/debussy/core/auditor.py` | Create | Audit logic |
| `src/debussy/cli.py` | Modify | Add `audit` command |
| `src/debussy/core/debussy.py` | Modify | Add pre-flight audit |
| `tests/test_audit.py` | Create | Audit tests |
| `tests/fixtures/audit/` | Create | Test fixtures |

## Patterns to Follow

**MANDATORY: Follow these patterns exactly. Study the reference files before implementing.**

| Pattern | Reference File | What to Copy |
|---------|----------------|--------------|
| Pydantic models | `src/debussy/core/models.py` | Use `from __future__ import annotations`, inherit from `BaseModel`, use type hints |
| Enum pattern | `src/debussy/core/models.py:PhaseStatus` | String enums with `(str, Enum)` |
| Parser functions | `src/debussy/parsers/master.py` | Top-level function, private helpers with `_` prefix |
| CLI commands | `src/debussy/cli.py` | Use `typer.Argument`, `typer.Option`, `Annotated` |
| Rich output | `src/debussy/cli.py` | Use `console = Console()`, `console.print()` with markup |
| Test structure | `tests/test_parsers.py` | Fixtures in `tests/fixtures/`, parametrized tests |

### Code Style Requirements

```python
# DO: Use future annotations
from __future__ import annotations

# DO: Type hints everywhere
def audit(self, path: Path) -> AuditResult:

# DO: Docstrings on public functions
def audit(self, path: Path) -> AuditResult:
    """Run all audit checks on a master plan.

    Args:
        path: Path to the master plan markdown file.

    Returns:
        AuditResult with pass/fail and list of issues.
    """

# DON'T: Use `Any` type unless absolutely necessary
# DON'T: Use print() - use Rich console
# DON'T: Catch broad exceptions without re-raising
```

### File Organization

```
src/debussy/core/
├── __init__.py      # Export new classes here
├── models.py        # Existing models
├── audit.py         # NEW: AuditSeverity, AuditIssue, AuditResult, AuditSummary
└── auditor.py       # NEW: PlanAuditor class

tests/
├── test_audit.py    # NEW: All audit tests
└── fixtures/
    └── audit/       # NEW: Test plan fixtures
        ├── valid_plan/
        │   ├── MASTER_PLAN.md
        │   └── phase-1.md
        ├── missing_gates/
        ├── missing_phase/
        └── grain_api_sample/
```

## Test Strategy

**Tests are NOT optional. Each feature MUST have tests.**

- [ ] Unit tests for `PlanAuditor._check_master_plan()`
- [ ] Unit tests for `PlanAuditor._check_phase()`
- [ ] Unit tests for `PlanAuditor._check_gates()`
- [ ] Unit tests for `PlanAuditor._check_dependencies()`
- [ ] Integration test: valid plan passes
- [ ] Integration test: each error type fails appropriately
- [ ] Fixture: copy Grain_API plan to `tests/fixtures/audit/grain_api_sample/`

## Acceptance Criteria

**ALL criteria must be met before signaling completion:**

- [ ] `debussy audit path/to/plan.md` command works from CLI
- [ ] Valid plans pass with green checkmarks
- [ ] Invalid plans fail with clear, actionable error messages
- [ ] `debussy run` runs audit as pre-flight check
- [ ] `debussy run --skip-audit` bypasses audit
- [ ] `tests/test_audit.py` exists with comprehensive tests
- [ ] All existing tests still pass (`uv run pytest tests/`)
- [ ] `uv run ruff check .` returns 0 errors
- [ ] `uv run pyright src/debussy/` returns 0 errors
- [ ] Grain_API sample plan in fixtures passes audit

## Rollback Plan
- Audit is additive, doesn't change existing behavior
- `--skip-audit` flag allows bypassing if issues found
- If audit breaks `debussy run`, the flag is the escape hatch

---

## Implementation Notes

### Using Existing Parsers

The parsers in `src/debussy/parsers/` already do most of the work. The auditor should:

1. Call `parse_master_plan()` - catches master plan parse errors
2. For each phase, check if file exists before calling `parse_phase()`
3. After parsing, validate the extracted data (gates present, notes paths, etc.)

```python
# Example: reusing existing parser
from debussy.parsers.master import parse_master_plan
from debussy.parsers.phase import parse_phase

class PlanAuditor:
    def audit(self, master_plan_path: Path) -> AuditResult:
        issues = []

        # Use existing parser
        try:
            master = parse_master_plan(master_plan_path)
        except Exception as e:
            issues.append(AuditIssue(
                severity=AuditSeverity.ERROR,
                code="MASTER_PARSE_ERROR",
                message=str(e),
                location=str(master_plan_path),
            ))
            return AuditResult(passed=False, issues=issues, ...)

        # Continue validation...
```

### Rich Output Format

Use Rich markup for colored output:

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# Success
console.print(f"[green]✓[/green] Phase {phase.id}: {phase.path.name}")

# Error
console.print(f"[red]✗[/red] ERROR: {issue.message}")

# Warning
console.print(f"[yellow]⚠[/yellow] WARNING: {issue.message}")
```
