"""Unit tests for plan audit functionality."""

from __future__ import annotations

from pathlib import Path

from debussy.core.audit import AuditSeverity
from debussy.core.auditor import PlanAuditor


class TestPlanAuditor:
    """Tests for PlanAuditor class."""

    def test_audit_valid_plan(self, fixtures_dir: Path) -> None:
        """Test that a valid plan passes audit."""
        plan_path = fixtures_dir / "audit" / "valid_plan" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert result.passed
        assert result.summary.errors == 0
        assert result.summary.phases_found == 2
        assert result.summary.phases_valid == 2
        assert result.summary.gates_total == 5  # 3 gates in phase-1, 2 in phase-2

    def test_audit_missing_master_plan(self, temp_dir: Path) -> None:
        """Test that missing master plan returns error."""
        plan_path = temp_dir / "nonexistent.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert not result.passed
        assert result.summary.errors == 1
        assert any(i.code == "MASTER_NOT_FOUND" for i in result.issues)

    def test_audit_missing_gates(self, fixtures_dir: Path) -> None:
        """Test that phase without gates returns error."""
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert not result.passed
        assert result.summary.errors >= 1
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "MISSING_GATES" for i in errors)

    def test_audit_missing_phase_file(self, fixtures_dir: Path) -> None:
        """Test that missing phase file returns error."""
        plan_path = fixtures_dir / "audit" / "missing_phase" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert not result.passed
        assert result.summary.errors >= 1
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "PHASE_NOT_FOUND" for i in errors)

    def test_audit_circular_dependencies(self, fixtures_dir: Path) -> None:
        """Test that circular dependencies return error."""
        plan_path = fixtures_dir / "audit" / "circular_deps" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert not result.passed
        assert result.summary.errors >= 1
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "CIRCULAR_DEPENDENCY" for i in errors)

    def test_audit_missing_notes_output_warning(self, temp_dir: Path) -> None:
        """Test that missing notes output path returns warning."""
        # Create a plan with a phase that has no notes output
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass (warnings don't fail audit)
        assert result.passed
        # Should have warning about missing notes output
        warnings = [i for i in result.issues if i.severity == AuditSeverity.WARNING]
        assert any(i.code == "NO_NOTES_OUTPUT" for i in warnings)

    def test_audit_empty_phases_table(self, temp_dir: Path) -> None:
        """Test that master plan with no phases returns error."""
        master_content = """\
# Empty Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        assert not result.passed
        assert result.summary.errors >= 1
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "NO_PHASES" for i in errors)

    def test_audit_missing_dependency_warning(self, temp_dir: Path) -> None:
        """Test that dependency on non-existent phase returns warning."""
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Phase depends on phase "99" which doesn't exist
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending
**Depends On:** [Phase 99](phase-99.md)

## Process Wrapper (MANDATORY)
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass (missing dependency is a warning, not error)
        assert result.passed
        warnings = [i for i in result.issues if i.severity == AuditSeverity.WARNING]
        assert any(i.code == "MISSING_DEPENDENCY" for i in warnings)

    def test_audit_self_dependency(self, temp_dir: Path) -> None:
        """Test that phase depending on itself returns error."""
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Phase depends on itself
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending
**Depends On:** [Phase 1](phase-1.md)

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        assert not result.passed
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "CIRCULAR_DEPENDENCY" for i in errors)

    def test_audit_summary_counts(self, fixtures_dir: Path) -> None:
        """Test that audit summary counts are accurate."""
        plan_path = fixtures_dir / "audit" / "valid_plan" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        assert result.summary.master_plan == "Valid Test Plan"
        assert result.summary.phases_found == 2
        assert result.summary.phases_valid == 2
        assert result.summary.gates_total == 5

    def test_audit_phase_parse_error(self, temp_dir: Path) -> None:
        """Test that malformed phase file returns error."""
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create a phase file that exists but will cause parse issues
        # (though our parser is quite forgiving, so this mainly tests the try/except)
        phase_content = "Not a valid phase file"
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # The phase file exists, so PHASE_NOT_FOUND won't trigger
        # But it has no gates, so MISSING_GATES will trigger
        assert not result.passed
        errors = [i for i in result.issues if i.severity == AuditSeverity.ERROR]
        assert any(i.code == "MISSING_GATES" for i in errors)


class TestAuditSuggestions:
    """Tests for audit suggestion functionality."""

    def test_audit_issue_has_suggestion_field(self) -> None:
        """Test that AuditIssue model has suggestion field."""
        from debussy.core.audit import AuditIssue, AuditSeverity

        issue = AuditIssue(
            severity=AuditSeverity.ERROR,
            code="TEST_CODE",
            message="Test message",
            suggestion="Test suggestion",
        )
        assert issue.suggestion == "Test suggestion"

    def test_audit_issue_suggestion_optional(self) -> None:
        """Test that suggestion field is optional."""
        from debussy.core.audit import AuditIssue, AuditSeverity

        issue = AuditIssue(
            severity=AuditSeverity.ERROR,
            code="TEST_CODE",
            message="Test message",
        )
        assert issue.suggestion is None

    def test_missing_gates_has_suggestion(self, fixtures_dir: Path) -> None:
        """Test that MISSING_GATES error includes suggestion."""
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        missing_gates_issues = [i for i in result.issues if i.code == "MISSING_GATES"]
        assert len(missing_gates_issues) > 0
        assert missing_gates_issues[0].suggestion is not None
        assert "## Gates" in missing_gates_issues[0].suggestion

    def test_missing_phase_has_suggestion(self, fixtures_dir: Path) -> None:
        """Test that PHASE_NOT_FOUND error includes suggestion."""
        plan_path = fixtures_dir / "audit" / "missing_phase" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        phase_not_found = [i for i in result.issues if i.code == "PHASE_NOT_FOUND"]
        assert len(phase_not_found) > 0
        assert phase_not_found[0].suggestion is not None
        assert "Create" in phase_not_found[0].suggestion or "update" in phase_not_found[0].suggestion

    def test_circular_dependency_has_suggestion(self, fixtures_dir: Path) -> None:
        """Test that CIRCULAR_DEPENDENCY error includes suggestion."""
        plan_path = fixtures_dir / "audit" / "circular_deps" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        circular_deps = [i for i in result.issues if i.code == "CIRCULAR_DEPENDENCY"]
        assert len(circular_deps) > 0
        assert circular_deps[0].suggestion is not None

    def test_no_notes_output_has_suggestion(self, temp_dir: Path) -> None:
        """Test that NO_NOTES_OUTPUT warning includes suggestion."""
        # Create a plan with a phase that has no notes output
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        no_notes = [i for i in result.issues if i.code == "NO_NOTES_OUTPUT"]
        assert len(no_notes) > 0
        assert no_notes[0].suggestion is not None
        assert "notes" in no_notes[0].suggestion.lower()


class TestAuditIntegration:
    """Integration tests for audit functionality."""

    def test_audit_with_sample_fixtures(self, sample_master_plan: Path) -> None:
        """Test audit with existing sample fixtures.

        Note: The sample_master.md references phase files that don't exist,
        so the audit correctly reports errors. This tests that the auditor
        handles real-world incomplete fixtures gracefully.
        """
        auditor = PlanAuditor()
        result = auditor.audit(sample_master_plan)

        # The sample master plan references non-existent phase files,
        # so we expect PHASE_NOT_FOUND errors
        assert not result.passed
        assert result.summary.errors > 0
        assert any(i.code == "PHASE_NOT_FOUND" for i in result.issues)

    def test_audit_result_structure(self, fixtures_dir: Path) -> None:
        """Test that audit result has proper structure."""
        plan_path = fixtures_dir / "audit" / "valid_plan" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        # Check result structure
        assert hasattr(result, "passed")
        assert hasattr(result, "issues")
        assert hasattr(result, "summary")
        assert isinstance(result.passed, bool)
        assert isinstance(result.issues, list)

        # Check summary structure
        assert hasattr(result.summary, "master_plan")
        assert hasattr(result.summary, "phases_found")
        assert hasattr(result.summary, "phases_valid")
        assert hasattr(result.summary, "gates_total")
        assert hasattr(result.summary, "errors")
        assert hasattr(result.summary, "warnings")

    def test_audit_issue_structure(self, fixtures_dir: Path) -> None:
        """Test that audit issues have proper structure."""
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"
        auditor = PlanAuditor()

        result = auditor.audit(plan_path)

        # Should have at least one issue
        assert len(result.issues) > 0

        for issue in result.issues:
            assert hasattr(issue, "severity")
            assert hasattr(issue, "code")
            assert hasattr(issue, "message")
            assert hasattr(issue, "location")
            assert hasattr(issue, "suggestion")
            assert isinstance(issue.code, str)
            assert isinstance(issue.message, str)


class TestAuditCLI:
    """Tests for audit CLI output formats."""

    def test_audit_json_output_structure(self, fixtures_dir: Path) -> None:
        """Test that JSON output has correct structure."""
        import json

        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "valid_plan" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path), "--format", "json"])

        # Should exit successfully for valid plan
        assert result.exit_code == 0

        # Parse JSON output
        output = json.loads(result.stdout)

        # Check structure
        assert "passed" in output
        assert "summary" in output
        assert "issues" in output
        assert isinstance(output["passed"], bool)
        assert isinstance(output["summary"], dict)
        assert isinstance(output["issues"], list)

        # Check summary fields
        assert "master_plan" in output["summary"]
        assert "phases_found" in output["summary"]
        assert "phases_valid" in output["summary"]
        assert "gates_total" in output["summary"]
        assert "errors" in output["summary"]
        assert "warnings" in output["summary"]

    def test_audit_json_output_with_errors(self, fixtures_dir: Path) -> None:
        """Test JSON output when audit fails."""
        import json

        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path), "--format", "json"])

        # Should exit with error
        assert result.exit_code == 1

        # Parse JSON output
        output = json.loads(result.stdout)

        assert output["passed"] is False
        assert output["summary"]["errors"] > 0
        assert len(output["issues"]) > 0

        # Check issue structure
        for issue in output["issues"]:
            assert "severity" in issue
            assert "code" in issue
            assert "message" in issue
            assert "location" in issue
            assert "suggestion" in issue

    def test_audit_json_includes_suggestions(self, fixtures_dir: Path) -> None:
        """Test that JSON output includes suggestions."""
        import json

        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path), "--format", "json"])

        output = json.loads(result.stdout)

        # Find the MISSING_GATES issue
        missing_gates = [i for i in output["issues"] if i["code"] == "MISSING_GATES"]
        assert len(missing_gates) > 0
        assert missing_gates[0]["suggestion"] is not None

    def test_audit_verbose_shows_suggestions(self, fixtures_dir: Path) -> None:
        """Test that verbose mode shows suggestions."""
        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path), "-v"])

        # Should show suggestions
        assert "Suggestion:" in result.stdout

    def test_audit_verbose_v2_shows_structure(self, fixtures_dir: Path) -> None:
        """Test that -vv shows parsed structure."""
        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "valid_plan" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path), "-vv"])

        # Should show parsed structure
        assert "Parsed Structure:" in result.stdout
        assert "Gates:" in result.stdout

    def test_audit_default_no_suggestions(self, fixtures_dir: Path) -> None:
        """Test that default output (no -v) doesn't show suggestions."""
        from typer.testing import CliRunner

        from debussy.cli import app

        runner = CliRunner()
        plan_path = fixtures_dir / "audit" / "missing_gates" / "MASTER_PLAN.md"

        result = runner.invoke(app, ["audit", str(plan_path)])

        # Should not show suggestions in default mode
        assert "Suggestion:" not in result.stdout
        # But should still show the error
        assert "no gates defined" in result.stdout
