# Phase 2: Templates & Init Command

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** [Phase 1](phase-1-audit.md) (audit command must exist to validate output)

---

## CRITICAL: Read These First

Before implementing ANYTHING, read these files:

1. **Existing templates**: `docs/templates/plans/MASTER_TEMPLATE.md` and `PHASE_BACKEND.md`
2. **Phase 3.1 implementation**: Review what was created in Phase 3.1
3. **CLI patterns**: `src/debussy/cli.py`
4. **Notes previous phase**: `notes/NOTES_phase3_templates_phase_1.md`

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_phase3_templates_phase_1.md`
- [ ] Read existing templates in `docs/templates/`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Code quality - run from project root
  uv run ruff format . && uv run ruff check --fix .

  # Type checking
  uv run pyright src/debussy/
  uv run ty check src/debussy/

  # Code metrics and security
  uv run radon mi src/debussy/ -s
  uv run bandit -r src/debussy/ -ll

  # Tests - ALL tests must pass
  uv run pytest tests/ -x -v

  # IMPORTANT: Test that init output passes audit
  uv run debussy init test-feature --output /tmp/test-init --phases 2
  uv run debussy audit /tmp/test-init/MASTER_PLAN.md
  ```
- [ ] Fix loop: repeat pre-validation until ALL pass
- [ ] Write `notes/NOTES_phase3_templates_phase_2.md`
- [ ] Signal completion: `debussy done --phase 2`

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- ruff: 0 errors (command: `uv run ruff check .`)
- pyright: 0 errors (command: `uv run pyright src/debussy/`)
- ty: 0 errors (command: `uv run ty check src/debussy/`)
- radon: maintainability A or B, no C/D/F (command: `uv run radon mi src/debussy/ -s`)
- bandit: 0 high severity issues (command: `uv run bandit -r src/debussy/ -ll`)
- tests: ALL tests pass (command: `uv run pytest tests/ -v`)
- init_audit: init output passes audit (command: `uv run debussy init test && uv run debussy audit`)

---

## Overview

Implement `debussy init <feature_name>` command that scaffolds a complete, audit-passing plan structure from templates. This is the primary onboarding path for new users.

## Dependencies
- Previous phase: Phase 1 (audit command)
- External: None

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Templates get out of sync | Low | Medium | Templates are source of truth, validate with audit |
| User confusion about placeholders | Medium | Low | Clear placeholder format, good defaults |

---

## Tasks

### 1. Consolidate Templates

The project already has templates in `docs/templates/`. We need to ensure they're complete and audit-compliant.

- [ ] 1.1: Review existing templates:
  - `docs/templates/plans/MASTER_TEMPLATE.md`
  - `docs/templates/plans/PHASE_BACKEND.md`
  - `docs/templates/plans/PHASE_FRONTEND.md`
  - `docs/templates/notes/NOTES_TEMPLATE.md`

- [ ] 1.2: Create a generic phase template (not backend/frontend specific):
  - File: `docs/templates/plans/PHASE_GENERIC.md`
  - Should pass audit when placeholders are filled
  - Must have: Gates section, Process Wrapper, Tasks section

- [ ] 1.3: Update `MASTER_TEMPLATE.md` if needed to pass audit:
  - Must have phases table with correct format
  - Links must use consistent naming pattern

- [ ] 1.4: Verify templates pass audit when filled in:
  ```bash
  # Manual test: copy template, fill placeholders, run audit
  ```

### 2. Create Init Module

- [ ] 2.1: Create `src/debussy/templates/__init__.py`:
  ```python
  """Template management for debussy init."""
  from pathlib import Path

  TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "templates"
  ```

- [ ] 2.2: Create `src/debussy/templates/scaffolder.py`:
  ```python
  from pathlib import Path
  from string import Template

  class PlanScaffolder:
      """Scaffold new plans from templates."""

      def __init__(self, templates_dir: Path):
          self.templates_dir = templates_dir

      def scaffold(
          self,
          feature_name: str,
          output_dir: Path,
          num_phases: int = 3,
          template_type: str = "generic",
      ) -> list[Path]:
          """Generate plan files from templates.

          Args:
              feature_name: Name of the feature (used in filenames and content)
              output_dir: Directory to write generated files
              num_phases: Number of phase files to generate
              template_type: "generic", "backend", or "frontend"

          Returns:
              List of created file paths.
          """

      def _load_template(self, name: str) -> str:
          """Load template content from file."""

      def _substitute(self, template: str, variables: dict[str, str]) -> str:
          """Replace placeholders in template."""
  ```

### 3. Template Variable System

- [ ] 3.1: Define placeholder format (use `{variable}` style):
  - `{feature}` - Feature name (e.g., "user-auth")
  - `{feature_slug}` - Filename-safe version (e.g., "user_auth")
  - `{phase_num}` - Phase number (1, 2, 3...)
  - `{date}` - Current date (YYYY-MM-DD)
  - `{prev_phase}` - Previous phase number or "N/A"
  - `{next_phase}` - Next phase number or "N/A"

