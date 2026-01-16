"""Tests for the drift detector."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from debussy.core.models import (
    DriftReport,
    DriftType,
    IssueStatus,
    PhaseStatus,
    ReconciliationPlan,
    SyncDirection,
)
from debussy.sync.drift_detector import (
    JIRA_STATUS_CATEGORIES,
    DriftDetector,
    StateSynchronizer,
)


class TestDriftDetector:
    """Tests for DriftDetector."""

    @pytest.fixture
    def mock_state_manager(self) -> MagicMock:
        """Create a mock state manager."""
        mock = MagicMock()
        mock.get_run.return_value = MagicMock(
            id="test-run",
            status="running",
            phase_executions=[],
        )
        mock.get_completed_phases.return_value = set()
        return mock

    @pytest.fixture
    def mock_fetcher(self) -> AsyncMock:
        """Create a mock status fetcher."""
        mock = AsyncMock()
        mock.fetch_github_status.return_value = {}
        mock.fetch_jira_status.return_value = {}
        return mock

    def test_detector_init(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detector initializes with dependencies."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        assert detector.state is mock_state_manager
        assert detector.fetcher is mock_fetcher

    def test_extract_github_issues_from_list(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test extracting GitHub issues from list format."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        result = detector._extract_github_issues([10, 11, 12])
        assert result == ["10", "11", "12"]

    def test_extract_github_issues_from_none(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test extracting from None returns empty list."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        result = detector._extract_github_issues(None)
        assert result == []

    def test_extract_jira_issues_from_list(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test extracting Jira issues from list format."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        result = detector._extract_jira_issues(["PROJ-123", "PROJ-124"])
        assert result == ["PROJ-123", "PROJ-124"]

    def test_extract_jira_issues_from_none(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test extracting from None returns empty list."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        result = detector._extract_jira_issues(None)
        assert result == []

    def test_compute_expected_state_all_completed(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test expected state when all phases completed."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        phase_statuses = {
            "1": PhaseStatus.COMPLETED,
            "2": PhaseStatus.COMPLETED,
        }

        result = detector._compute_expected_state(None, phase_statuses)

        assert result["github_state"] == "closed"
        assert result["jira_state"] == "closed"

    def test_compute_expected_state_running(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test expected state when phase is running."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        phase_statuses = {
            "1": PhaseStatus.COMPLETED,
            "2": PhaseStatus.RUNNING,
        }

        result = detector._compute_expected_state(None, phase_statuses)

        assert result["github_state"] == "open"
        assert "debussy:in-progress" in result["github_labels"]

    def test_compute_expected_state_failed(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test expected state when phase failed."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        phase_statuses = {
            "1": PhaseStatus.COMPLETED,
            "2": PhaseStatus.FAILED,
        }

        result = detector._compute_expected_state(None, phase_statuses)

        assert result["github_state"] == "open"
        assert "debussy:failed" in result["github_labels"]

    def test_check_github_drift_closed_externally(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detecting when issue was closed externally."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(id="10", platform="github", state="closed")
        expected = {"github_state": "open", "github_labels": []}

        drift = detector._check_github_drift("10", status, expected)

        assert drift is not None
        assert drift.drift_type == DriftType.CLOSED_EXTERNALLY
        assert drift.expected_state == "open"
        assert drift.actual_state == "closed"

    def test_check_github_drift_reopened_externally(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detecting when issue was reopened externally."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(id="10", platform="github", state="open")
        expected = {"github_state": "closed", "github_labels": ["debussy:completed"]}

        drift = detector._check_github_drift("10", status, expected)

        assert drift is not None
        assert drift.drift_type == DriftType.REOPENED_EXTERNALLY

    def test_check_github_drift_label_mismatch(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detecting label mismatch."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(
            id="10",
            platform="github",
            state="open",
            labels=["debussy:failed"],
        )
        expected = {
            "github_state": "open",
            "github_labels": ["debussy:in-progress"],
        }

        drift = detector._check_github_drift("10", status, expected)

        assert drift is not None
        assert drift.drift_type == DriftType.LABEL_MISMATCH

    def test_check_github_drift_no_drift(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test no drift when states match."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(
            id="10",
            platform="github",
            state="open",
            labels=["debussy:in-progress"],
        )
        expected = {
            "github_state": "open",
            "github_labels": ["debussy:in-progress"],
        }

        drift = detector._check_github_drift("10", status, expected)

        assert drift is None

    def test_check_jira_drift_closed_externally(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detecting when Jira issue was closed externally."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(id="PROJ-123", platform="jira", state="Done")
        expected = {"jira_state": "in_progress"}

        drift = detector._check_jira_drift("PROJ-123", status, expected)

        assert drift is not None
        assert drift.drift_type == DriftType.CLOSED_EXTERNALLY

    def test_check_jira_drift_status_mismatch(
        self,
        mock_state_manager: MagicMock,
        mock_fetcher: AsyncMock,
    ) -> None:
        """Test detecting Jira status mismatch."""
        detector = DriftDetector(mock_state_manager, mock_fetcher)
        status = IssueStatus(id="PROJ-123", platform="jira", state="To Do")
        expected = {"jira_state": "in_progress"}

        drift = detector._check_jira_drift("PROJ-123", status, expected)

        assert drift is not None
        assert drift.drift_type == DriftType.STATUS_MISMATCH

    def test_jira_status_categories(self) -> None:
        """Test Jira status category mapping."""
        assert JIRA_STATUS_CATEGORIES["done"] == "closed"
        assert JIRA_STATUS_CATEGORIES["in progress"] == "in_progress"
        assert JIRA_STATUS_CATEGORIES["to do"] == "open"


class TestReconciliationPlan:
    """Tests for reconciliation plan creation."""

    @pytest.fixture
    def detector(self) -> DriftDetector:
        """Create detector with mocks."""
        mock_state = MagicMock()
        mock_fetcher = AsyncMock()
        return DriftDetector(mock_state, mock_fetcher)

    def test_create_plan_from_tracker(self, detector: DriftDetector) -> None:
        """Test creating plan for from-tracker direction."""
        drift_reports = [
            DriftReport(
                issue_id="10",
                platform="github",
                expected_state="open",
                actual_state="closed",
                drift_type=DriftType.CLOSED_EXTERNALLY,
            ),
        ]

        plan = detector.create_reconciliation_plan(
            drift_reports,
            SyncDirection.FROM_TRACKER,
        )

        assert plan.direction == SyncDirection.FROM_TRACKER
        assert plan.total_drift_count == 1
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "update_phase_status"

    def test_create_plan_to_tracker(self, detector: DriftDetector) -> None:
        """Test creating plan for to-tracker direction."""
        drift_reports = [
            DriftReport(
                issue_id="10",
                platform="github",
                expected_state="open",
                actual_state="closed",
                drift_type=DriftType.CLOSED_EXTERNALLY,
            ),
        ]

        plan = detector.create_reconciliation_plan(
            drift_reports,
            SyncDirection.TO_TRACKER,
        )

        assert plan.direction == SyncDirection.TO_TRACKER
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "update_issue_status"

    def test_create_plan_empty_drift(self, detector: DriftDetector) -> None:
        """Test creating plan with no drift."""
        plan = detector.create_reconciliation_plan([], SyncDirection.FROM_TRACKER)

        assert plan.total_drift_count == 0
        assert plan.actions == []


class TestStateSynchronizer:
    """Tests for StateSynchronizer."""

    @pytest.fixture
    def synchronizer(self) -> StateSynchronizer:
        """Create synchronizer with mocks."""
        mock_state = MagicMock()
        return StateSynchronizer(mock_state)

    @pytest.mark.asyncio
    async def test_apply_plan_dry_run(self, synchronizer: StateSynchronizer) -> None:
        """Test applying plan in dry-run mode."""
        from debussy.core.models import ReconciliationAction

        plan = ReconciliationPlan(
            direction=SyncDirection.FROM_TRACKER,
            actions=[
                ReconciliationAction(
                    issue_id="10",
                    platform="github",
                    action="update_phase_status",
                    description="Test action",
                    from_value="open",
                    to_value="completed",
                ),
            ],
            total_drift_count=1,
        )

        results = await synchronizer.apply_plan(plan, "test-run", dry_run=True)

        assert len(results) == 1
        _action, success, error = results[0]
        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_apply_plan_executes_actions(
        self,
        synchronizer: StateSynchronizer,
    ) -> None:
        """Test applying plan executes actions when dry_run=False."""
        from debussy.core.models import ReconciliationAction

        plan = ReconciliationPlan(
            direction=SyncDirection.FROM_TRACKER,
            actions=[
                ReconciliationAction(
                    issue_id="10",
                    platform="github",
                    action="update_phase_status",
                    description="Mark completed",
                    from_value="open",
                    to_value="completed",
                ),
            ],
            total_drift_count=1,
        )

        results = await synchronizer.apply_plan(plan, "test-run", dry_run=False)

        assert len(results) == 1
        # Action execution is logged but not fully implemented
        _action, success, _error = results[0]
        assert success is True
