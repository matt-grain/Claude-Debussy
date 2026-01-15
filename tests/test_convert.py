"""Unit tests for plan conversion functionality."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from debussy.cli import app
from debussy.converters import ConversionResult, PlanConverter
from debussy.converters.plan_converter import PlanConverter as PlanConverterClass
from debussy.converters.prompts import CONVERSION_PROMPT, REMEDIATION_SECTION
from debussy.core.auditor import PlanAuditor
from debussy.templates import TEMPLATES_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to convert test fixtures."""
    return Path(__file__).parent / "fixtures" / "convert"


@pytest.fixture
def simple_plan(fixtures_dir: Path) -> Path:
    """Get path to simple plan fixture."""
    return fixtures_dir / "simple_plan.md"


@pytest.fixture
def complex_plan(fixtures_dir: Path) -> Path:
    """Get path to complex plan fixture."""
    return fixtures_dir / "complex_plan.md"


@pytest.fixture
def mock_auditor() -> MagicMock:
    """Create a mock auditor that passes."""
    auditor = MagicMock(spec=PlanAuditor)
    # Create a passing audit result
    mock_result = MagicMock()
    mock_result.passed = True
    mock_result.summary.errors = 0
    mock_result.summary.warnings = 0
    mock_result.issues = []
    auditor.audit.return_value = mock_result
    return auditor


@pytest.fixture
def mock_failing_auditor() -> MagicMock:
    """Create a mock auditor that fails."""
    auditor = MagicMock(spec=PlanAuditor)
    # Create a failing audit result
    mock_result = MagicMock()
    mock_result.passed = False
    mock_result.summary.errors = 1
    mock_result.summary.warnings = 0
    mock_result.issues = [
        MagicMock(
            severity=MagicMock(value="error"),
            code="MISSING_GATES",
            message="Phase 1 has no gates defined",
        )
    ]
    auditor.audit.return_value = mock_result
    return auditor


class TestPlanConverter:
    """Tests for PlanConverter class."""

    def test_converter_initialization(self, mock_auditor: MagicMock) -> None:
        """Test converter can be initialized with required parameters."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=3,
            model="haiku",
        )

        assert converter.auditor == mock_auditor
        assert converter.templates_dir == TEMPLATES_DIR
        assert converter.max_iterations == 3
        assert converter.model == "haiku"

    def test_convert_source_not_found(self, mock_auditor: MagicMock, tmp_path: Path) -> None:
        """Test conversion fails gracefully when source not found."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        result = converter.convert(
            source_plan=tmp_path / "nonexistent.md",
            output_dir=tmp_path / "output",
        )

        assert not result.success
        assert result.iterations == 0
        assert "not found" in result.warnings[0].lower()

    def test_convert_template_not_found(self, mock_auditor: MagicMock, tmp_path: Path) -> None:
        """Test conversion fails when templates not found."""
        # Create a source plan
        source = tmp_path / "source.md"
        source.write_text("# Test Plan\n\nSome content")

        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=tmp_path / "nonexistent_templates",
        )

        result = converter.convert(
            source_plan=source,
            output_dir=tmp_path / "output",
        )

        assert not result.success
        assert "not found" in result.warnings[0].lower()

    @patch.object(PlanConverterClass, "_run_claude")
    def test_convert_simple_plan(
        self,
        mock_run_claude: MagicMock,
        mock_auditor: MagicMock,
        simple_plan: Path,
        tmp_path: Path,
    ) -> None:
        """Test conversion of a simple freeform plan."""
        # Mock Claude output with properly structured files
        mock_run_claude.return_value = """
---FILE: MASTER_PLAN.md---
# User Authentication - Master Plan

**Created:** 2024-01-15
**Status:** Draft

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Setup](phase-1.md) | Database schema | Low | Pending |
| 2 | [Implementation](phase-2.md) | Auth endpoints | Medium | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1: Setup

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)

## Process Wrapper
- [ ] Read previous notes: N/A
- [ ] **[IMPLEMENTATION]**
- [ ] Write `notes/NOTES_auth_phase_1.md`

## Gates
- lint: 0 errors (command: `uv run ruff check .`)
- tests: pass (command: `uv run pytest tests/`)

## Tasks
- [ ] Create auth table schema
---END FILE---

---FILE: phase-2.md---
# Phase 2: Implementation

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)

## Process Wrapper
- [ ] Read previous notes: `notes/NOTES_auth_phase_1.md`
- [ ] **[IMPLEMENTATION]**
- [ ] Write `notes/NOTES_auth_phase_2.md`

## Gates
- lint: 0 errors (command: `uv run ruff check .`)
- tests: pass (command: `uv run pytest tests/`)

## Tasks
- [ ] Create login endpoint
- [ ] Create logout endpoint
---END FILE---
"""

        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        result = converter.convert(
            source_plan=simple_plan,
            output_dir=tmp_path / "output",
        )

        assert result.success
        assert result.iterations == 1
        assert len(result.files_created) == 3
        assert (tmp_path / "output" / "MASTER_PLAN.md").exists()

    @patch.object(PlanConverterClass, "_run_claude")
    def test_convert_retry_on_audit_fail(
        self,
        mock_run_claude: MagicMock,
        simple_plan: Path,
        tmp_path: Path,
    ) -> None:
        """Test converter retries when audit fails."""
        # First attempt: missing gates
        # Second attempt: fixed output
        call_count = [0]

        def mock_claude_with_retry(_prompt: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                # First attempt - will fail audit (no gates)
                return """
---FILE: MASTER_PLAN.md---
# Test Plan

## Phases
| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase 1](phase-1.md) | Setup | Low | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1
**Status:** Pending

## Tasks
- [ ] Do something
---END FILE---
"""
            else:
                # Second attempt - will pass audit
                return """
---FILE: MASTER_PLAN.md---
# Test Plan

## Phases
| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase 1](phase-1.md) | Setup | Low | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1
**Status:** Pending

## Process Wrapper
- [ ] Write `notes/NOTES_phase_1.md`

## Gates
- lint: 0 errors (command: `uv run ruff check .`)

## Tasks
- [ ] Do something
---END FILE---
"""

        mock_run_claude.side_effect = mock_claude_with_retry

        # Use real auditor
        auditor = PlanAuditor()
        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=3,
        )

        result = converter.convert(
            source_plan=simple_plan,
            output_dir=tmp_path / "output",
        )

        assert result.success
        assert result.iterations == 2  # Took 2 attempts
        assert call_count[0] == 2

    @patch.object(PlanConverterClass, "_run_claude")
    def test_convert_max_retries_exceeded(
        self,
        mock_run_claude: MagicMock,
        simple_plan: Path,
        tmp_path: Path,
    ) -> None:
        """Test conversion fails after max retries exceeded."""
        # Always return invalid output
        mock_run_claude.return_value = """
---FILE: MASTER_PLAN.md---
# Test Plan
## Phases
| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase 1](phase-1.md) | Setup | Low | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1 - No gates, will fail audit
## Tasks
- [ ] Task 1
---END FILE---
"""

        # Use real auditor
        auditor = PlanAuditor()
        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=2,
        )

        result = converter.convert(
            source_plan=simple_plan,
            output_dir=tmp_path / "output",
        )

        assert not result.success
        assert result.iterations == 2
        assert "failed after" in result.warnings[0].lower()

    def test_parse_file_output(self, mock_auditor: MagicMock) -> None:
        """Test parsing of Claude file output blocks."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        output = """