- [ ] 3.2: Update templates to use consistent placeholders:
  ```markdown
  # {feature} Phase {phase_num}: {phase_title}

  **Status:** Pending
  **Master Plan:** [{feature}-master.md]({feature}-master.md)
  **Depends On:** {prev_phase_link}
  ```

### 4. Add CLI Command

- [ ] 4.1: Add `init` command to `src/debussy/cli.py`:
  ```python
  @app.command()
  def init(
      feature: Annotated[str, typer.Argument(help="Feature name for the plan")],
      output: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = None,
      phases: Annotated[int, typer.Option("--phases", "-p", help="Number of phases")] = 3,
      template: Annotated[str, typer.Option("--template", "-t", help="Template type")] = "generic",
      force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing")] = False,
  ):
      """Initialize a new plan from templates.

      Example:
          debussy init user-auth --phases 3
          debussy init api-refactor --output plans/api/ --template backend
      """
  ```

- [ ] 4.2: Implement command logic:
  1. Determine output directory (default: `./plans/{feature}/`)
  2. Check if directory exists (fail unless `--force`)
  3. Call scaffolder to generate files
  4. Run audit on generated files
  5. Print success message with next steps

- [ ] 4.3: Rich output for init:
  ```
  debussy init user-auth --phases 3

  Creating plan: user-auth

  ✓ Created: plans/user-auth/MASTER_PLAN.md
  ✓ Created: plans/user-auth/phase-1.md
  ✓ Created: plans/user-auth/phase-2.md
  ✓ Created: plans/user-auth/phase-3.md

  Running audit...
  ✓ Plan passes audit

  Next steps:
  1. Edit plans/user-auth/MASTER_PLAN.md to fill in overview and goals
  2. Edit each phase file to add specific tasks
  3. Run: debussy run plans/user-auth/MASTER_PLAN.md
  ```

### 5. Write Tests

- [ ] 5.1: Create `tests/test_init.py`:
  ```python
  def test_scaffold_creates_files(tmp_path):
      """Init creates master plan and phase files."""

  def test_scaffold_output_passes_audit(tmp_path):
      """Generated files pass audit."""

  def test_scaffold_respects_phase_count(tmp_path):
      """--phases flag controls number of phase files."""

  def test_scaffold_fails_if_exists(tmp_path):
      """Init fails if output dir exists without --force."""

  def test_scaffold_force_overwrites(tmp_path):
      """--force allows overwriting existing files."""
  ```

- [ ] 5.2: Test CLI integration:
  ```python
  from typer.testing import CliRunner
  from debussy.cli import app

  def test_init_cli_command(tmp_path):
      runner = CliRunner()
      result = runner.invoke(app, ["init", "test-feature", "-o", str(tmp_path)])
      assert result.exit_code == 0
  ```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `docs/templates/plans/PHASE_GENERIC.md` | Create | Generic phase template |
| `docs/templates/plans/MASTER_TEMPLATE.md` | Modify | Ensure audit-compliant |
| `src/debussy/templates/__init__.py` | Create | Template module |
| `src/debussy/templates/scaffolder.py` | Create | Scaffolding logic |
| `src/debussy/cli.py` | Modify | Add `init` command |
| `tests/test_init.py` | Create | Init command tests |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| String templating | Python `string.Template` or f-strings | Variable substitution |
| CLI commands | `src/debussy/cli.py` existing commands | Typer patterns |
| File I/O | `src/debussy/parsers/` | Path handling |

### Template Loading Pattern

```python
from importlib import resources

# Option 1: Relative to package
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Option 2: Use importlib.resources (better for packaging)
with resources.files("debussy").joinpath("templates").as_file() as templates:
    ...
```

### Variable Substitution

```python
from string import Template

# Use $variable or ${variable} syntax
template = Template("""
# $feature - Master Plan

## Phases
| Phase | Title |
|-------|-------|
| 1 | [$feature Phase 1](${feature_slug}-phase-1.md) |
""")

content = template.safe_substitute(
    feature="User Auth",
    feature_slug="user-auth",
)
```

## Test Strategy

- [ ] Unit tests for `PlanScaffolder`
- [ ] Integration tests for CLI `init` command
- [ ] **Critical**: Test that init output passes audit
- [ ] Test various phase counts (1, 3, 5)
- [ ] Test force overwrite behavior

## Acceptance Criteria

**ALL must pass:**

- [ ] `debussy init feature-name` creates plan directory with files
- [ ] Generated master plan has correct structure
- [ ] Generated phase files have correct structure
- [ ] **Generated files pass `debussy audit`** (critical!)
- [ ] `--phases N` controls number of phase files
- [ ] `--template` supports generic, backend, frontend
- [ ] `--force` allows overwriting existing
- [ ] Tests exist and pass
- [ ] All linting passes

## Rollback Plan
- Init is additive, creates new files only
- `--force` required to overwrite, so no accidental data loss
- If templates are wrong, fix templates and re-run init
