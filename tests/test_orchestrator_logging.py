"""Unit tests for orchestrator logging functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from debussy.core.models import PhaseStatus
from debussy.logging.orchestrator_logger import (
    OrchestratorLogger,
    get_orchestrator_logger,
    reset_orchestrator_logger,
)


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root directory."""
    return tmp_path


@pytest.fixture
def orchestrator_logger(temp_project_root: Path) -> OrchestratorLogger:
    """Create an orchestrator logger for testing."""
    # Reset singleton to ensure clean state
    reset_orchestrator_logger()
    return OrchestratorLogger(temp_project_root)


@pytest.fixture(autouse=True)
def reset_logger_after_test():
    """Reset the orchestrator logger singleton after each test."""
    yield
    reset_orchestrator_logger()


class TestOrchestratorLoggerInitialization:
    """Tests for logger initialization."""

    def test_creates_log_directory(self, temp_project_root: Path) -> None:
        """Logger should create the log directory if it doesn't exist."""
        log_dir = temp_project_root / ".debussy" / "logs"
        assert not log_dir.exists()

        OrchestratorLogger(temp_project_root)

        assert log_dir.exists()

    def test_creates_log_file(self, temp_project_root: Path) -> None:
        """Logger should create the orchestrator.log file."""
        logger = OrchestratorLogger(temp_project_root)
        log_file = temp_project_root / ".debussy" / "logs" / "orchestrator.log"

        # Log something to trigger file creation
        logger.log_run_init("test123", "/path/to/plan.md", 5)

        assert log_file.exists()

    def test_log_path_attribute(self, temp_project_root: Path) -> None:
        """Logger should have correct log_path attribute."""
        logger = OrchestratorLogger(temp_project_root)
        expected_path = temp_project_root / ".debussy" / "logs" / "orchestrator.log"

        assert logger.log_path == expected_path


class TestGetOrchestratorLogger:
    """Tests for the singleton getter function."""

    def test_requires_project_root_on_first_call(self) -> None:
        """Should raise ValueError if project_root is None on first call."""
        reset_orchestrator_logger()

        with pytest.raises(ValueError, match="project_root is required"):
            get_orchestrator_logger(None)

    def test_returns_same_instance(self, temp_project_root: Path) -> None:
        """Should return the same instance on subsequent calls."""
        reset_orchestrator_logger()

        logger1 = get_orchestrator_logger(temp_project_root)
        logger2 = get_orchestrator_logger()  # No project_root needed

        assert logger1 is logger2

    def test_project_root_optional_after_init(self, temp_project_root: Path) -> None:
        """project_root should be optional after initialization."""
        reset_orchestrator_logger()

        get_orchestrator_logger(temp_project_root)
        # This should not raise
        logger = get_orchestrator_logger()

        assert logger is not None