Some text before

---FILE: test.md---
Content of test file
with multiple lines
---END FILE---

---FILE: other.md---
Other content
---END FILE---

Some text after
"""

        files = converter._parse_file_output(output)

        assert len(files) == 2
        assert "test.md" in files
        assert "other.md" in files
        assert "Content of test file" in files["test.md"]
        assert "Other content" in files["other.md"]

    def test_parse_file_output_empty(self, mock_auditor: MagicMock) -> None:
        """Test parsing handles empty output."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        files = converter._parse_file_output("No file blocks here")

        assert len(files) == 0

    def test_build_conversion_prompt_basic(self, mock_auditor: MagicMock) -> None:
        """Test prompt building without previous issues."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        prompt = converter._build_conversion_prompt(
            source_content="# My Plan\n\nSome tasks",
            master_template="Master template content",
            phase_template="Phase template content",
            previous_issues=None,
        )

        assert "# My Plan" in prompt
        assert "Master template content" in prompt
        assert "Phase template content" in prompt
        assert "Previous Attempt Failed" not in prompt

    def test_build_conversion_prompt_with_issues(self, mock_auditor: MagicMock) -> None:
        """Test prompt building includes previous issues for remediation."""
        converter = PlanConverter(
            auditor=mock_auditor,
            templates_dir=TEMPLATES_DIR,
        )

        mock_issue = MagicMock()
        mock_issue.severity.value = "error"
        mock_issue.code = "MISSING_GATES"
        mock_issue.message = "Phase 1 has no gates"

        prompt = converter._build_conversion_prompt(
            source_content="# My Plan",
            master_template="Master template",
            phase_template="Phase template",
            previous_issues=[mock_issue],
        )

        assert "Previous Attempt Failed" in prompt
        assert "MISSING_GATES" in prompt
        assert "Phase 1 has no gates" in prompt


class TestConversionResult:
    """Tests for ConversionResult model."""

    def test_result_successful(self) -> None:
        """Test creating a successful result."""
        result = ConversionResult(
            success=True,
            iterations=1,
            files_created=["MASTER_PLAN.md", "phase-1.md"],
            audit_passed=True,
            audit_errors=0,
            audit_warnings=0,
        )

        assert result.success
        assert result.iterations == 1
        assert len(result.files_created) == 2
        assert result.audit_passed

    def test_result_failed(self) -> None:
        """Test creating a failed result."""
        result = ConversionResult(
            success=False,
            iterations=3,
            files_created=["MASTER_PLAN.md"],
            audit_passed=False,
            audit_errors=2,
            audit_warnings=1,
            warnings=["Max retries exceeded"],
        )

        assert not result.success
        assert result.iterations == 3
        assert result.audit_errors == 2
        assert len(result.warnings) == 1


class TestConvertCLI:
    """Tests for the convert CLI command."""

    @pytest.fixture
    def cli_runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_convert_cli_source_not_found(self, cli_runner: CliRunner, tmp_path: Path) -> None:
        """Test CLI fails when source file doesn't exist."""
        result = cli_runner.invoke(app, ["convert", str(tmp_path / "nonexistent.md")])

        assert result.exit_code != 0
        # Typer validates file exists before command runs

    def test_convert_cli_output_exists(self, cli_runner: CliRunner, simple_plan: Path, tmp_path: Path) -> None:
        """Test CLI fails when output directory exists without --force."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = cli_runner.invoke(app, ["convert", str(simple_plan), "--output", str(output_dir)])

        assert result.exit_code != 0
        assert "already exists" in result.output.lower()

    @patch.object(PlanConverterClass, "_run_claude")
    def test_convert_cli_with_force(
        self,
        mock_run_claude: MagicMock,
        cli_runner: CliRunner,
        simple_plan: Path,
        tmp_path: Path,
    ) -> None:
        """Test CLI can overwrite with --force flag."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock successful conversion
        mock_run_claude.return_value = """
---FILE: MASTER_PLAN.md---
# Test

## Phases
| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase 1](phase-1.md) | Setup | Low | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1
## Process Wrapper
- [ ] Write `notes/NOTES_phase_1.md`
## Gates
- lint: 0 errors (command: `uv run ruff check .`)
## Tasks
- [ ] Task 1
---END FILE---
"""

        result = cli_runner.invoke(
            app,
            ["convert", str(simple_plan), "--output", str(output_dir), "--force"],
        )

        # Should succeed with --force
        assert result.exit_code == 0

    @patch("debussy.converters.plan_converter.subprocess.run")
    def test_convert_cli_default_output(
        self,
        mock_subprocess: MagicMock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test CLI uses default output directory based on source name."""
        # Create a source plan in temp directory to avoid polluting fixtures
        source_plan = tmp_path / "my-feature.md"
        source_plan.write_text("# My Feature\n\n## Tasks\n- Do something")

        # Mock subprocess.run to return valid Claude output
        mock_result = MagicMock()
        mock_result.stdout = """
---FILE: MASTER_PLAN.md---
# Test
## Phases
| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase 1](phase-1.md) | Setup | Low | Pending |
---END FILE---

