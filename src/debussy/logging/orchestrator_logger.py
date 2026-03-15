"""Orchestrator-level logging infrastructure.

This module provides dedicated logging for orchestrator events:
- Phase start/stop events
- Commit actions
- Phase rejections/skips
- Configuration decisions

Logs are written to `.debussy/logs/orchestrator.log` with a format
consistent with worker logs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from debussy.core.models import PhaseStatus

# Log format matching worker logs: [TIMESTAMP] [LEVEL] message
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class OrchestratorLogger:
    """Logger for orchestrator-level events.

    Provides structured logging for phase transitions, commits, rejections,
    and configuration decisions. All events are written to a dedicated log file
    at `.debussy/logs/orchestrator.log`.

    Attributes:
        logger: The underlying Python logger instance.
        log_path: Path to the orchestrator log file.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the orchestrator logger.

        Args:
            project_root: Path to the project root directory.
                The log file will be created at `{project_root}/.debussy/logs/orchestrator.log`.
        """
        self.log_dir = project_root / ".debussy" / "logs"
        self.log_path = self.log_dir / "orchestrator.log"

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create a dedicated logger using a unique name based on log path
        # This prevents conflicts when multiple loggers exist (e.g., in tests)
        logger_name = f"debussy.orchestrator.events.{hash(str(self.log_path))}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers and add a fresh one for this path
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        # File handler for orchestrator events
        file_handler = logging.FileHandler(self.log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    # =========================================================================
    # Phase Events
    # =========================================================================

    def log_phase_start(
        self,
        phase_id: str,
        title: str,
        attempt: int = 1,
    ) -> None:
        """Log a phase start event.

        Args:
            phase_id: The phase identifier (e.g., "1", "2a").
            title: The phase title/description.
            attempt: The attempt number (1 for first try, >1 for retries).
        """
        self.logger.info(
            "[PHASE_START] phase=%s title=%r attempt=%d",
            phase_id,
            title,
            attempt,
        )

    def log_phase_stop(
        self,
        phase_id: str,
        status: PhaseStatus,
        duration_seconds: float,
    ) -> None:
        """Log a phase stop event.

        Args:
            phase_id: The phase identifier.
            status: The final phase status.
            duration_seconds: How long the phase execution took.
        """
        self.logger.info(
            "[PHASE_STOP] phase=%s status=%s duration=%.1fs",
            phase_id,
            status.value,
            duration_seconds,
        )

    def log_phase_skip(
        self,
        phase_id: str,
        reason: str,
    ) -> None:
        """Log when a phase is skipped.

        Args:
            phase_id: The phase identifier.
            reason: Why the phase was skipped (e.g., "dependencies not met", "already completed").
        """
        self.logger.info(
            "[PHASE_SKIP] phase=%s reason=%r",
            phase_id,
            reason,
        )

    def log_phase_rejection(
        self,
        phase_id: str,
        reason: str,
        issues: list[str] | None = None,
    ) -> None:
        """Log when a phase fails compliance checks.

        Args:
            phase_id: The phase identifier.
            reason: Summary of why the phase was rejected.
            issues: Optional list of specific compliance issues.
        """
        if issues:
            issues_str = "; ".join(issues[:5])  # Limit to 5 issues
            if len(issues) > 5:
                issues_str += f" (+{len(issues) - 5} more)"
            self.logger.warning(
                "[PHASE_REJECTION] phase=%s reason=%r issues=[%s]",
                phase_id,
                reason,
                issues_str,
            )
        else:
            self.logger.warning(
                "[PHASE_REJECTION] phase=%s reason=%r",
                phase_id,
                reason,
            )

    # =========================================================================
    # Commit Events
    # =========================================================================

    def log_commit(
        self,
        phase_id: str,
        message: str,
        files_changed: int,
    ) -> None:
        """Log an auto-commit action.

        Args:
            phase_id: The phase that triggered the commit.
            message: The commit message.
            files_changed: Number of files included in the commit.
        """
        self.logger.info(
            "[COMMIT] phase=%s message=%r files_changed=%d",
            phase_id,
            message,
            files_changed,
        )

    def log_commit_skipped(
        self,
        phase_id: str,
        reason: str,
    ) -> None:
        """Log when auto-commit is skipped.

        Args:
            phase_id: The phase identifier.
            reason: Why the commit was skipped (e.g., "no changes", "disabled").
        """
        self.logger.debug(
            "[COMMIT_SKIP] phase=%s reason=%r",
            phase_id,
            reason,
        )

    # =========================================================================
    # Configuration Events
    # =========================================================================

    def log_config(
        self,
        model: str,
        sandbox_mode: str,
        learnings_enabled: bool,
        auto_commit: bool,
        interactive: bool,
    ) -> None:
        """Log orchestrator configuration at startup.

        Args:
            model: The Claude model being used.
            sandbox_mode: Sandbox mode (none, devcontainer).
            learnings_enabled: Whether LTM learnings are enabled.
            auto_commit: Whether auto-commit is enabled.
            interactive: Whether running in interactive TUI mode.
        """
        self.logger.info(
            "[CONFIG] model=%s sandbox=%s learnings=%s auto_commit=%s interactive=%s",
            model,
            sandbox_mode,
            learnings_enabled,
            auto_commit,
            interactive,
        )

    def log_config_override(
        self,
        key: str,
        value: str,
        source: str = "cli",
    ) -> None:
        """Log a configuration override from CLI flags.

        Args:
            key: The configuration key being overridden.
            value: The new value.
            source: Where the override came from (cli, env, etc.).
        """
        self.logger.info(
            "[CONFIG_OVERRIDE] key=%s value=%r source=%s",
            key,
            value,
            source,
        )

    def log_run_init(
        self,
        run_id: str,
        plan_path: str,
        total_phases: int,
    ) -> None:
        """Log run initialization.

        Args:
            run_id: The unique run identifier.
            plan_path: Path to the master plan file.
            total_phases: Total number of phases in the plan.
        """
        self.logger.info(
            "[RUN_INIT] run_id=%s plan=%r phases=%d",
            run_id,
            plan_path,
            total_phases,
        )

    def log_run_complete(
        self,
        run_id: str,
        status: str,
        completed_phases: int,
        total_phases: int,
    ) -> None:
        """Log run completion.

        Args:
            run_id: The unique run identifier.
            status: Final run status (completed, failed, paused).
            completed_phases: Number of phases completed successfully.
            total_phases: Total number of phases in the plan.
        """
        self.logger.info(
            "[RUN_COMPLETE] run_id=%s status=%s completed=%d/%d",
            run_id,
            status,
            completed_phases,
            total_phases,
        )


# Module-level singleton
_orchestrator_logger: OrchestratorLogger | None = None


def get_orchestrator_logger(project_root: Path | None = None) -> OrchestratorLogger:
    """Get the orchestrator logger singleton.

    Args:
        project_root: Path to the project root. Required on first call,
            optional on subsequent calls (uses cached instance).

    Returns:
        The OrchestratorLogger instance.

    Raises:
        ValueError: If project_root is None and no logger has been initialized.
    """
    global _orchestrator_logger  # noqa: PLW0603

    if _orchestrator_logger is None:
        if project_root is None:
            raise ValueError("project_root is required when initializing the orchestrator logger")
        _orchestrator_logger = OrchestratorLogger(project_root)

    return _orchestrator_logger


def reset_orchestrator_logger() -> None:
    """Reset the orchestrator logger singleton (for testing only).

    WARNING: Only call this in test fixtures, never in production code.
    """
    global _orchestrator_logger  # noqa: PLW0603
    if _orchestrator_logger is not None:
        # Close any handlers
        for handler in _orchestrator_logger.logger.handlers[:]:
            handler.close()
            _orchestrator_logger.logger.removeHandler(handler)
    _orchestrator_logger = None
