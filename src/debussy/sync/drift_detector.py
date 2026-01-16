"""State drift detection between Debussy and external issue trackers.

This module compares Debussy's internal phase state with the current
state of linked issues in external trackers (GitHub/Jira) to detect
drift and enable reconciliation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from debussy.core.models import (
    DriftReport,
    DriftType,
    IssueStatus,
    PhaseStatus,
    ReconciliationAction,
    ReconciliationPlan,
    SyncDirection,
)
from debussy.parsers.master import parse_master_plan
from debussy.sync.github_sync import GitHubSyncCoordinator
from debussy.sync.jira_sync import JiraSynchronizer

if TYPE_CHECKING:
    from debussy.core.state import StateManager
    from debussy.sync.status_fetcher import IssueStatusFetcher

logger = logging.getLogger(__name__)


# Mapping from Debussy phase status to expected issue states
PHASE_TO_GITHUB_STATE: dict[PhaseStatus, str] = {
    PhaseStatus.PENDING: "open",
    PhaseStatus.RUNNING: "open",
    PhaseStatus.VALIDATING: "open",
    PhaseStatus.AWAITING_HUMAN: "open",
    PhaseStatus.COMPLETED: "closed",  # Or open with completed label
    PhaseStatus.FAILED: "open",
    PhaseStatus.BLOCKED: "open",
}

# Expected labels for each phase status (GitHub)
PHASE_TO_GITHUB_LABELS: dict[PhaseStatus, set[str]] = {
    PhaseStatus.RUNNING: {"debussy:in-progress"},
    PhaseStatus.COMPLETED: {"debussy:completed"},
    PhaseStatus.FAILED: {"debussy:failed"},
}

# Mapping from Jira status names to abstract states (customize per workflow)
JIRA_STATUS_CATEGORIES = {
    "to do": "open",
    "open": "open",
    "backlog": "open",
    "in progress": "in_progress",
    "in review": "in_progress",
    "done": "closed",
    "closed": "closed",
    "resolved": "closed",
}


class DriftDetector:
    """Detects state drift between Debussy and external issue trackers.

    Compares phase execution status from StateManager with current
    issue status from GitHub/Jira APIs to identify mismatches.
    """

    def __init__(
        self,
        state_manager: StateManager,
        fetcher: IssueStatusFetcher,
    ) -> None:
        """Initialize the drift detector.

        Args:
            state_manager: State manager for querying Debussy state.
            fetcher: Status fetcher for getting current tracker state.
        """
        self.state = state_manager
        self.fetcher = fetcher

    async def detect_drift(
        self,
        run_id: str,
        master_plan_path: Path,
        use_cache: bool = True,
    ) -> list[DriftReport]:
        """Detect state drift for all linked issues in a run.

        Args:
            run_id: The run ID to check.
            master_plan_path: Path to the master plan file.
            use_cache: Whether to use cached status (False to force refresh).

        Returns:
            List of DriftReport objects for each detected drift.
        """
        # Parse the master plan to get linked issues
        plan = parse_master_plan(master_plan_path)

        # Get current run state
        run_state = self.state.get_run(run_id)
        if not run_state:
            logger.warning(f"Run {run_id} not found")
            return []

        # Build map of phase statuses from state manager
        phase_statuses: dict[str, PhaseStatus] = {}
        completed_phases = self.state.get_completed_phases(run_id)

        for phase in plan.phases:
            if phase.id in completed_phases:
                phase_statuses[phase.id] = PhaseStatus.COMPLETED
            else:
                # Find latest execution status
                for exec_record in reversed(run_state.phase_executions):
                    if exec_record.phase_id == phase.id:
                        phase_statuses[phase.id] = exec_record.status
                        break
                else:
                    phase_statuses[phase.id] = phase.status

        # Extract linked issues from plan
        github_issues = self._extract_github_issues(plan.github_issues)
        jira_issues = self._extract_jira_issues(plan.jira_issues)

        # Fetch current status from trackers
        github_statuses: dict[str, IssueStatus] = {}
        jira_statuses: dict[str, IssueStatus] = {}

        if github_issues:
            github_statuses = await self.fetcher.fetch_github_status(
                github_issues,
                use_cache=use_cache,
            )

        if jira_issues:
            jira_statuses = await self.fetcher.fetch_jira_status(
                jira_issues,
                use_cache=use_cache,
            )

        # Determine expected state based on overall run/phase status
        expected_state = self._compute_expected_state(run_state.status, phase_statuses)

        # Detect drift
        drift_reports: list[DriftReport] = []

        for issue_id, status in github_statuses.items():
            drift = self._check_github_drift(issue_id, status, expected_state)
            if drift:
                drift_reports.append(drift)

        for issue_id, status in jira_statuses.items():
            drift = self._check_jira_drift(issue_id, status, expected_state)
            if drift:
                drift_reports.append(drift)

        return drift_reports

    def _extract_github_issues(
        self,
        github_issues: list[int] | str | None,
    ) -> list[str]:
        """Extract GitHub issue IDs from plan metadata."""
        if github_issues is None:
            return []

        if isinstance(github_issues, list):
            return [str(n) for n in github_issues]

        # Parse string format: "#10, #11" or "gh#10, gh#11"
        coordinator = GitHubSyncCoordinator(
            repo="dummy/repo",
            config=None,  # type: ignore[arg-type]
        )
        return [str(n) for n in coordinator.parse_github_issues(github_issues)]

    def _extract_jira_issues(
        self,
        jira_issues: list[str] | str | None,
    ) -> list[str]:
        """Extract Jira issue keys from plan metadata."""
        if jira_issues is None:
            return []

        if isinstance(jira_issues, list):
            return jira_issues

        # Parse string format
        # Use JiraSynchronizer's parser (requires config)
        from debussy.config import JiraConfig

        config = JiraConfig(url="https://dummy.atlassian.net")
        synchronizer = JiraSynchronizer(config=config)
        return synchronizer.parse_jira_issues(jira_issues)

    def _compute_expected_state(
        self,
        run_status: object,  # noqa: ARG002
        phase_statuses: dict[str, PhaseStatus],
    ) -> dict[str, Any]:
        """Compute expected issue state based on run progress.

        For now, we use a simple heuristic:
        - If all phases completed -> issues should be closed
        - If any phase is running -> issues should be open with in-progress label
        - Otherwise -> issues should be open

        Returns:
            Dict with 'github_state', 'github_labels', 'jira_state'.
        """
        all_completed = all(status == PhaseStatus.COMPLETED for status in phase_statuses.values())
        any_running = any(status == PhaseStatus.RUNNING for status in phase_statuses.values())
        any_failed = any(status == PhaseStatus.FAILED for status in phase_statuses.values())

        if all_completed:
            return {
                "github_state": "closed",
                "github_labels": ["debussy:completed"],
                "jira_state": "closed",
            }
        elif any_running:
            return {
                "github_state": "open",
                "github_labels": ["debussy:in-progress"],
                "jira_state": "in_progress",
            }
        elif any_failed:
            return {
                "github_state": "open",
                "github_labels": ["debussy:failed"],
                "jira_state": "open",
            }
        else:
            return {
                "github_state": "open",
                "github_labels": [],
                "jira_state": "open",
            }

    def _check_github_drift(
        self,
        issue_id: str,
        status: IssueStatus,
        expected: dict[str, Any],
    ) -> DriftReport | None:
        """Check for drift in a GitHub issue."""
        expected_state = expected["github_state"]
        actual_state = status.state

        # Check for state mismatch
        if expected_state == "closed" and actual_state == "open":
            return DriftReport(
                issue_id=issue_id,
                platform="github",
                expected_state="closed",
                actual_state="open",
                drift_type=DriftType.REOPENED_EXTERNALLY,
                tracker_timestamp=status.last_updated,
            )
        elif expected_state == "open" and actual_state == "closed":
            return DriftReport(
                issue_id=issue_id,
                platform="github",
                expected_state="open",
                actual_state="closed",
                drift_type=DriftType.CLOSED_EXTERNALLY,
                tracker_timestamp=status.last_updated,
            )

        # Check for label mismatch
        expected_labels = set(expected.get("github_labels", []))
        actual_labels = {label for label in status.labels if label.startswith("debussy:")}

        if expected_labels and expected_labels != actual_labels:
            return DriftReport(
                issue_id=issue_id,
                platform="github",
                expected_state=", ".join(sorted(expected_labels)) or "no debussy labels",
                actual_state=", ".join(sorted(actual_labels)) or "no debussy labels",
                drift_type=DriftType.LABEL_MISMATCH,
                tracker_timestamp=status.last_updated,
            )

        return None

    def _check_jira_drift(
        self,
        issue_id: str,
        status: IssueStatus,
        expected: dict[str, Any],
    ) -> DriftReport | None:
        """Check for drift in a Jira issue."""
        expected_state = expected["jira_state"]
        actual_category = JIRA_STATUS_CATEGORIES.get(status.state.lower(), "unknown")

        # Normalize expected state to category
        if expected_state == "closed" and actual_category != "closed":
            return DriftReport(
                issue_id=issue_id,
                platform="jira",
                expected_state="closed",
                actual_state=status.state,
                drift_type=DriftType.REOPENED_EXTERNALLY,
                tracker_timestamp=status.last_updated,
            )
        elif expected_state in ("open", "in_progress") and actual_category == "closed":
            return DriftReport(
                issue_id=issue_id,
                platform="jira",
                expected_state=expected_state,
                actual_state=status.state,
                drift_type=DriftType.CLOSED_EXTERNALLY,
                tracker_timestamp=status.last_updated,
            )
        elif expected_state == "in_progress" and actual_category == "open":
            return DriftReport(
                issue_id=issue_id,
                platform="jira",
                expected_state="in_progress",
                actual_state=status.state,
                drift_type=DriftType.STATUS_MISMATCH,
                tracker_timestamp=status.last_updated,
            )

        return None

    def create_reconciliation_plan(
        self,
        drift_reports: list[DriftReport],
        direction: SyncDirection = SyncDirection.FROM_TRACKER,
    ) -> ReconciliationPlan:
        """Create a plan to reconcile detected drift.

        Args:
            drift_reports: List of detected drift reports.
            direction: Sync direction (from tracker or to tracker).

        Returns:
            ReconciliationPlan with proposed actions.
        """
        actions: list[ReconciliationAction] = []

        for drift in drift_reports:
            action = self._create_from_tracker_action(drift) if direction == SyncDirection.FROM_TRACKER else self._create_to_tracker_action(drift)
            if action:
                actions.append(action)

        return ReconciliationPlan(
            direction=direction,
            actions=actions,
            drift_reports=drift_reports,
            total_drift_count=len(drift_reports),
        )

    def _create_from_tracker_action(
        self,
        drift: DriftReport,
    ) -> ReconciliationAction | None:
        """Create action to update Debussy state from tracker."""
        if drift.drift_type == DriftType.CLOSED_EXTERNALLY:
            return ReconciliationAction(
                issue_id=drift.issue_id,
                platform=drift.platform,
                action="update_phase_status",
                description=f"Mark linked phases as completed (issue {drift.issue_id} closed externally)",
                from_value=drift.expected_state,
                to_value="completed",
            )
        elif drift.drift_type == DriftType.REOPENED_EXTERNALLY:
            return ReconciliationAction(
                issue_id=drift.issue_id,
                platform=drift.platform,
                action="update_phase_status",
                description=f"Reopen linked phases (issue {drift.issue_id} reopened externally)",
                from_value="completed",
                to_value="pending",
            )
        return None

    def _create_to_tracker_action(
        self,
        drift: DriftReport,
    ) -> ReconciliationAction | None:
        """Create action to update tracker from Debussy state."""
        if drift.drift_type in (DriftType.CLOSED_EXTERNALLY, DriftType.REOPENED_EXTERNALLY):
            return ReconciliationAction(
                issue_id=drift.issue_id,
                platform=drift.platform,
                action="update_issue_status",
                description=f"Update issue {drift.issue_id} state to match Debussy",
                from_value=drift.actual_state,
                to_value=drift.expected_state,
            )
        elif drift.drift_type == DriftType.LABEL_MISMATCH:
            return ReconciliationAction(
                issue_id=drift.issue_id,
                platform=drift.platform,
                action="update_labels",
                description=f"Update labels on issue {drift.issue_id}",
                from_value=drift.actual_state,
                to_value=drift.expected_state,
            )
        return None


class StateSynchronizer:
    """Applies reconciliation plans to sync Debussy and tracker state."""

    def __init__(
        self,
        state_manager: StateManager,
        github_coordinator: GitHubSyncCoordinator | None = None,
        jira_synchronizer: JiraSynchronizer | None = None,
    ) -> None:
        """Initialize the synchronizer.

        Args:
            state_manager: State manager for updating Debussy state.
            github_coordinator: Optional GitHub sync coordinator.
            jira_synchronizer: Optional Jira synchronizer.
        """
        self.state = state_manager
        self.github = github_coordinator
        self.jira = jira_synchronizer

    async def apply_plan(
        self,
        plan: ReconciliationPlan,
        run_id: str,
        dry_run: bool = True,
    ) -> list[tuple[ReconciliationAction, bool, str | None]]:
        """Apply a reconciliation plan.

        Args:
            plan: The reconciliation plan to apply.
            run_id: The run ID to update.
            dry_run: If True, only log actions without executing.

        Returns:
            List of tuples: (action, success, error_message).
        """
        results: list[tuple[ReconciliationAction, bool, str | None]] = []

        for action in plan.actions:
            if dry_run:
                logger.info(f"[DRY RUN] Would execute: {action.description}")
                results.append((action, True, None))
                continue

            try:
                success = await self._execute_action(action, run_id)
                results.append((action, success, None))
            except Exception as e:
                logger.error(f"Failed to execute action: {e}")
                results.append((action, False, str(e)))

        return results

    async def _execute_action(
        self,
        action: ReconciliationAction,
        run_id: str,  # noqa: ARG002
    ) -> bool:
        """Execute a single reconciliation action."""
        if action.action == "update_phase_status":
            # Update Debussy state based on tracker
            # This requires knowing which phases are linked to this issue
            # For now, log the action - full implementation needs issue-to-phase mapping
            logger.info(f"Would update phase status: {action.description}")
            return True

        elif action.action == "update_issue_status":
            # Update tracker state
            if action.platform == "github" and self.github:
                # Close or reopen issue
                issue_num = int(action.issue_id)
                if action.to_value == "closed":
                    await self.github.client.close_issue(issue_num)
                # Reopening not yet implemented in client
                return True
            elif action.platform == "jira" and self.jira:
                # Transition issue
                # This would require finding the right transition name
                logger.info(f"Would transition Jira issue: {action.description}")
                return True

        elif action.action == "update_labels":
            if action.platform == "github" and self.github:
                # Update labels
                issue_num = int(action.issue_id)
                expected_labels = action.to_value.split(", ") if action.to_value else []
                await self.github.client.update_labels(issue_num, expected_labels)
                return True

        return False