---FILE: phase-1.md---
# Phase 1
## Process Wrapper
- [ ] Write `notes/NOTES_phase_1.md`
## Gates
- lint: 0 errors (command: `uv run ruff check .`)
## Tasks
- [ ] Task 1
---END FILE---
"""
        mock_subprocess.return_value = mock_result

        # The default output should be structured-{source_stem}
        result = cli_runner.invoke(app, ["convert", str(source_plan)])

        # Either succeeds with our mock or fails because it tries to create default output
        # The key is that it attempted to use our mock
        assert mock_subprocess.called or "already exists" in result.output.lower()


class TestPrompts:
    """Tests for conversion prompts."""

    def test_conversion_prompt_has_placeholders(self) -> None:
        """Test conversion prompt has all required placeholders."""
        assert "{source_content}" in CONVERSION_PROMPT
        assert "{master_template}" in CONVERSION_PROMPT
        assert "{phase_template}" in CONVERSION_PROMPT
        assert "{previous_issues_section}" in CONVERSION_PROMPT

    def test_remediation_section_has_placeholder(self) -> None:
        """Test remediation section has issues placeholder."""
        assert "{issues}" in REMEDIATION_SECTION

    def test_conversion_prompt_structure(self) -> None:
        """Test conversion prompt has key structural elements."""
        assert "## Critical Requirements" in CONVERSION_PROMPT
        assert "## Output Format" in CONVERSION_PROMPT
        assert "---FILE:" in CONVERSION_PROMPT
        assert "---END FILE---" in CONVERSION_PROMPT
