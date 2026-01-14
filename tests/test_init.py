"""Unit tests for plan init (scaffolding) functionality."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from debussy.cli import app
from debussy.core.auditor import PlanAuditor
from debussy.templates import TEMPLATES_DIR
from debussy.templates.scaffolder import PlanScaffolder


class TestPlanScaffolder:
    """Tests for PlanScaffolder class."""

    def test_scaffold_creates_files(self, temp_dir: Path) -> None:
        """Test that scaffold creates master plan and phase files."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test-feature"

        created_files = scaffolder.scaffold(
            feature_name="Test Feature",
            output_dir=output_dir,
            num_phases=3,
            template_type="generic",
        )

        # Should create 4 files: 1 master + 3 phases
        assert len(created_files) == 4
        assert (output_dir / "MASTER_PLAN.md").exists()
        assert (output_dir / "test-feature-phase-1.md").exists()
        assert (output_dir / "test-feature-phase-2.md").exists()
        assert (output_dir / "test-feature-phase-3.md").exists()

    def test_scaffold_output_passes_audit(self, temp_dir: Path) -> None:
        """Test that generated files pass audit."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test-feature"

        scaffolder.scaffold(
            feature_name="Test Feature",
            output_dir=output_dir,
            num_phases=2,
            template_type="generic",
        )

        # Run audit on generated master plan
        auditor = PlanAuditor()
        master_plan = output_dir / "MASTER_PLAN.md"
        result = auditor.audit(master_plan)

        # Should pass audit (critical requirement)
        assert result.passed, f"Audit failed: {[i.message for i in result.issues]}"
        assert result.summary.errors == 0

    def test_scaffold_respects_phase_count(self, temp_dir: Path) -> None:
        """Test that --phases flag controls number of phase files."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)

        # Test with 1 phase
        output_dir_1 = temp_dir / "feature-1"
        files_1 = scaffolder.scaffold(
            feature_name="Feature One",
            output_dir=output_dir_1,
            num_phases=1,
            template_type="generic",
        )
        assert len(files_1) == 2  # 1 master + 1 phase

        # Test with 5 phases
        output_dir_5 = temp_dir / "feature-5"
        files_5 = scaffolder.scaffold(
            feature_name="Feature Five",
            output_dir=output_dir_5,
            num_phases=5,
            template_type="generic",
        )
        assert len(files_5) == 6  # 1 master + 5 phases

    def test_scaffold_slugification(self, temp_dir: Path) -> None:
        """Test that feature names are properly slugified."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test"

        scaffolder.scaffold(
            feature_name="User Auth System",
            output_dir=output_dir,
            num_phases=2,
            template_type="generic",
        )

        # Check that slugified names are used in filenames
        assert (output_dir / "user-auth-system-phase-1.md").exists()
        assert (output_dir / "user-auth-system-phase-2.md").exists()

    def test_scaffold_template_types(self, temp_dir: Path) -> None:
        """Test that different template types work."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)

        for template_type in ["generic", "backend", "frontend"]:
            output_dir = temp_dir / f"test-{template_type}"
            created_files = scaffolder.scaffold(
                feature_name="Test",
                output_dir=output_dir,
                num_phases=2,
                template_type=template_type,
            )
            assert len(created_files) == 3  # 1 master + 2 phases

    def test_scaffold_invalid_template_type(self, temp_dir: Path) -> None:
        """Test that invalid template type raises error."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test"

        with pytest.raises(ValueError, match="Unknown template type"):
            scaffolder.scaffold(
                feature_name="Test",
                output_dir=output_dir,
                num_phases=2,
                template_type="invalid",
            )

    def test_scaffold_invalid_phase_count(self, temp_dir: Path) -> None:
        """Test that invalid phase count raises error."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test"

        with pytest.raises(ValueError, match="Number of phases must be at least 1"):
            scaffolder.scaffold(
                feature_name="Test",
                output_dir=output_dir,
                num_phases=0,
                template_type="generic",
            )

    def test_scaffold_content_substitution(self, temp_dir: Path) -> None:
        """Test that placeholders are properly substituted."""
        scaffolder = PlanScaffolder(TEMPLATES_DIR)
        output_dir = temp_dir / "test"

        scaffolder.scaffold(
            feature_name="User Authentication",
            output_dir=output_dir,
            num_phases=2,
            template_type="generic",
        )

        # Check master plan content
        master_content = (output_dir / "MASTER_PLAN.md").read_text()
        assert "User Authentication" in master_content
        assert "user-authentication-phase-1.md" in master_content
        assert "user-authentication-phase-2.md" in master_content

        # Check phase 1 content
        phase1_content = (output_dir / "user-authentication-phase-1.md").read_text()
        assert "User Authentication" in phase1_content
        assert "Phase 1" in phase1_content
        assert "N/A" in phase1_content  # First phase has no previous phase

        # Check phase 2 content
        phase2_content = (output_dir / "user-authentication-phase-2.md").read_text()
        assert "User Authentication" in phase2_content
        assert "Phase 2" in phase2_content
        assert "Phase 1" in phase2_content  # Should reference previous phase


