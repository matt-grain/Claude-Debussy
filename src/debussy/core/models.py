"""Core data models for the debussy."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class PhaseStatus(str, Enum):
    """Status of a phase in the orchestration pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    VALIDATING = "validating"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class RunStatus(str, Enum):
    """Status of an orchestration run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ComplianceIssueType(str, Enum):
    """Types of compliance issues that can be detected."""

    NOTES_MISSING = "notes_missing"
    NOTES_INCOMPLETE = "notes_incomplete"
    GATES_FAILED = "gates_failed"
    AGENT_SKIPPED = "agent_skipped"
    STEP_SKIPPED = "step_skipped"


class RemediationStrategy(str, Enum):
    """Strategy for handling compliance failures."""

    WARN_AND_ACCEPT = "warn"  # Minor issues, log and continue
    TARGETED_FIX = "fix"  # Spawn remediation session
    FULL_RETRY = "retry"  # Fresh session, restart phase
    HUMAN_REQUIRED = "human"  # Pause for human decision


# =============================================================================
# Plan Models
# =============================================================================


class Task(BaseModel):
    """A task item from a phase plan."""

    id: str
    description: str
    completed: bool = False


class Gate(BaseModel):
    """A validation gate that must pass."""

    name: str
    command: str
    blocking: bool = True


class Phase(BaseModel):
    """A phase in the master plan."""

    id: str
    title: str
    path: Path
    status: PhaseStatus = PhaseStatus.PENDING
    depends_on: list[str] = Field(default_factory=list)
    gates: list[Gate] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    required_agents: list[str] = Field(default_factory=list)
    required_steps: list[str] = Field(default_factory=list)
    notes_input: Path | None = None
    notes_output: Path | None = None


class MasterPlan(BaseModel):
    """A master plan containing multiple phases."""

    name: str
    path: Path
    phases: list[Phase]
    github_issues: list[int] | str | None = Field(
        default=None,
        description="GitHub issue numbers to sync (e.g., [10, 11] or '#10, #11')",
    )
    github_repo: str | None = Field(
        default=None,
        description="GitHub repo for sync (e.g., 'owner/repo'). Auto-detected if not set.",
    )
    jira_issues: list[str] | str | None = Field(
        default=None,
        description="Jira issue keys to sync (e.g., ['PROJ-123', 'PROJ-124'] or 'PROJ-123, PROJ-124')",
    )
    created_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Execution Models
# =============================================================================


class GateResult(BaseModel):
    """Result of running a single gate."""

    name: str
    command: str
    passed: bool
    output: str
    executed_at: datetime = Field(default_factory=datetime.now)


class ExecutionResult(BaseModel):
    """Result of executing a Claude session."""

    success: bool
    session_log: str
    exit_code: int
    duration_seconds: float
    pid: int | None = None


class CompletionSignal(BaseModel):
    """Signal sent by Claude worker when phase is done."""

    phase_id: str
    status: Literal["completed", "blocked", "failed"]
    reason: str | None = None
    report: dict[str, object] | None = None
    signaled_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Compliance Models
# =============================================================================


class ComplianceIssue(BaseModel):
    """A compliance issue found during verification."""

    type: ComplianceIssueType
    severity: Literal["low", "high", "critical"]
    details: str
    evidence: str | None = None


class ComplianceResult(BaseModel):
    """Result of compliance verification."""

    passed: bool
    issues: list[ComplianceIssue] = Field(default_factory=list)
    remediation: RemediationStrategy | None = None
    verified_steps: list[str] = Field(default_factory=list)
    gate_results: list[GateResult] = Field(default_factory=list)


# =============================================================================
# State Models
# =============================================================================


class PhaseExecution(BaseModel):
    """Record of a phase execution attempt."""

    id: int | None = None
    run_id: str
    phase_id: str
    attempt: int = 1
    status: PhaseStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    claude_pid: int | None = None
    log_path: Path | None = None
    error_message: str | None = None


class RunState(BaseModel):
    """State of an orchestration run."""

    id: str
    master_plan_path: Path
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus
    current_phase: str | None = None
    phase_executions: list[PhaseExecution] = Field(default_factory=list)


# =============================================================================
# Completion Tracking Models
# =============================================================================


class IssueRef(BaseModel):
    """Reference to an issue (GitHub or Jira)."""

    type: Literal["github", "jira"]
    id: str
    """Issue ID: number for GitHub (e.g., '10'), key for Jira (e.g., 'PROJ-123')"""


class CompletedFeature(BaseModel):
    """Record of a completed feature with linked issues."""

    id: int | None = None
    name: str
    completed_at: datetime
    issues: list[IssueRef]
    plan_path: Path


# =============================================================================
# Issue Sync Models
# =============================================================================


class IssueStatus(BaseModel):
    """Current status of an issue from an external tracker."""

    id: str = Field(description="Issue identifier (e.g., '10' for GitHub, 'PROJ-123' for Jira)")
    platform: Literal["github", "jira"]
    state: str = Field(description="Current state (e.g., 'open', 'closed' for GitHub; 'In Progress', 'Done' for Jira)")
    labels: list[str] = Field(default_factory=list)
    milestone: str | None = None
    last_updated: datetime | None = None


class DriftType(str, Enum):
    """Types of state drift between Debussy and external trackers."""

    LABEL_MISMATCH = "label_mismatch"  # Debussy labels don't match tracker
    STATUS_MISMATCH = "status_mismatch"  # Expected vs actual state differs
    CLOSED_EXTERNALLY = "closed_externally"  # Tracker shows closed, Debussy expects open
    REOPENED_EXTERNALLY = "reopened_externally"  # Tracker shows open, Debussy expects closed


class DriftReport(BaseModel):
    """Report of state drift for a single issue."""

    issue_id: str = Field(description="Issue identifier")
    platform: Literal["github", "jira"]
    expected_state: str = Field(description="State Debussy expects based on phase status")
    actual_state: str = Field(description="Current state in the tracker")
    drift_type: DriftType
    debussy_timestamp: datetime | None = Field(
        default=None,
        description="When Debussy last synced this issue",
    )
    tracker_timestamp: datetime | None = Field(
        default=None,
        description="When the tracker was last updated",
    )
    debussy_is_newer: bool | None = Field(
        default=None,
        description="True if Debussy state is more recent than tracker",
    )


class SyncDirection(str, Enum):
    """Direction for state reconciliation."""

    FROM_TRACKER = "from-tracker"  # Treat tracker as source of truth (default)
    TO_TRACKER = "to-tracker"  # Push Debussy state to tracker


class ReconciliationAction(BaseModel):
    """A proposed action to reconcile state drift."""

    issue_id: str
    platform: Literal["github", "jira"]
    action: Literal["update_phase_status", "update_issue_status", "update_labels"]
    description: str
    from_value: str
    to_value: str


class ReconciliationPlan(BaseModel):
    """Plan for reconciling state drift."""

    direction: SyncDirection
    actions: list[ReconciliationAction] = Field(default_factory=list)
    drift_reports: list[DriftReport] = Field(default_factory=list)
    total_drift_count: int = 0
