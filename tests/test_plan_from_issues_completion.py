"""Tests for plan-from-issues completion detection integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from debussy.core.models import IssueRef
from debussy.core.state import StateManager
from debussy.planners.models import GitHubIssue, IssueSet


@pytest.fixture
def state_manager(temp_db: Path) -> StateManager:
    """Create a state manager with a temporary database."""
    return StateManager(temp_db)


@pytest.fixture
def sample_issues() -> IssueSet:
    """Create a sample IssueSet for testing."""
    return IssueSet(
        issues=[
            GitHubIssue(number=10, title="Issue 10", body="Description"),
            GitHubIssue(number=11, title="Issue 11", body="Description"),
            GitHubIssue(number=12, title="Issue 12", body="Description"),
        ],
        source="github",
        filter_used="milestone:test",
    )


class TestCheckCompletedFeatures:
    """Tests for _check_completed_features function."""

    def test_no_completed_features(
        self,
        sample_issues: IssueSet,
        temp_dir: Path,
    ) -> None:
        """Test when no features have been completed."""
        from debussy.planners.command import _check_completed_features

        # Create state.db in temp_dir (this is what the code looks for)
        StateManager(temp_dir / "state.db")

        console = Console(force_terminal=True)

        # Patch get_orchestrator_dir to point to our temp_dir
        with patch("debussy.config.get_orchestrator_dir") as mock_dir:
            mock_dir.return_value = temp_dir

            completed = _check_completed_features(sample_issues, console, verbose=False)

        assert completed == []

    def test_with_completed_features(
        self,
        sample_issues: IssueSet,
        temp_dir: Path,
    ) -> None:
        """Test detection of completed features."""
        from debussy.planners.command import _check_completed_features

        # Create state.db in temp_dir (this is what the code looks for)
        state_manager = StateManager(temp_dir / "state.db")

        # Record a completion that overlaps with sample_issues
        state_manager.record_completion(
            name="Previous Feature",
            issues=[
                IssueRef(type="github", id="10"),
                IssueRef(type="github", id="99"),  # Extra issue not in sample
            ],
            plan_path=Path("/tmp/previous.md"),
        )

        console = Console(force_terminal=True)

        # Patch to use our temp_dir so _check_completed_features finds state.db
        with patch("debussy.config.get_orchestrator_dir") as mock_dir:
            mock_dir.return_value = temp_dir

            completed = _check_completed_features(sample_issues, console, verbose=False)

        assert len(completed) == 1
        assert completed[0].name == "Previous Feature"

    def test_empty_issues(self, temp_dir: Path) -> None:
        """Test with empty issue set."""
        from debussy.planners.command import _check_completed_features

        # Create state.db in temp_dir
        StateManager(temp_dir / "state.db")

        empty_issues = IssueSet(issues=[], source="github")
        console = Console(force_terminal=True)

        with patch("debussy.config.get_orchestrator_dir") as mock_dir:
            mock_dir.return_value = temp_dir

            completed = _check_completed_features(empty_issues, console, verbose=False)

        assert completed == []


class TestConfirmRegeneration:
    """Tests for _confirm_regeneration function."""

    def test_non_interactive_returns_false(
        self,
        state_manager: StateManager,
        sample_issues: IssueSet,
    ) -> None:
        """Test that non-interactive mode returns False."""
        from debussy.planners.command import _confirm_regeneration

        # Record a completion
        state_manager.record_completion(
            name="Test Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/test.md"),
        )

        # Get the completed features
        completed = state_manager.find_completed_features([IssueRef(type="github", id="10")])

        console = Console(force_terminal=True)

        # Mock sys.stdin.isatty to return False (non-interactive)
        with patch("sys.stdin.isatty", return_value=False):
            result = _confirm_regeneration(completed, sample_issues, console)

        assert result is False

    def test_user_confirms(
        self,
        state_manager: StateManager,
        sample_issues: IssueSet,
    ) -> None:
        """Test user confirmation with 'y' response."""
        from debussy.planners.command import _confirm_regeneration

        state_manager.record_completion(
            name="Test Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/test.md"),
        )

        completed = state_manager.find_completed_features([IssueRef(type="github", id="10")])

        console = MagicMock(spec=Console)
        console.input.return_value = "y"

        with patch("sys.stdin.isatty", return_value=True):
            result = _confirm_regeneration(completed, sample_issues, console)

        assert result is True

    def test_user_rejects(
        self,
        state_manager: StateManager,
        sample_issues: IssueSet,
    ) -> None:
        """Test user rejection with 'n' response."""
        from debussy.planners.command import _confirm_regeneration

        state_manager.record_completion(
            name="Test Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/test.md"),
        )

        completed = state_manager.find_completed_features([IssueRef(type="github", id="10")])

        console = MagicMock(spec=Console)
        console.input.return_value = "n"

        with patch("sys.stdin.isatty", return_value=True):
            result = _confirm_regeneration(completed, sample_issues, console)

        assert result is False

    def test_keyboard_interrupt_returns_false(
        self,
        state_manager: StateManager,
        sample_issues: IssueSet,
    ) -> None:
        """Test that KeyboardInterrupt returns False."""
        from debussy.planners.command import _confirm_regeneration

        state_manager.record_completion(
            name="Test Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/test.md"),
        )

        completed = state_manager.find_completed_features([IssueRef(type="github", id="10")])

        console = MagicMock(spec=Console)
        console.input.side_effect = KeyboardInterrupt()

        with patch("sys.stdin.isatty", return_value=True):
            result = _confirm_regeneration(completed, sample_issues, console)

        assert result is False


class TestPlanFromIssuesForceFlag:
    """Tests for --force flag in plan-from-issues."""

    def test_force_bypasses_completion_check(
        self,
        temp_dir: Path,
    ) -> None:
        """Test that --force bypasses completion confirmation."""
        from debussy.planners.command import plan_from_issues

        # Create state.db in temp_dir and record a completion
        state_manager = StateManager(temp_dir / "state.db")
        state_manager.record_completion(
            name="Completed Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/completed.md"),
        )

        console = Console(force_terminal=True)

        # Mock all the phases to avoid real API calls
        with (
            patch("debussy.planners.command._get_current_repo", return_value="owner/repo"),
            patch("debussy.config.get_orchestrator_dir", return_value=temp_dir),
            patch("debussy.planners.command._fetch_phase") as mock_fetch,
            patch("debussy.planners.command._analyze_phase") as mock_analyze,
            patch("debussy.planners.command._generate_phase") as mock_generate,
            patch("debussy.planners.command._audit_loop") as mock_audit,
            patch("debussy.planners.command._print_summary"),
        ):
            # Setup mock returns
            mock_fetch.return_value = IssueSet(
                issues=[GitHubIssue(number=10, title="Issue", body="Body")],
                source="github",
            )
            mock_analyze.return_value = MagicMock(
                total_gaps=0,
                critical_gaps=0,
                questions_needed=False,
            )
            mock_generate.return_value = ["/tmp/plan.md"]
            mock_audit.return_value = (True, 1)

            # With force=True, should proceed despite completion
            result = plan_from_issues(
                source="gh",
                repo="owner/repo",
                milestone="test",
                force=True,
                console=console,
            )

            assert result.success is True
            assert result.completed_features_found == 1
            assert result.user_aborted is False

    def test_without_force_prompts_confirmation(
        self,
        temp_dir: Path,
    ) -> None:
        """Test that without --force, confirmation is required."""
        from debussy.planners.command import plan_from_issues

        # Create state.db in temp_dir and record a completion
        state_manager = StateManager(temp_dir / "state.db")
        state_manager.record_completion(
            name="Completed Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/completed.md"),
        )

        console = Console(force_terminal=True)

        with (
            patch("debussy.planners.command._get_current_repo", return_value="owner/repo"),
            patch("debussy.config.get_orchestrator_dir", return_value=temp_dir),
            patch("debussy.planners.command._fetch_phase") as mock_fetch,
            patch("sys.stdin.isatty", return_value=False),  # Non-interactive
        ):
            mock_fetch.return_value = IssueSet(
                issues=[GitHubIssue(number=10, title="Issue", body="Body")],
                source="github",
            )

            # Without force and non-interactive, should abort
            result = plan_from_issues(
                source="gh",
                repo="owner/repo",
                milestone="test",
                force=False,
                console=console,
            )

            assert result.success is False
            assert result.user_aborted is True
            assert result.completed_features_found == 1


class TestResultFields:
    """Tests for PlanFromIssuesResult fields."""

    def test_result_includes_completion_info(self) -> None:
        """Test that result includes completion tracking fields."""
        from debussy.planners.command import PlanFromIssuesResult

        result = PlanFromIssuesResult()

        assert hasattr(result, "completed_features_found")
        assert hasattr(result, "user_aborted")
        assert result.completed_features_found == 0
        assert result.user_aborted is False