class TestPlanInitCLI:
    """Tests for plan-init CLI command."""

    def test_init_cli_command(self, temp_dir: Path) -> None:
        """Test that CLI command creates files successfully."""
        runner = CliRunner()
        output_dir = temp_dir / "test-feature"

        result = runner.invoke(
            app,
            ["plan-init", "Test Feature", "--output", str(output_dir), "--phases", "2"],
        )

        if result.exit_code != 0:
            print(f"Command failed with output:\n{result.stdout}")
            if result.exception:
                import traceback

                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        assert result.exit_code == 0
        assert "Created:" in result.stdout
        assert "Success!" in result.stdout
        assert (output_dir / "MASTER_PLAN.md").exists()

    def test_init_cli_fails_if_exists(self, temp_dir: Path) -> None:
        """Test that init fails if output dir exists without --force."""
        runner = CliRunner()
        output_dir = temp_dir / "test-feature"
        output_dir.mkdir()

        result = runner.invoke(
            app,
            ["plan-init", "Test Feature", "--output", str(output_dir)],
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_init_cli_force_overwrites(self, temp_dir: Path) -> None:
        """Test that --force allows overwriting existing files."""
        runner = CliRunner()
        output_dir = temp_dir / "test-feature"
        output_dir.mkdir()
        (output_dir / "MASTER_PLAN.md").write_text("old content")

        result = runner.invoke(
            app,
            ["plan-init", "Test Feature", "--output", str(output_dir), "--force"],
        )

        assert result.exit_code == 0
        # Check that file was overwritten
        content = (output_dir / "MASTER_PLAN.md").read_text()
        assert "Test Feature" in content
        assert "old content" not in content

    def test_init_cli_default_output_dir(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default output directory is used when not specified."""
        # Change to temp directory so default output goes there
        monkeypatch.chdir(temp_dir)

        runner = CliRunner()
        result = runner.invoke(app, ["plan-init", "my-feature", "--phases", "2"])

        assert result.exit_code == 0
        # Default output should be plans/my-feature
        assert (temp_dir / "plans" / "my-feature" / "MASTER_PLAN.md").exists()

    def test_init_cli_invalid_template(self, temp_dir: Path) -> None:
        """Test that invalid template type returns error."""
        runner = CliRunner()
        output_dir = temp_dir / "test"

        result = runner.invoke(
            app,
            ["plan-init", "Test", "--output", str(output_dir), "--template", "invalid"],
        )

        assert result.exit_code == 1
        assert "Invalid template type" in result.stdout

    def test_init_cli_runs_audit(self, temp_dir: Path) -> None:
        """Test that CLI command runs audit after generating files."""
        runner = CliRunner()
        output_dir = temp_dir / "test-feature"

        result = runner.invoke(
            app,
            ["plan-init", "Test Feature", "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Running audit..." in result.stdout
        assert "Plan passes audit" in result.stdout

    def test_init_cli_shows_next_steps(self, temp_dir: Path) -> None:
        """Test that CLI command shows next steps after success."""
        runner = CliRunner()
        output_dir = temp_dir / "test-feature"

        result = runner.invoke(
            app,
            ["plan-init", "Test Feature", "--output", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Next steps:" in result.stdout
        assert "Edit" in result.stdout
        assert "debussy run" in result.stdout
