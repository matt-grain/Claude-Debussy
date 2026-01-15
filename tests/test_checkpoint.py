"""Tests for the checkpoint module."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from debussy.core.checkpoint import (
    MAX_FILES_IN_RESTART_CONTEXT,
    CheckpointManager,
    PhaseCheckpoint,
    ProgressEntry,
)


class TestProgressEntryDataclass:
    """Tests for ProgressEntry dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """ProgressEntry can be created with all required fields."""
        now = datetime.now()
        entry = ProgressEntry(
            timestamp=now,
            message="Completed task 1",
            phase_id="1",
        )
        assert entry.timestamp == now
        assert entry.message == "Completed task 1"
        assert entry.phase_id == "1"

    def test_fields_are_accessible(self) -> None:
        """All fields are accessible after creation."""
        entry = ProgressEntry(
            timestamp=datetime.now(),
            message="Test message",
            phase_id="test-phase",
        )
        assert hasattr(entry, "timestamp")
        assert hasattr(entry, "message")
        assert hasattr(entry, "phase_id")


class TestPhaseCheckpointDataclass:
    """Tests for PhaseCheckpoint dataclass."""

    def test_creation_with_minimal_fields(self) -> None:
        """PhaseCheckpoint can be created with minimal required fields."""
        checkpoint = PhaseCheckpoint(
            phase_id="1",
            phase_name="Setup Phase",
        )
        assert checkpoint.phase_id == "1"
        assert checkpoint.phase_name == "Setup Phase"
        assert checkpoint.start_commit is None
        assert checkpoint.progress_entries == []
        assert checkpoint.modified_files == []
        assert checkpoint.restart_count == 0

    def test_creation_with_all_fields(self) -> None:
        """PhaseCheckpoint can be created with all fields."""
        checkpoint = PhaseCheckpoint(
            phase_id="2",
            phase_name="Implementation Phase",
            start_commit="abc123",
            progress_entries=[],
            modified_files=["src/main.py"],
            restart_count=3,
        )
        assert checkpoint.phase_id == "2"
        assert checkpoint.phase_name == "Implementation Phase"
        assert checkpoint.start_commit == "abc123"
        assert checkpoint.modified_files == ["src/main.py"]
        assert checkpoint.restart_count == 3


