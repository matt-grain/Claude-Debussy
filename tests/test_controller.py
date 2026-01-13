"""Unit tests for OrchestrationController business logic.

This tests the full controller implementation added in PR #2.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from debussy.ui.base import UIState, UserAction
from debussy.ui.controller import OrchestrationController
from debussy.ui.messages import (
    HUDMessageSet,
    LogMessage,
    OrchestrationCompleted,
    OrchestrationStarted,
    PhaseChanged,
    StateChanged,
    TokenStatsUpdated,
    VerboseToggled,
)


class TestOrchestrationLifecycle:
    """Test orchestration lifecycle methods."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app that captures posted messages."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_start_initializes_context(self, controller: OrchestrationController) -> None:
        """start() should initialize all context fields."""
        controller.start("test-plan", 5)

        assert controller.context.plan_name == "test-plan"
        assert controller.context.total_phases == 5
        assert controller.context.state == UIState.RUNNING
        assert controller.context.start_time > 0

    def test_start_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """start() should emit OrchestrationStarted message."""
        controller.start("test-plan", 5)

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, OrchestrationStarted)
        assert msg.plan_name == "test-plan"
        assert msg.total_phases == 5

    def test_stop_is_no_op(self, controller: OrchestrationController) -> None:
        """stop() should be a no-op (doesn't raise or change state)."""
        controller.context.state = UIState.RUNNING
        controller.stop()
        # State should not change
        assert controller.context.state == UIState.RUNNING

    def test_set_phase_updates_context(self, controller: OrchestrationController) -> None:
        """set_phase() should update all phase-related context."""
        mock_phase = Mock()
        mock_phase.id = "phase-1"
        mock_phase.title = "Setup Phase"
        controller.context.total_phases = 3

        controller.set_phase(mock_phase, 1)

        assert controller.context.current_phase == "phase-1"
        assert controller.context.phase_title == "Setup Phase"
        assert controller.context.phase_index == 1
        assert controller.context.start_time > 0

    def test_set_phase_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """set_phase() should emit PhaseChanged message."""
        mock_phase = Mock()
        mock_phase.id = "phase-2"
        mock_phase.title = "Build Phase"
        controller.context.total_phases = 4

        controller.set_phase(mock_phase, 2)

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, PhaseChanged)
        assert msg.phase_id == "phase-2"
        assert msg.phase_title == "Build Phase"
        assert msg.phase_index == 2
        assert msg.total_phases == 4

    def test_set_state_updates_context(self, controller: OrchestrationController) -> None:
        """set_state() should update the UI state."""
        controller.set_state(UIState.PAUSED)

        assert controller.context.state == UIState.PAUSED

    def test_set_state_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """set_state() should emit StateChanged message."""
        controller.set_state(UIState.WAITING_INPUT)

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, StateChanged)
        assert msg.state == UIState.WAITING_INPUT

    def test_complete_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """complete() should emit OrchestrationCompleted message."""
        controller.complete("run-123", True, "All done!")

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, OrchestrationCompleted)
        assert msg.run_id == "run-123"
        assert msg.success is True
        assert msg.message == "All done!"

    def test_complete_with_failure(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """complete() should handle failure case."""
        controller.complete("run-456", False, "Phase 2 failed")

        msg = mock_app.posted_messages[0]
        assert msg.success is False
        assert msg.message == "Phase 2 failed"


class TestTokenStatistics:
    """Test token tracking and accumulation."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_update_token_stats_session_tracking(self, controller: OrchestrationController) -> None:
        """update_token_stats() should update session stats."""
        controller.update_token_stats(
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.0,  # No cost means intermediate update
            context_tokens=150,
            context_window=200_000,
        )

        assert controller.context.session_input_tokens == 100
        assert controller.context.session_output_tokens == 50
        assert controller.context.current_context_tokens == 150
        assert controller.context.context_window == 200_000

    def test_update_token_stats_no_accumulation_without_cost(
        self, controller: OrchestrationController
    ) -> None:
        """Intermediate updates (cost=0) should not accumulate totals."""
        controller.update_token_stats(100, 50, 0.0, 100, 200_000)

        assert controller.context.total_input_tokens == 0
        assert controller.context.total_output_tokens == 0
        assert controller.context.total_cost_usd == 0.0

    def test_update_token_stats_accumulation_with_cost(
        self, controller: OrchestrationController
    ) -> None:
        """Final updates (cost>0) should accumulate to totals."""
        controller.update_token_stats(100, 50, 0.05, 100, 200_000)

        assert controller.context.total_input_tokens == 100
        assert controller.context.total_output_tokens == 50
        assert controller.context.total_cost_usd == 0.05

    def test_update_token_stats_multiple_accumulation(
        self, controller: OrchestrationController
    ) -> None:
        """Multiple final updates should accumulate correctly."""
        # First final update
        controller.update_token_stats(100, 50, 0.05, 100, 200_000)
        # Second final update
        controller.update_token_stats(200, 100, 0.10, 200, 200_000)

        assert controller.context.total_input_tokens == 300
        assert controller.context.total_output_tokens == 150
        assert controller.context.total_cost_usd == pytest.approx(0.15)

    def test_update_token_stats_context_percentage(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """Context percentage should be calculated correctly."""
        controller.update_token_stats(1000, 500, 0.0, 50_000, 200_000)

        msg = mock_app.posted_messages[0]
        assert isinstance(msg, TokenStatsUpdated)
        assert msg.context_pct == 25  # 50_000 / 200_000 * 100

    def test_update_token_stats_context_percentage_zero_context(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """Context percentage should be 0 when context_tokens is 0."""
        controller.update_token_stats(100, 50, 0.0, 0, 200_000)

        msg = mock_app.posted_messages[0]
        assert msg.context_pct == 0

    def test_update_token_stats_context_percentage_zero_window(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """Context percentage should be 0 when context_window is 0."""
        controller.update_token_stats(100, 50, 0.0, 100, 0)

        msg = mock_app.posted_messages[0]
        assert msg.context_pct == 0

    def test_update_token_stats_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """update_token_stats() should emit TokenStatsUpdated message."""
        controller.update_token_stats(1000, 500, 0.05, 1500, 200_000)

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, TokenStatsUpdated)
        # session_input_tokens is input + output combined
        assert msg.session_input_tokens == 1500
        assert msg.session_output_tokens == 500
        assert msg.total_cost_usd == 0.05


class TestUserActions:
    """Test user action queue management."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_queue_action_adds_to_queue(self, controller: OrchestrationController) -> None:
        """queue_action() should add action to the queue."""
        controller.queue_action(UserAction.PAUSE)

        assert len(controller._action_queue) == 1
        assert controller._action_queue[0] == UserAction.PAUSE

    def test_queue_action_fifo_order(self, controller: OrchestrationController) -> None:
        """Action queue should be FIFO."""
        controller.queue_action(UserAction.PAUSE)
        controller.queue_action(UserAction.SKIP)
        controller.queue_action(UserAction.RESUME)

        assert controller.get_pending_action() == UserAction.PAUSE
        assert controller.get_pending_action() == UserAction.SKIP
        assert controller.get_pending_action() == UserAction.RESUME

    def test_queue_action_emits_feedback_pause(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """queue_action(PAUSE) should emit feedback message."""
        controller.queue_action(UserAction.PAUSE)

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, HUDMessageSet)
        assert "Pause" in msg.message

    def test_queue_action_emits_feedback_resume(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """queue_action(RESUME) should emit feedback message."""
        controller.queue_action(UserAction.RESUME)

        msg = mock_app.posted_messages[0]
        assert "Resume" in msg.message

    def test_queue_action_emits_feedback_skip(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """queue_action(SKIP) should emit feedback message."""
        controller.queue_action(UserAction.SKIP)

        msg = mock_app.posted_messages[0]
        assert "Skip" in msg.message

    def test_queue_action_emits_feedback_quit(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """queue_action(QUIT) should emit feedback message."""
        controller.queue_action(UserAction.QUIT)

        msg = mock_app.posted_messages[0]
        assert "Quit" in msg.message

    def test_queue_action_no_feedback_for_status(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """queue_action(STATUS) should not emit feedback."""
        controller.queue_action(UserAction.STATUS)

        assert len(mock_app.posted_messages) == 0

    def test_get_pending_action_returns_none_when_empty(
        self, controller: OrchestrationController
    ) -> None:
        """get_pending_action() should return NONE when queue is empty."""
        action = controller.get_pending_action()

        assert action == UserAction.NONE

    def test_get_pending_action_updates_last_action(
        self, controller: OrchestrationController
    ) -> None:
        """get_pending_action() should update context.last_action."""
        controller.queue_action(UserAction.PAUSE)

        controller.get_pending_action()

        assert controller.context.last_action == UserAction.PAUSE

    def test_get_pending_action_removes_from_queue(
        self, controller: OrchestrationController
    ) -> None:
        """get_pending_action() should remove action from queue."""
        controller.queue_action(UserAction.PAUSE)

        controller.get_pending_action()

        assert len(controller._action_queue) == 0


class TestVerboseToggle:
    """Test verbose mode toggling."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_toggle_verbose_flips_state(self, controller: OrchestrationController) -> None:
        """toggle_verbose() should flip the verbose state."""
        assert controller.context.verbose is True  # Default

        result = controller.toggle_verbose()

        assert result is False
        assert controller.context.verbose is False

    def test_toggle_verbose_flips_back(self, controller: OrchestrationController) -> None:
        """toggle_verbose() called twice should restore state."""
        controller.toggle_verbose()
        controller.toggle_verbose()

        assert controller.context.verbose is True

    def test_toggle_verbose_emits_verbose_toggled(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """toggle_verbose() should emit VerboseToggled message."""
        controller.toggle_verbose()

        verbose_msgs = [m for m in mock_app.posted_messages if isinstance(m, VerboseToggled)]
        assert len(verbose_msgs) == 1
        assert verbose_msgs[0].is_verbose is False

    def test_toggle_verbose_emits_hud_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """toggle_verbose() should emit HUD feedback message."""
        controller.toggle_verbose()

        hud_msgs = [m for m in mock_app.posted_messages if isinstance(m, HUDMessageSet)]
        assert len(hud_msgs) == 1
        assert "Verbose: OFF" in hud_msgs[0].message

    def test_toggle_verbose_on_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """toggle_verbose() should show ON when turning verbose on."""
        controller.context.verbose = False

        controller.toggle_verbose()

        hud_msgs = [m for m in mock_app.posted_messages if isinstance(m, HUDMessageSet)]
        assert "Verbose: ON" in hud_msgs[0].message


class TestLogging:
    """Test logging methods."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_log_message_emits_non_raw(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """log_message() should emit LogMessage with raw=False."""
        controller.log_message("test message")

        assert len(mock_app.posted_messages) == 1
        msg = mock_app.posted_messages[0]
        assert isinstance(msg, LogMessage)
        assert msg.message == "test message"
        assert msg.raw is False

    def test_log_message_raw_emits_raw(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """log_message_raw() should emit LogMessage with raw=True."""
        controller.log_message_raw("important message")

        msg = mock_app.posted_messages[0]
        assert msg.message == "important message"
        assert msg.raw is True


class TestStatus:
    """Test status-related methods."""

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_show_status_popup_emits_header(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """show_status_popup() should emit header message."""
        controller.show_status_popup({"Key": "Value"})

        messages = [m.message for m in mock_app.posted_messages if isinstance(m, LogMessage)]
        assert any("Current Status" in m for m in messages)

    def test_show_status_popup_emits_details(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """show_status_popup() should emit all detail lines."""
        controller.show_status_popup({"Phase": "Setup", "Progress": "50%"})

        messages = [m.message for m in mock_app.posted_messages if isinstance(m, LogMessage)]
        assert any("Phase: Setup" in m for m in messages)
        assert any("Progress: 50%" in m for m in messages)

    def test_show_status_popup_all_raw(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """show_status_popup() messages should all be raw."""
        controller.show_status_popup({"Key": "Value"})

        log_msgs = [m for m in mock_app.posted_messages if isinstance(m, LogMessage)]
        assert all(m.raw is True for m in log_msgs)

    def test_confirm_returns_true(self, controller: OrchestrationController) -> None:
        """confirm() should always return True (auto-confirm)."""
        result = controller.confirm("Proceed?")

        assert result is True

    def test_confirm_emits_message(
        self, controller: OrchestrationController, mock_app: MagicMock
    ) -> None:
        """confirm() should emit confirmation message."""
        controller.confirm("Delete all files?")

        msg = mock_app.posted_messages[0]
        assert isinstance(msg, LogMessage)
        assert "Delete all files?" in msg.message
        assert "auto-confirmed" in msg.message
        assert msg.raw is True


# =============================================================================
# PR #3: Controller Integration Tests
# =============================================================================


class TestControllerIntegration:
    """Test controller integration with DebussyTUI (PR #3).

    These tests verify the dual-mode bridge pattern where TUI methods
    delegate to the controller when one is set.
    """

    @pytest.fixture
    def mock_app(self) -> MagicMock:
        """Create a mock Textual app."""
        app = MagicMock()
        app.posted_messages = []
        app.post_message = lambda msg: app.posted_messages.append(msg)
        return app

    @pytest.fixture
    def controller(self, mock_app: MagicMock) -> OrchestrationController:
        """Create a controller with mock app."""
        return OrchestrationController(mock_app)

    def test_set_controller_syncs_context(self) -> None:
        """set_controller() should sync ui_context to controller's context."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)

        app.set_controller(controller)

        # Both should reference the same context object
        assert app.ui_context is controller.context

    def test_textual_ui_creates_controller(self) -> None:
        """TextualUI.create_app() should create and inject controller."""
        from debussy.ui.tui import TextualUI

        ui = TextualUI()
        app = ui.create_app()

        assert ui._controller is not None
        assert app._controller is ui._controller

    def test_textual_ui_context_from_controller(self) -> None:
        """TextualUI.context should return controller's context."""
        from debussy.ui.tui import TextualUI

        ui = TextualUI()
        ui.create_app()

        # Should return controller's context
        assert ui._controller is not None
        assert ui.context is ui._controller.context

    def test_start_delegates_to_controller(self) -> None:
        """start() should delegate to controller when set."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        # Mock update_hud and write_log to avoid Textual widget queries
        with patch.object(app, "update_hud"), patch.object(app, "write_log"):
            app.start("test-plan", 5)

        mock_controller.start.assert_called_once_with("test-plan", 5)

    def test_set_phase_delegates_to_controller(self) -> None:
        """set_phase() should delegate to controller when set."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        mock_phase = Mock()
        mock_phase.id = "p1"
        mock_phase.title = "Test"

        with patch.object(app, "update_hud"):
            app.set_phase(mock_phase, 1)

        mock_controller.set_phase.assert_called_once_with(mock_phase, 1)

    def test_set_state_delegates_to_controller(self) -> None:
        """set_state() should delegate to controller when set."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        with patch.object(app, "update_hud"):
            app.set_state(UIState.PAUSED)

        mock_controller.set_state.assert_called_once_with(UIState.PAUSED)

    def test_get_pending_action_delegates_to_controller(self) -> None:
        """get_pending_action() should delegate to controller when set."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        mock_controller.get_pending_action.return_value = UserAction.PAUSE
        app.set_controller(mock_controller)

        result = app.get_pending_action()

        assert result == UserAction.PAUSE
        mock_controller.get_pending_action.assert_called_once()

    def test_toggle_verbose_delegates_to_controller(self) -> None:
        """toggle_verbose() should delegate to controller when set."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        mock_controller.toggle_verbose.return_value = False
        app.set_controller(mock_controller)

        with patch.object(app, "update_hud"):
            result = app.toggle_verbose()

        assert result is False
        mock_controller.toggle_verbose.assert_called_once()

    def test_update_token_stats_delegates_to_controller(self) -> None:
        """update_token_stats() should delegate to controller when set."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        with patch.object(app, "update_hud"):
            app.update_token_stats(100, 50, 0.05, 150, 200_000)

        mock_controller.update_token_stats.assert_called_once_with(100, 50, 0.05, 150, 200_000)


class TestControllerIntegrationActions:
    """Test action handler delegation to controller (PR #3)."""

    def test_action_toggle_pause_delegates_pause(self) -> None:
        """action_toggle_pause() should queue PAUSE via controller when running."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        mock_controller.context.state = UIState.RUNNING
        app.set_controller(mock_controller)

        with patch.object(app, "set_timer"):
            app.action_toggle_pause()

        mock_controller.queue_action.assert_called_once_with(UserAction.PAUSE)

    def test_action_toggle_pause_delegates_resume(self) -> None:
        """action_toggle_pause() should queue RESUME via controller when paused."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        mock_controller.context.state = UIState.PAUSED
        app.set_controller(mock_controller)

        with patch.object(app, "set_timer"):
            app.action_toggle_pause()

        mock_controller.queue_action.assert_called_once_with(UserAction.RESUME)

    def test_action_toggle_verbose_delegates(self) -> None:
        """action_toggle_verbose() should call controller.toggle_verbose()."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        with patch.object(app, "set_timer"):
            app.action_toggle_verbose()

        mock_controller.toggle_verbose.assert_called_once()

    def test_action_skip_phase_delegates(self) -> None:
        """action_skip_phase() should queue SKIP via controller."""
        from unittest.mock import patch

        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_controller = MagicMock()
        mock_controller.context = MagicMock()
        app.set_controller(mock_controller)

        with patch.object(app, "set_timer"):
            app.action_skip_phase()

        mock_controller.queue_action.assert_called_once_with(UserAction.SKIP)


class TestControllerRequired:
    """Test that controller is required (PR #5)."""

    def test_ui_context_raises_without_controller(self) -> None:
        """ui_context should raise RuntimeError without controller."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with pytest.raises(RuntimeError, match="Controller not set"):
            _ = app.ui_context

    def test_start_raises_without_controller(self) -> None:
        """start() should raise RuntimeError without controller."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with pytest.raises(RuntimeError, match="Controller not set"):
            app.start("test-plan", 3)

    def test_set_phase_raises_without_controller(self) -> None:
        """set_phase() should raise RuntimeError without controller."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        mock_phase = Mock()
        mock_phase.id = "p1"
        mock_phase.title = "Setup"

        with pytest.raises(RuntimeError, match="Controller not set"):
            app.set_phase(mock_phase, 1)

    def test_get_pending_action_raises_without_controller(self) -> None:
        """get_pending_action() should raise RuntimeError without controller."""
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with pytest.raises(RuntimeError, match="Controller not set"):
            app.get_pending_action()


# =============================================================================
# PR #4: TUI Message Handler Tests
# =============================================================================


class TestTUIMessageHandlers:
    """Test TUI message handlers (PR #4).

    These tests verify that the TUI correctly handles messages emitted by
    the OrchestrationController.
    """

    def test_on_orchestration_started_updates_hud(self) -> None:
        """on_orchestration_started() should update HUD phase info."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import OrchestrationStarted
        from debussy.ui.tui import DebussyTUI, HUDHeader

        app = DebussyTUI()
        mock_header = MagicMock(spec=HUDHeader)

        with patch.object(app, "query_one", return_value=mock_header):
            message = OrchestrationStarted("test-plan", 5)
            app.on_orchestration_started(message)

        assert mock_header.phase_info == "0/5: Starting..."

    def test_on_phase_changed_updates_hud(self) -> None:
        """on_phase_changed() should update HUD with phase info."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import PhaseChanged
        from debussy.ui.tui import DebussyTUI, HUDHeader

        app = DebussyTUI()
        mock_header = MagicMock(spec=HUDHeader)

        with patch.object(app, "query_one", return_value=mock_header):
            message = PhaseChanged(
                phase_id="phase-1",
                phase_title="Setup Phase",
                phase_index=2,
                total_phases=5,
            )
            app.on_phase_changed(message)

        assert mock_header.phase_info == "2/5: Setup Phase"

    def test_on_state_changed_updates_hud_running(self) -> None:
        """on_state_changed() should update HUD status for RUNNING state."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import StateChanged
        from debussy.ui.tui import DebussyTUI, HUDHeader

        app = DebussyTUI()
        mock_header = MagicMock(spec=HUDHeader)

        with patch.object(app, "query_one", return_value=mock_header):
            message = StateChanged(UIState.RUNNING)
            app.on_state_changed(message)

        assert mock_header.status == "Running"
        assert mock_header.status_style == "green"

    def test_on_state_changed_updates_hud_paused(self) -> None:
        """on_state_changed() should update HUD status for PAUSED state."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import StateChanged
        from debussy.ui.tui import DebussyTUI, HUDHeader

        app = DebussyTUI()
        mock_header = MagicMock(spec=HUDHeader)

        with patch.object(app, "query_one", return_value=mock_header):
            message = StateChanged(UIState.PAUSED)
            app.on_state_changed(message)

        assert mock_header.status == "Paused"
        assert mock_header.status_style == "yellow"

    def test_on_token_stats_updated_updates_hud(self) -> None:
        """on_token_stats_updated() should update HUD token display."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import TokenStatsUpdated
        from debussy.ui.tui import DebussyTUI, HUDHeader

        app = DebussyTUI()
        mock_header = MagicMock(spec=HUDHeader)

        with patch.object(app, "query_one", return_value=mock_header):
            message = TokenStatsUpdated(
                session_input_tokens=1500,
                session_output_tokens=500,
                total_cost_usd=0.15,
                context_pct=25,
            )
            app.on_token_stats_updated(message)

        assert mock_header.total_tokens == 1500
        assert mock_header.cost_usd == 0.15
        assert mock_header.context_pct == 25

    def test_on_log_message_raw_always_writes(self) -> None:
        """on_log_message() with raw=True should always write to log."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import LogMessage
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)
        controller.context.verbose = False  # Verbose OFF

        with patch.object(app, "write_log") as mock_write:
            message = LogMessage("Important message", raw=True)
            app.on_log_message(message)

        mock_write.assert_called_once_with("Important message")

    def test_on_log_message_respects_verbose_on(self) -> None:
        """on_log_message() with raw=False should respect verbose=True."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import LogMessage
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)
        controller.context.verbose = True  # Verbose ON

        with patch.object(app, "write_log") as mock_write:
            message = LogMessage("Debug message", raw=False)
            app.on_log_message(message)

        mock_write.assert_called_once_with("Debug message")

    def test_on_log_message_respects_verbose_off(self) -> None:
        """on_log_message() with raw=False should respect verbose=False."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import LogMessage
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)
        controller.context.verbose = False  # Verbose OFF

        with patch.object(app, "write_log") as mock_write:
            message = LogMessage("Debug message", raw=False)
            app.on_log_message(message)

        mock_write.assert_not_called()

    def test_on_hud_message_set_shows_message(self) -> None:
        """on_hud_message_set() should show message in HUD."""
        from unittest.mock import patch

        from debussy.ui.messages import HUDMessageSet
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with (
            patch.object(app, "set_hud_message") as mock_set,
            patch.object(app, "set_timer") as mock_timer,
        ):
            message = HUDMessageSet("Pause requested", clear_after=3.0)
            app.on_hud_message_set(message)

        mock_set.assert_called_once_with("Pause requested")
        mock_timer.assert_called_once()

    def test_on_hud_message_set_no_clear_when_zero(self) -> None:
        """on_hud_message_set() should not set timer when clear_after=0."""
        from unittest.mock import patch

        from debussy.ui.messages import HUDMessageSet
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with (
            patch.object(app, "set_hud_message") as mock_set,
            patch.object(app, "set_timer") as mock_timer,
        ):
            message = HUDMessageSet("Persistent message", clear_after=0)
            app.on_hud_message_set(message)

        mock_set.assert_called_once_with("Persistent message")
        mock_timer.assert_not_called()

    def test_on_verbose_toggled_updates_hotkey_bar(self) -> None:
        """on_verbose_toggled() should update hotkey bar verbose state."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import VerboseToggled
        from debussy.ui.tui import DebussyTUI, HotkeyBar

        app = DebussyTUI()
        mock_hotkey_bar = MagicMock(spec=HotkeyBar)

        with patch.object(app, "query_one", return_value=mock_hotkey_bar):
            message = VerboseToggled(is_verbose=False)
            app.on_verbose_toggled(message)

        assert mock_hotkey_bar.verbose is False

    def test_on_verbose_toggled_true(self) -> None:
        """on_verbose_toggled() should handle verbose=True."""
        from unittest.mock import MagicMock, patch

        from debussy.ui.messages import VerboseToggled
        from debussy.ui.tui import DebussyTUI, HotkeyBar

        app = DebussyTUI()
        mock_hotkey_bar = MagicMock(spec=HotkeyBar)

        with patch.object(app, "query_one", return_value=mock_hotkey_bar):
            message = VerboseToggled(is_verbose=True)
            app.on_verbose_toggled(message)

        assert mock_hotkey_bar.verbose is True

    def test_on_orchestration_completed_success(self) -> None:
        """on_orchestration_completed() should log success message."""
        from unittest.mock import patch

        from debussy.ui.messages import OrchestrationCompleted
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with patch.object(app, "write_log") as mock_write:
            message = OrchestrationCompleted(
                run_id="run-123", success=True, message="All phases complete"
            )
            app.on_orchestration_completed(message)

        mock_write.assert_called_once()
        call_args = mock_write.call_args[0][0]
        assert "green" in call_args
        assert "All phases complete" in call_args

    def test_on_orchestration_completed_failure(self) -> None:
        """on_orchestration_completed() should log failure message."""
        from unittest.mock import patch

        from debussy.ui.messages import OrchestrationCompleted
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()

        with patch.object(app, "write_log") as mock_write:
            message = OrchestrationCompleted(
                run_id="run-456", success=False, message="Phase 2 failed"
            )
            app.on_orchestration_completed(message)

        mock_write.assert_called_once()
        call_args = mock_write.call_args[0][0]
        assert "red" in call_args
        assert "Phase 2 failed" in call_args


class TestMessageHandlerIntegration:
    """Integration tests for message handlers with controller (PR #4).

    These tests verify that messages emitted by the controller are correctly
    received and handled by the TUI.
    """

    def test_controller_start_triggers_handler(self) -> None:
        """Controller.start() should trigger on_orchestration_started handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import OrchestrationStarted
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        # Capture posted message
        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.start("test-plan", 3)

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], OrchestrationStarted)
        assert posted_messages[0].plan_name == "test-plan"
        assert posted_messages[0].total_phases == 3

    def test_controller_set_phase_triggers_handler(self) -> None:
        """Controller.set_phase() should trigger on_phase_changed handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import PhaseChanged
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)
        controller.context.total_phases = 5

        mock_phase = Mock()
        mock_phase.id = "build"
        mock_phase.title = "Build Phase"

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.set_phase(mock_phase, 2)

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], PhaseChanged)
        assert posted_messages[0].phase_id == "build"
        assert posted_messages[0].phase_title == "Build Phase"
        assert posted_messages[0].phase_index == 2

    def test_controller_set_state_triggers_handler(self) -> None:
        """Controller.set_state() should trigger on_state_changed handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import StateChanged
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.set_state(UIState.PAUSED)

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], StateChanged)
        assert posted_messages[0].state == UIState.PAUSED

    def test_controller_toggle_verbose_triggers_handlers(self) -> None:
        """Controller.toggle_verbose() should trigger both handlers."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import HUDMessageSet, VerboseToggled
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.toggle_verbose()

        # Should emit VerboseToggled and HUDMessageSet
        assert len(posted_messages) == 2
        assert any(isinstance(m, VerboseToggled) for m in posted_messages)
        assert any(isinstance(m, HUDMessageSet) for m in posted_messages)

    def test_controller_queue_action_triggers_hud_message(self) -> None:
        """Controller.queue_action() should trigger HUD message."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import HUDMessageSet
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.queue_action(UserAction.PAUSE)

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], HUDMessageSet)
        assert "Pause" in posted_messages[0].message

    def test_controller_update_token_stats_triggers_handler(self) -> None:
        """Controller.update_token_stats() should trigger handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import TokenStatsUpdated
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.update_token_stats(1000, 500, 0.05, 50_000, 200_000)

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], TokenStatsUpdated)
        assert posted_messages[0].session_input_tokens == 1500  # input + output
        assert posted_messages[0].context_pct == 25

    def test_controller_complete_triggers_handler(self) -> None:
        """Controller.complete() should trigger on_orchestration_completed handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import OrchestrationCompleted
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.complete("run-abc", True, "Success!")

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], OrchestrationCompleted)
        assert posted_messages[0].run_id == "run-abc"
        assert posted_messages[0].success is True
        assert posted_messages[0].message == "Success!"

    def test_controller_log_message_triggers_handler(self) -> None:
        """Controller.log_message() should trigger on_log_message handler."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import LogMessage
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.log_message("Test log entry")

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], LogMessage)
        assert posted_messages[0].message == "Test log entry"
        assert posted_messages[0].raw is False

    def test_controller_log_message_raw_triggers_handler(self) -> None:
        """Controller.log_message_raw() should trigger handler with raw=True."""
        from unittest.mock import patch

        from debussy.ui.controller import OrchestrationController
        from debussy.ui.messages import LogMessage
        from debussy.ui.tui import DebussyTUI

        app = DebussyTUI()
        controller = OrchestrationController(app)
        app.set_controller(controller)

        posted_messages = []
        with patch.object(app, "post_message", side_effect=posted_messages.append):
            controller.log_message_raw("Important message")

        assert len(posted_messages) == 1
        assert isinstance(posted_messages[0], LogMessage)
        assert posted_messages[0].raw is True
