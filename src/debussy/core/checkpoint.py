"""Progress checkpoint tracking for phase restarts.

Captures progress during phase execution so restarts can continue from
where they left off. Tracks progress entries from /debussy-progress skill
calls, captures git state (modified files, diffs), and formats readable
restart context.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
MAX_FILES_IN_RESTART_CONTEXT = 20


@dataclass
class ProgressEntry:
    """A single progress log entry from /debussy-progress."""

    timestamp: datetime
    message: str
    phase_id: str


@dataclass
class PhaseCheckpoint:
    """Checkpoint data for a phase execution.

    Captures progress entries, git state, and restart count to enable
    context-aware restarts when sessions hit context limits.
    """

    phase_id: str
    phase_name: str
    start_commit: str | None = None
    progress_entries: list[ProgressEntry] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    restart_count: int = 0

    def add_progress(self, message: str) -> None:
        """Add a progress entry to the checkpoint.

        Args:
            message: The progress message from /debussy-progress
        """
        entry = ProgressEntry(
            timestamp=datetime.now(),
            message=message,
            phase_id=self.phase_id,
        )
        self.progress_entries.append(entry)
        logger.debug(f"Checkpoint: added progress entry '{message}'")

    def capture_git_state(self, project_root: Path) -> None:
        """Capture current git state (modified files).

        Uses `git diff --name-only` to get list of modified files.
        Gracefully handles git command failures.

        Args:
            project_root: Project root directory for git commands
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                # Parse file list, filter empty lines
                files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
                self.modified_files = files
                logger.debug(f"Checkpoint: captured {len(files)} modified files")
            else:
                logger.warning(f"Git diff failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.warning("Git diff timed out")
        except FileNotFoundError:
            logger.warning("Git not available for state capture")
        except OSError as e:
            logger.warning(f"Git command error: {e}")

    def format_restart_context(self) -> str:
        """Format checkpoint data for restart prompt injection.

        Creates a human-readable summary of progress and modified files
        to help Claude continue from where the previous session left off.

        Returns:
            Formatted restart context string
        """
        lines: list[str] = []

        # Header with warning
        lines.append("⚠️ SESSION RESET: Context limit reached, fresh session started.")
        lines.append(f"Phase: {self.phase_id} - {self.phase_name}")
        lines.append(f"Restart attempt: {self.restart_count}")
        lines.append("")

        # Progress entries (if any)
        if self.progress_entries:
            lines.append("Progress logged before reset:")
            for entry in self.progress_entries:
                lines.append(f"  ✓ {entry.message}")
            lines.append("")

        # Modified files (limited to MAX_FILES_IN_RESTART_CONTEXT)
        if self.modified_files:
            lines.append("Files modified (do not recreate):")
            files_to_show = self.modified_files[:MAX_FILES_IN_RESTART_CONTEXT]
            for f in files_to_show:
                lines.append(f"  - {f}")
            if len(self.modified_files) > MAX_FILES_IN_RESTART_CONTEXT:
                remaining = len(self.modified_files) - MAX_FILES_IN_RESTART_CONTEXT
                lines.append(f"  ... and {remaining} more files")
            lines.append("")

        # Important instructions
        lines.append("IMPORTANT:")
        lines.append("- Continue from where you stopped")
        lines.append("- Do NOT redo completed work")
        lines.append("- Review modified files to understand current state")
        lines.append("- Use /debussy-progress to log significant progress")

        return "\n".join(lines)


class CheckpointManager:
    """Manages checkpoints for phase executions.

    Provides methods to start checkpoints, record progress, and prepare
    restart context when sessions need to be restarted due to context limits.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize the checkpoint manager.

        Args:
            project_root: Project root directory for git commands
        """
        self.project_root = project_root
        self._current: PhaseCheckpoint | None = None

    def start_phase(self, phase_id: str, phase_name: str) -> PhaseCheckpoint:
        """Initialize a checkpoint for a new phase execution.

        Captures the current HEAD commit for reference and creates
        a fresh checkpoint.

        Args:
            phase_id: The phase identifier
            phase_name: Human-readable phase name

        Returns:
            The initialized PhaseCheckpoint
        """
        start_commit = self._get_head_commit()

        self._current = PhaseCheckpoint(
            phase_id=phase_id,
            phase_name=phase_name,
            start_commit=start_commit,
            restart_count=0,
        )

        logger.debug(f"Checkpoint: started phase {phase_id} at commit {start_commit or 'unknown'}")
        return self._current

    def get_current(self) -> PhaseCheckpoint | None:
        """Get the current active checkpoint.

        Returns:
            Current PhaseCheckpoint or None if no phase is active
        """
        return self._current

    def record_progress(self, message: str) -> None:
        """Add a progress entry to the current checkpoint.

        Args:
            message: The progress message from /debussy-progress

        Raises:
            RuntimeError: If no phase is currently active
        """
        if self._current is None:
            logger.warning("Attempted to record progress with no active checkpoint")
            return

        self._current.add_progress(message)
        logger.debug(f"Checkpoint: recorded progress '{message}'")

    def prepare_restart(self) -> str:
        """Capture git state and format restart context.

        Call this when preparing to restart a session due to context limits.
        Increments the restart count and captures current git state.

        Returns:
            Formatted restart context string, or empty string if no checkpoint
        """
        if self._current is None:
            logger.warning("Attempted to prepare restart with no active checkpoint")
            return ""

        # Increment restart count
        self._current.restart_count += 1

        # Capture current git state
        self._current.capture_git_state(self.project_root)

        # Format and return context
        context = self._current.format_restart_context()
        logger.info(f"Checkpoint: prepared restart context (attempt {self._current.restart_count})")

        return context

    def _get_head_commit(self) -> str | None:
        """Get the current HEAD commit hash.

        Returns:
            Short commit hash or None if git unavailable/failed
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.debug(f"git rev-parse failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.warning("git rev-parse timed out")
            return None
        except FileNotFoundError:
            logger.debug("Git not available")
            return None
        except OSError as e:
            logger.warning(f"Git command error: {e}")
            return None