class TestPhaseCheckpointAddProgress:
    """Tests for PhaseCheckpoint.add_progress() method."""

    def test_adds_progress_entry(self) -> None:
        """add_progress() adds a new progress entry."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.add_progress("Completed step 1")

        assert len(checkpoint.progress_entries) == 1
        assert checkpoint.progress_entries[0].message == "Completed step 1"
        assert checkpoint.progress_entries[0].phase_id == "1"

    def test_accumulates_multiple_entries(self) -> None:
        """add_progress() accumulates multiple entries."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.add_progress("Step 1")
        checkpoint.add_progress("Step 2")
        checkpoint.add_progress("Step 3")

        assert len(checkpoint.progress_entries) == 3
        assert checkpoint.progress_entries[0].message == "Step 1"
        assert checkpoint.progress_entries[1].message == "Step 2"
        assert checkpoint.progress_entries[2].message == "Step 3"

    def test_sets_timestamp_on_entry(self) -> None:
        """add_progress() sets timestamp on each entry."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        before = datetime.now()
        checkpoint.add_progress("Test step")
        after = datetime.now()

        entry = checkpoint.progress_entries[0]
        assert before <= entry.timestamp <= after


class TestPhaseCheckpointFormatRestartContext:
    """Tests for PhaseCheckpoint.format_restart_context() method."""

    def test_includes_warning_header(self) -> None:
        """format_restart_context() includes warning header."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test Phase")
        context = checkpoint.format_restart_context()

        assert "SESSION RESET" in context
        assert "Context limit reached" in context

    def test_includes_phase_info(self) -> None:
        """format_restart_context() includes phase ID and name."""
        checkpoint = PhaseCheckpoint(phase_id="3", phase_name="Build Phase")
        context = checkpoint.format_restart_context()

        assert "Phase: 3 - Build Phase" in context

    def test_includes_restart_count(self) -> None:
        """format_restart_context() includes restart count."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.restart_count = 5
        context = checkpoint.format_restart_context()

        assert "Restart attempt: 5" in context

    def test_includes_progress_entries_with_checkmarks(self) -> None:
        """format_restart_context() includes progress entries with checkmarks."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.add_progress("Created project structure")
        checkpoint.add_progress("Installed dependencies")
        context = checkpoint.format_restart_context()

        assert "Progress logged before reset:" in context
        assert "✓ Created project structure" in context
        assert "✓ Installed dependencies" in context

    def test_includes_modified_files(self) -> None:
        """format_restart_context() includes modified files list."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.modified_files = ["src/main.py", "pyproject.toml"]
        context = checkpoint.format_restart_context()

        assert "Files modified (do not recreate):" in context
        assert "- src/main.py" in context
        assert "- pyproject.toml" in context

    def test_limits_modified_files_to_max(self) -> None:
        """format_restart_context() limits file list to MAX_FILES_IN_RESTART_CONTEXT."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        # Add more than MAX_FILES_IN_RESTART_CONTEXT files
        checkpoint.modified_files = [f"file{i}.py" for i in range(25)]
        context = checkpoint.format_restart_context()

        # Should show first 20 and indicate more exist
        assert "file0.py" in context
        assert f"file{MAX_FILES_IN_RESTART_CONTEXT - 1}.py" in context
        assert "... and 5 more files" in context

    def test_includes_important_instructions(self) -> None:
        """format_restart_context() includes important instructions."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        context = checkpoint.format_restart_context()

        assert "IMPORTANT:" in context
        assert "Continue from where you stopped" in context
        assert "Do NOT redo completed work" in context
        assert "/debussy-progress" in context

    def test_handles_empty_checkpoint(self) -> None:
        """format_restart_context() handles checkpoint with no progress or files."""
        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        context = checkpoint.format_restart_context()

        # Should still have header and instructions
        assert "SESSION RESET" in context
        assert "IMPORTANT:" in context
        # Should not have progress or files sections
        assert "Progress logged before reset:" not in context
        assert "Files modified (do not recreate):" not in context


class TestPhaseCheckpointCaptureGitState:
    """Tests for PhaseCheckpoint.capture_git_state() method."""

    @patch("subprocess.run")
    def test_captures_modified_files(self, mock_run: MagicMock) -> None:
        """capture_git_state() captures modified files from git diff."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="src/main.py\npyproject.toml\nREADME.md\n",
        )

        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.capture_git_state(Path("/project"))

        assert checkpoint.modified_files == ["src/main.py", "pyproject.toml", "README.md"]

    @patch("subprocess.run")
    def test_handles_empty_diff(self, mock_run: MagicMock) -> None:
        """capture_git_state() handles case where no files are modified."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
        )

        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.capture_git_state(Path("/project"))

        assert checkpoint.modified_files == []

    @patch("subprocess.run")
    def test_handles_git_failure(self, mock_run: MagicMock) -> None:
        """capture_git_state() handles git command failure gracefully."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="fatal: not a git repository",
        )

        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.capture_git_state(Path("/project"))

        # Should not crash, modified_files stays empty
        assert checkpoint.modified_files == []

    @patch("subprocess.run")
    def test_handles_timeout(self, mock_run: MagicMock) -> None:
        """capture_git_state() handles subprocess timeout gracefully."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)

        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.capture_git_state(Path("/project"))

        # Should not crash
        assert checkpoint.modified_files == []

    @patch("subprocess.run")
    def test_handles_git_not_found(self, mock_run: MagicMock) -> None:
        """capture_git_state() handles git not being installed."""
        mock_run.side_effect = FileNotFoundError()

        checkpoint = PhaseCheckpoint(phase_id="1", phase_name="Test")
        checkpoint.capture_git_state(Path("/project"))

        # Should not crash
        assert checkpoint.modified_files == []


class TestCheckpointManagerInit:
    """Tests for CheckpointManager initialization."""

    def test_initializes_with_project_root(self) -> None:
        """CheckpointManager initializes with project root path."""
        manager = CheckpointManager(Path("/project"))
        assert manager.project_root == Path("/project")

    def test_starts_with_no_current_checkpoint(self) -> None:
        """CheckpointManager starts with no active checkpoint."""
        manager = CheckpointManager(Path("/project"))
        assert manager.get_current() is None


class TestCheckpointManagerStartPhase:
    """Tests for CheckpointManager.start_phase() method."""

    @patch("subprocess.run")
    def test_creates_new_checkpoint(self, mock_run: MagicMock) -> None:
        """start_phase() creates a new checkpoint."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        checkpoint = manager.start_phase("1", "Setup Phase")

        assert checkpoint.phase_id == "1"
        assert checkpoint.phase_name == "Setup Phase"

    @patch("subprocess.run")
    def test_captures_start_commit(self, mock_run: MagicMock) -> None:
        """start_phase() captures the current HEAD commit."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        checkpoint = manager.start_phase("1", "Test")

        assert checkpoint.start_commit == "abc123"

    @patch("subprocess.run")
    def test_sets_restart_count_to_zero(self, mock_run: MagicMock) -> None:
        """start_phase() initializes restart count to zero."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        checkpoint = manager.start_phase("1", "Test")

        assert checkpoint.restart_count == 0

    @patch("subprocess.run")
    def test_handles_git_not_available(self, mock_run: MagicMock) -> None:
        """start_phase() handles git not being available."""
        mock_run.side_effect = FileNotFoundError()

        manager = CheckpointManager(Path("/project"))
        checkpoint = manager.start_phase("1", "Test")

        assert checkpoint.start_commit is None
        assert checkpoint.phase_id == "1"