class TestPhaseEventLogging:
    """Tests for phase start/stop event logging."""

    def test_log_phase_start(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase start event."""
        orchestrator_logger.log_phase_start("1", "Test Phase", 1)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[PHASE_START]" in log_content
        assert "phase=1" in log_content
        assert "title='Test Phase'" in log_content
        assert "attempt=1" in log_content

    def test_log_phase_start_with_retry(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase start with attempt number > 1 for retries."""
        orchestrator_logger.log_phase_start("2", "Retry Phase", 3)

        log_content = orchestrator_logger.log_path.read_text()
        assert "attempt=3" in log_content

    def test_log_phase_stop_completed(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase stop event with completed status."""
        orchestrator_logger.log_phase_stop("1", PhaseStatus.COMPLETED, 120.5)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[PHASE_STOP]" in log_content
        assert "phase=1" in log_content
        assert "status=completed" in log_content
        assert "duration=120.5s" in log_content

    def test_log_phase_stop_failed(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase stop event with failed status."""
        orchestrator_logger.log_phase_stop("1", PhaseStatus.FAILED, 45.0)

        log_content = orchestrator_logger.log_path.read_text()
        assert "status=failed" in log_content

    def test_log_phase_skip(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase skip event."""
        orchestrator_logger.log_phase_skip("2", "dependencies not met")

        log_content = orchestrator_logger.log_path.read_text()
        assert "[PHASE_SKIP]" in log_content
        assert "phase=2" in log_content
        assert "reason='dependencies not met'" in log_content

    def test_log_phase_rejection(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase rejection event."""
        orchestrator_logger.log_phase_rejection(
            "1",
            "compliance failed",
            ["Gate 'lint' failed", "Notes file missing"],
        )

        log_content = orchestrator_logger.log_path.read_text()
        assert "[PHASE_REJECTION]" in log_content
        assert "phase=1" in log_content
        assert "reason='compliance failed'" in log_content
        assert "Gate 'lint' failed" in log_content
        assert "Notes file missing" in log_content

    def test_log_phase_rejection_without_issues(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log phase rejection without issues list."""
        orchestrator_logger.log_phase_rejection("1", "max attempts reached")

        log_content = orchestrator_logger.log_path.read_text()
        assert "[PHASE_REJECTION]" in log_content
        assert "reason='max attempts reached'" in log_content
        # Should not have issues array
        assert "issues=" not in log_content

    def test_log_phase_rejection_limits_issues(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should limit issues to 5 in rejection log."""
        many_issues = [f"Issue {i}" for i in range(10)]
        orchestrator_logger.log_phase_rejection("1", "many failures", many_issues)

        log_content = orchestrator_logger.log_path.read_text()
        assert "(+5 more)" in log_content


class TestCommitEventLogging:
    """Tests for commit action logging."""

    def test_log_commit(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log successful commit event."""
        orchestrator_logger.log_commit("1", "feat(phase-1): implement feature X", 5)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[COMMIT]" in log_content
        assert "phase=1" in log_content
        assert "message='feat(phase-1): implement feature X'" in log_content
        assert "files_changed=5" in log_content

    def test_log_commit_skipped(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log commit skipped event."""
        orchestrator_logger.log_commit_skipped("1", "no changes")

        log_content = orchestrator_logger.log_path.read_text()
        assert "[COMMIT_SKIP]" in log_content
        assert "phase=1" in log_content
        assert "reason='no changes'" in log_content


class TestConfigurationLogging:
    """Tests for configuration event logging."""

    def test_log_config(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log orchestrator configuration at startup."""
        orchestrator_logger.log_config(
            model="opus",
            sandbox_mode="devcontainer",
            learnings_enabled=True,
            auto_commit=True,
            interactive=False,
        )

        log_content = orchestrator_logger.log_path.read_text()
        assert "[CONFIG]" in log_content
        assert "model=opus" in log_content
        assert "sandbox=devcontainer" in log_content
        assert "learnings=True" in log_content
        assert "auto_commit=True" in log_content
        assert "interactive=False" in log_content

    def test_log_config_override(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log configuration override."""
        orchestrator_logger.log_config_override("model", "haiku", "cli")

        log_content = orchestrator_logger.log_path.read_text()
        assert "[CONFIG_OVERRIDE]" in log_content
        assert "key=model" in log_content
        assert "value='haiku'" in log_content
        assert "source=cli" in log_content

    def test_log_run_init(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log run initialization."""
        orchestrator_logger.log_run_init("abc123", "/workspace/plans/feature/MASTER_PLAN.md", 5)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[RUN_INIT]" in log_content
        assert "run_id=abc123" in log_content
        assert "plan='/workspace/plans/feature/MASTER_PLAN.md'" in log_content
        assert "phases=5" in log_content

    def test_log_run_complete(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log run completion."""
        orchestrator_logger.log_run_complete("abc123", "completed", 5, 5)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[RUN_COMPLETE]" in log_content
        assert "run_id=abc123" in log_content
        assert "status=completed" in log_content
        assert "completed=5/5" in log_content

    def test_log_run_complete_partial(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Should log partial run completion (failure)."""
        orchestrator_logger.log_run_complete("xyz789", "failed", 2, 5)

        log_content = orchestrator_logger.log_path.read_text()
        assert "status=failed" in log_content
        assert "completed=2/5" in log_content


class TestLogFormatConsistency:
    """Tests for log format consistency with worker logs."""

    def test_log_format_has_timestamp(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Log entries should have ISO-style timestamp."""
        orchestrator_logger.log_run_init("test", "/path", 1)

        log_content = orchestrator_logger.log_path.read_text()
        # Check for timestamp format: YYYY-MM-DD HH:MM:SS
        import re

        timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, log_content) is not None

    def test_log_format_has_level(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Log entries should have log level."""
        orchestrator_logger.log_run_init("test", "/path", 1)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[INFO]" in log_content

    def test_log_format_warning_level(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Rejection logs should use WARNING level."""
        orchestrator_logger.log_phase_rejection("1", "test failure")

        log_content = orchestrator_logger.log_path.read_text()
        assert "[WARNING]" in log_content


class TestLogFileAppendBehavior:
    """Tests for log file append behavior."""

    def test_multiple_events_in_same_file(self, orchestrator_logger: OrchestratorLogger) -> None:
        """Multiple events should be appended to the same file."""
        orchestrator_logger.log_run_init("test", "/path", 3)
        orchestrator_logger.log_phase_start("1", "Phase 1", 1)
        orchestrator_logger.log_phase_stop("1", PhaseStatus.COMPLETED, 10.0)
        orchestrator_logger.log_phase_start("2", "Phase 2", 1)

        log_content = orchestrator_logger.log_path.read_text()
        assert "[RUN_INIT]" in log_content
        assert "Phase 1" in log_content
        assert "Phase 2" in log_content
        # Should have 4 log lines
        lines = [line for line in log_content.strip().split("\n") if line]
        assert len(lines) == 4

    def test_log_file_persists_across_logger_instances(self, temp_project_root: Path) -> None:
        """Log file should persist and append across logger instances."""
        # First logger instance
        logger1 = OrchestratorLogger(temp_project_root)
        logger1.log_run_init("run1", "/path1", 1)

        # Close handlers
        for handler in logger1.logger.handlers[:]:
            handler.close()
            logger1.logger.removeHandler(handler)

        # Second logger instance (simulating restart)
        logger2 = OrchestratorLogger(temp_project_root)
        logger2.log_run_init("run2", "/path2", 2)

        log_content = logger2.log_path.read_text()
        assert "run1" in log_content
        assert "run2" in log_content


class TestLogDirectoryCreation:
    """Tests for log directory creation when missing."""

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Should create nested .debussy/logs directory structure."""
        project_root = tmp_path / "deep" / "nested" / "project"
        project_root.mkdir(parents=True)

        logger = OrchestratorLogger(project_root)
        logger.log_run_init("test", "/path", 1)

        log_dir = project_root / ".debussy" / "logs"
        assert log_dir.exists()
        assert logger.log_path.exists()