class TestCheckpointManagerGetCurrent:
    """Tests for CheckpointManager.get_current() method."""

    @patch("subprocess.run")
    def test_returns_active_checkpoint(self, mock_run: MagicMock) -> None:
        """get_current() returns the active checkpoint."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Test")

        current = manager.get_current()
        assert current is not None
        assert current.phase_id == "1"

    def test_returns_none_when_no_phase_started(self) -> None:
        """get_current() returns None when no phase has been started."""
        manager = CheckpointManager(Path("/project"))
        assert manager.get_current() is None


class TestCheckpointManagerRecordProgress:
    """Tests for CheckpointManager.record_progress() method."""

    @patch("subprocess.run")
    def test_adds_progress_to_current_checkpoint(self, mock_run: MagicMock) -> None:
        """record_progress() adds progress entry to current checkpoint."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Test")
        manager.record_progress("Completed step 1")

        current = manager.get_current()
        assert current is not None
        assert len(current.progress_entries) == 1
        assert current.progress_entries[0].message == "Completed step 1"

    @patch("subprocess.run")
    def test_accumulates_progress_entries(self, mock_run: MagicMock) -> None:
        """record_progress() accumulates multiple entries."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Test")
        manager.record_progress("Step 1")
        manager.record_progress("Step 2")
        manager.record_progress("Step 3")

        current = manager.get_current()
        assert current is not None
        assert len(current.progress_entries) == 3

    def test_handles_no_active_checkpoint(self) -> None:
        """record_progress() handles case where no checkpoint is active."""
        manager = CheckpointManager(Path("/project"))
        # Should not raise an exception
        manager.record_progress("Progress without checkpoint")

        assert manager.get_current() is None


class TestCheckpointManagerPrepareRestart:
    """Tests for CheckpointManager.prepare_restart() method."""

    @patch("subprocess.run")
    def test_returns_formatted_context(self, mock_run: MagicMock) -> None:
        """prepare_restart() returns formatted restart context."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Setup Phase")
        manager.record_progress("Created files")

        # Mock git diff for capture_git_state
        mock_run.return_value = MagicMock(returncode=0, stdout="src/main.py\n")

        context = manager.prepare_restart()

        assert "SESSION RESET" in context
        assert "Phase: 1 - Setup Phase" in context
        assert "Created files" in context

    @patch("subprocess.run")
    def test_increments_restart_count(self, mock_run: MagicMock) -> None:
        """prepare_restart() increments the restart count."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Test")

        manager.prepare_restart()
        current = manager.get_current()
        assert current is not None
        assert current.restart_count == 1

        manager.prepare_restart()
        assert current.restart_count == 2

    @patch("subprocess.run")
    def test_captures_git_state(self, mock_run: MagicMock) -> None:
        """prepare_restart() captures git state."""
        # First call for start_phase (git rev-parse)
        # Subsequent calls for capture_git_state (git diff)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="abc123\n"),  # rev-parse
            MagicMock(returncode=0, stdout="modified.py\n"),  # diff
        ]

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("1", "Test")

        context = manager.prepare_restart()
        assert "modified.py" in context

    def test_returns_empty_string_when_no_checkpoint(self) -> None:
        """prepare_restart() returns empty string when no checkpoint active."""
        manager = CheckpointManager(Path("/project"))
        context = manager.prepare_restart()
        assert context == ""


class TestCheckpointManagerGetHeadCommit:
    """Tests for CheckpointManager._get_head_commit() method."""

    @patch("subprocess.run")
    def test_returns_short_commit_hash(self, mock_run: MagicMock) -> None:
        """_get_head_commit() returns short commit hash."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        manager = CheckpointManager(Path("/project"))
        commit = manager._get_head_commit()

        assert commit == "abc123"

    @patch("subprocess.run")
    def test_returns_none_on_failure(self, mock_run: MagicMock) -> None:
        """_get_head_commit() returns None on git failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        manager = CheckpointManager(Path("/project"))
        commit = manager._get_head_commit()

        assert commit is None

    @patch("subprocess.run")
    def test_returns_none_on_timeout(self, mock_run: MagicMock) -> None:
        """_get_head_commit() returns None on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)

        manager = CheckpointManager(Path("/project"))
        commit = manager._get_head_commit()

        assert commit is None

    @patch("subprocess.run")
    def test_returns_none_when_git_not_found(self, mock_run: MagicMock) -> None:
        """_get_head_commit() returns None when git not found."""
        mock_run.side_effect = FileNotFoundError()

        manager = CheckpointManager(Path("/project"))
        commit = manager._get_head_commit()

        assert commit is None


class TestCheckpointModuleConstants:
    """Tests for module constants."""

    def test_max_files_in_restart_context(self) -> None:
        """MAX_FILES_IN_RESTART_CONTEXT is 20."""
        assert MAX_FILES_IN_RESTART_CONTEXT == 20


class TestCheckpointIntegration:
    """Integration tests for checkpoint functionality."""

    @patch("subprocess.run")
    def test_full_workflow(self, mock_run: MagicMock) -> None:
        """Test full checkpoint workflow from start to restart."""
        # Mock git commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="start123\n"),  # start_phase rev-parse
            MagicMock(returncode=0, stdout="file1.py\nfile2.py\n"),  # prepare_restart diff
        ]

        manager = CheckpointManager(Path("/project"))

        # Start phase
        checkpoint = manager.start_phase("1", "Implementation")
        assert checkpoint.start_commit == "start123"
        assert checkpoint.restart_count == 0

        # Record progress
        manager.record_progress("Created base structure")
        manager.record_progress("Added core functionality")
        manager.record_progress("Wrote initial tests")

        # Prepare restart
        context = manager.prepare_restart()

        # Verify context contains all expected elements
        assert "SESSION RESET" in context
        assert "Phase: 1 - Implementation" in context
        assert "Restart attempt: 1" in context
        assert "Created base structure" in context
        assert "Added core functionality" in context
        assert "Wrote initial tests" in context
        assert "file1.py" in context
        assert "file2.py" in context
        assert "Do NOT redo completed work" in context

    @patch("subprocess.run")
    def test_checkpoint_with_no_progress_only_git_diff(self, mock_run: MagicMock) -> None:
        """Test checkpoint that has no progress entries but captures git state."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="abc123\n"),  # rev-parse
            MagicMock(returncode=0, stdout="modified.py\nnew.py\n"),  # diff
        ]

        manager = CheckpointManager(Path("/project"))
        manager.start_phase("2", "Bug Fixes")

        # No progress recorded
        context = manager.prepare_restart()

        # Should still have useful information
        assert "Phase: 2 - Bug Fixes" in context
        assert "modified.py" in context
        assert "Progress logged before reset:" not in context  # No progress entries
