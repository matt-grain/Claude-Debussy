"""Unit and integration tests for Q&A pipe mode functionality.

Tests the JSON IPC protocol for integrating QAHandler with parent processes
like Claude Code. Covers:
- Environment detection for QAMode
- JSON serialization/deserialization
- Pipe mode question emission
- Pipe mode answer reading
- Timeout handling
- Fallback to terminal mode on errors
- End-to-end pipe mode simulation
"""

from __future__ import annotations

import io
import json
import os
import sys
from unittest.mock import patch

import pytest

from debussy.planners.analyzer import Gap, GapType
from debussy.planners.models import QAAnswer, QAMode, QAQuestion
from debussy.planners.qa_handler import (
    DEFAULT_PIPE_TIMEOUT,
    ENV_QA_PIPE,
    ENV_QA_TIMEOUT,
    PipeProtocolError,
    PipeTimeoutError,
    QAHandler,
    _detect_qa_mode,
    _get_pipe_timeout,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_gap() -> Gap:
    """Create a sample gap for testing."""
    return Gap(
        gap_type=GapType.TECH_STACK,
        severity="warning",
        issue_number=1,
        description="No technology mentioned",
        suggested_question="Which database will this project use?",
    )


@pytest.fixture
def sample_gaps() -> list[Gap]:
    """Create multiple sample gaps for testing."""
    return [
        Gap(
            gap_type=GapType.TECH_STACK,
            severity="warning",
            issue_number=1,
            description="No technology mentioned",
            suggested_question="Which database will this project use?",
        ),
        Gap(
            gap_type=GapType.ACCEPTANCE_CRITERIA,
            severity="critical",
            issue_number=1,
            description="No acceptance criteria",
            suggested_question="What defines 'done' for this issue?",
        ),
    ]


@pytest.fixture
def _clean_env():
    """Ensure environment variables are clean before and after tests."""
    old_pipe = os.environ.pop(ENV_QA_PIPE, None)
    old_timeout = os.environ.pop(ENV_QA_TIMEOUT, None)
    yield
    if old_pipe is not None:
        os.environ[ENV_QA_PIPE] = old_pipe
    else:
        os.environ.pop(ENV_QA_PIPE, None)
    if old_timeout is not None:
        os.environ[ENV_QA_TIMEOUT] = old_timeout
    else:
        os.environ.pop(ENV_QA_TIMEOUT, None)


# =============================================================================
# Test QAMode Detection
# =============================================================================


class TestQAModeDetection:
    """Test environment-based Q&A mode detection."""

    def test_default_mode_is_terminal(self, _clean_env: None) -> None:
        """Test that default mode is TERMINAL when env var not set."""
        mode = _detect_qa_mode()
        assert mode == QAMode.TERMINAL

    def test_pipe_mode_when_env_set(self, _clean_env: None) -> None:
        """Test that PIPE mode is detected when DEBUSSY_QA_PIPE=1."""
        os.environ[ENV_QA_PIPE] = "1"
        mode = _detect_qa_mode()
        assert mode == QAMode.PIPE

    def test_terminal_mode_when_env_not_one(self, _clean_env: None) -> None:
        """Test that TERMINAL mode is used for values other than '1'."""
        os.environ[ENV_QA_PIPE] = "0"
        assert _detect_qa_mode() == QAMode.TERMINAL

        os.environ[ENV_QA_PIPE] = "true"
        assert _detect_qa_mode() == QAMode.TERMINAL

        os.environ[ENV_QA_PIPE] = ""
        assert _detect_qa_mode() == QAMode.TERMINAL

    def test_pipe_mode_with_whitespace(self, _clean_env: None) -> None:
        """Test that whitespace around '1' is handled."""
        os.environ[ENV_QA_PIPE] = " 1 "
        mode = _detect_qa_mode()
        assert mode == QAMode.PIPE


class TestPipeTimeout:
    """Test timeout configuration for pipe mode."""

    def test_default_timeout(self, _clean_env: None) -> None:
        """Test that default timeout is used when env var not set."""
        timeout = _get_pipe_timeout()
        assert timeout == DEFAULT_PIPE_TIMEOUT

    def test_custom_timeout(self, _clean_env: None) -> None:
        """Test that custom timeout is parsed from env var."""
        os.environ[ENV_QA_TIMEOUT] = "60"
        timeout = _get_pipe_timeout()
        assert timeout == 60

    def test_invalid_timeout_uses_default(self, _clean_env: None) -> None:
        """Test that invalid timeout values fall back to default."""
        os.environ[ENV_QA_TIMEOUT] = "not_a_number"
        timeout = _get_pipe_timeout()
        assert timeout == DEFAULT_PIPE_TIMEOUT


# =============================================================================
# Test Pydantic Models
# =============================================================================


class TestQAQuestionModel:
    """Test QAQuestion Pydantic model."""

    def test_question_creation(self) -> None:
        """Test creating a QAQuestion with required fields."""
        question = QAQuestion(
            gap_type="tech_stack",
            question="Which database?",
        )
        assert question.type == "question"
        assert question.gap_type == "tech_stack"
        assert question.question == "Which database?"
        assert question.options == []
        assert question.context == ""

    def test_question_with_all_fields(self) -> None:
        """Test creating a QAQuestion with all fields."""
        question = QAQuestion(
            gap_type="tech_stack",
            question="Which database will this project use?",
            options=["PostgreSQL", "MySQL", "SQLite"],
            context="No database mentioned in issues",
        )
        assert question.options == ["PostgreSQL", "MySQL", "SQLite"]
        assert question.context == "No database mentioned in issues"

    def test_question_serialization(self) -> None:
        """Test JSON serialization of QAQuestion."""
        question = QAQuestion(
            gap_type="tech_stack",
            question="Which database?",
            options=["PostgreSQL"],
            context="Test context",
        )
        json_str = question.model_dump_json()
        data = json.loads(json_str)

        assert data["type"] == "question"
        assert data["gap_type"] == "tech_stack"
        assert data["question"] == "Which database?"
        assert data["options"] == ["PostgreSQL"]
        assert data["context"] == "Test context"

    def test_question_deserialization(self) -> None:
        """Test JSON deserialization to QAQuestion."""
        data = {
            "type": "question",
            "gap_type": "acceptance_criteria",
            "question": "What is done?",
            "options": [],
            "context": "",
        }
        question = QAQuestion.model_validate(data)
        assert question.gap_type == "acceptance_criteria"
        assert question.question == "What is done?"


class TestQAAnswerModel:
    """Test QAAnswer Pydantic model."""

    def test_answer_creation(self) -> None:
        """Test creating a QAAnswer."""
        answer = QAAnswer(
            gap_type="tech_stack",
            answer="PostgreSQL",
        )
        assert answer.type == "answer"
        assert answer.gap_type == "tech_stack"
        assert answer.answer == "PostgreSQL"

    def test_answer_serialization(self) -> None:
        """Test JSON serialization of QAAnswer."""
        answer = QAAnswer(gap_type="tech_stack", answer="PostgreSQL")
        json_str = answer.model_dump_json()
        data = json.loads(json_str)

        assert data["type"] == "answer"
        assert data["gap_type"] == "tech_stack"
        assert data["answer"] == "PostgreSQL"

    def test_answer_deserialization(self) -> None:
        """Test JSON deserialization to QAAnswer."""
        data = {
            "type": "answer",
            "gap_type": "tech_stack",
            "answer": "MySQL",
        }
        answer = QAAnswer.model_validate(data)
        assert answer.gap_type == "tech_stack"
        assert answer.answer == "MySQL"


# =============================================================================
# Test QAHandler Initialization
# =============================================================================


class TestQAHandlerInit:
    """Test QAHandler initialization with different modes."""

    def test_default_mode_detection(self, _clean_env: None) -> None:
        """Test that handler detects mode from environment."""
        handler = QAHandler(questions=["Q1?"])
        assert handler.mode == QAMode.TERMINAL

    def test_explicit_terminal_mode(self, _clean_env: None) -> None:
        """Test explicit terminal mode override."""
        os.environ[ENV_QA_PIPE] = "1"  # Would be PIPE, but we override
        handler = QAHandler(questions=["Q1?"], mode=QAMode.TERMINAL)
        assert handler.mode == QAMode.TERMINAL

    def test_explicit_pipe_mode(self, _clean_env: None) -> None:
        """Test explicit pipe mode override."""
        handler = QAHandler(questions=["Q1?"], mode=QAMode.PIPE)
        assert handler.mode == QAMode.PIPE

    def test_mode_property(self, _clean_env: None) -> None:
        """Test that mode property returns current mode."""
        handler = QAHandler(questions=["Q1?"], mode=QAMode.PIPE)
        assert handler.mode == QAMode.PIPE


# =============================================================================
# Test Pipe Mode Question Emission
# =============================================================================


class TestPipeQuestionEmission:
    """Test JSON question emission in pipe mode."""

    def test_emit_question_json_basic(self, _clean_env: None, capsys: pytest.CaptureFixture[str]) -> None:
        """Test basic question emission to stdout."""
        handler = QAHandler(questions=["What database?"], mode=QAMode.PIPE)
        handler._emit_question_json("What database?", "tech_stack", "No DB mentioned")

        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())

        assert data["type"] == "question"
        assert data["gap_type"] == "tech_stack"
        assert data["question"] == "What database?"
        assert data["context"] == "No DB mentioned"

    def test_emit_question_uses_gap_info(self, _clean_env: None, sample_gap: Gap, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that question emission uses gap info when available."""
        handler = QAHandler(
            questions=[sample_gap.suggested_question],
            gaps=[sample_gap],
            mode=QAMode.PIPE,
        )
        handler._emit_question_json(sample_gap.suggested_question)

        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())

        assert data["gap_type"] == "tech_stack"
        assert data["context"] == "No technology mentioned"


# =============================================================================
# Test Pipe Mode Answer Reading
# =============================================================================


class TestPipeAnswerReading:
    """Test JSON answer reading in pipe mode."""

    def test_read_valid_answer(self, _clean_env: None) -> None:
        """Test reading a valid JSON answer."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        answer_json = json.dumps({"type": "answer", "gap_type": "tech_stack", "answer": "PostgreSQL"})
        mock_stdin = io.StringIO(answer_json + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler._read_answer_json("tech_stack")

        assert result == "PostgreSQL"

    def test_read_skip_answer(self, _clean_env: None) -> None:
        """Test that 'skip' answer returns None."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        answer_json = json.dumps({"type": "answer", "gap_type": "tech_stack", "answer": "skip"})
        mock_stdin = io.StringIO(answer_json + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler._read_answer_json("tech_stack")

        assert result is None

    def test_read_invalid_json_raises_error(self, _clean_env: None) -> None:
        """Test that invalid JSON raises PipeProtocolError."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        mock_stdin = io.StringIO("not valid json\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])), pytest.raises(PipeProtocolError, match="Invalid JSON"):
            handler._read_answer_json("tech_stack")

    def test_read_invalid_format_raises_error(self, _clean_env: None) -> None:
        """Test that invalid answer format raises PipeProtocolError."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        # Missing required 'answer' field
        answer_json = json.dumps({"type": "answer", "gap_type": "tech_stack"})
        mock_stdin = io.StringIO(answer_json + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])), pytest.raises(PipeProtocolError, match="Invalid answer format"):
            handler._read_answer_json("tech_stack")

    def test_read_eof_raises_error(self, _clean_env: None) -> None:
        """Test that EOF raises PipeProtocolError."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        mock_stdin = io.StringIO("")  # EOF immediately

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])), pytest.raises(PipeProtocolError, match="EOF"):
            handler._read_answer_json("tech_stack")

    @pytest.mark.skipif(sys.platform == "win32", reason="select-based timeout not supported on Windows")
    def test_read_timeout_raises_error(self, _clean_env: None) -> None:
        """Test that timeout raises PipeTimeoutError.

        Note: This test only runs on Unix-like systems where select() works on stdin.
        On Windows, the timeout mechanism falls through to readline() which raises
        PipeProtocolError on EOF instead.
        """
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)
        handler._pipe_timeout = 1  # Short timeout

        mock_stdin = io.StringIO("")

        # Simulate select timeout (empty list)
        with (
            patch.object(sys, "stdin", mock_stdin),
            patch("select.select", return_value=([], [], [])),
            pytest.raises(PipeTimeoutError, match="Timeout"),
        ):
            handler._read_answer_json("tech_stack")

    def test_gap_type_mismatch_logged_but_accepted(self, _clean_env: None) -> None:
        """Test that gap type mismatch is logged but answer is accepted."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        # Answer has different gap type
        answer_json = json.dumps({"type": "answer", "gap_type": "other_type", "answer": "PostgreSQL"})
        mock_stdin = io.StringIO(answer_json + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler._read_answer_json("tech_stack")

        # Should still return the answer
        assert result == "PostgreSQL"


# =============================================================================
# Test Pipe Mode Fallback
# =============================================================================


class TestPipeModeFallback:
    """Test fallback to terminal mode on pipe errors."""

    def test_fallback_on_timeout(self, _clean_env: None) -> None:
        """Test that timeout triggers fallback to terminal."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)
        handler._pipe_timeout = 1

        # Simulate timeout
        with patch("select.select", return_value=([], [], [])), patch.object(handler, "_prompt_terminal", return_value="terminal answer") as mock_terminal:
            result = handler._ask_question_pipe("Q?")

        mock_terminal.assert_called_once_with("Q?")
        assert result == "terminal answer"

    def test_fallback_on_protocol_error(self, _clean_env: None) -> None:
        """Test that protocol error triggers fallback to terminal."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        mock_stdin = io.StringIO("invalid json\n")

        with (
            patch.object(sys, "stdin", mock_stdin),
            patch("select.select", return_value=([mock_stdin], [], [])),
            patch.object(handler, "_prompt_terminal", return_value="fallback") as mock_terminal,
        ):
            result = handler._ask_question_pipe("Q?")

        mock_terminal.assert_called_once()
        assert result == "fallback"


# =============================================================================
# Test Interactive Q&A in Pipe Mode
# =============================================================================


class TestPipeModeInteractive:
    """Test full interactive Q&A flow in pipe mode."""

    def test_ask_questions_interactive_pipe_mode(self, _clean_env: None, sample_gaps: list[Gap]) -> None:
        """Test asking multiple questions in pipe mode."""
        questions = [gap.suggested_question for gap in sample_gaps]
        handler = QAHandler(questions=questions, gaps=sample_gaps, mode=QAMode.PIPE)

        # Prepare answers for both questions
        answer1 = json.dumps({"type": "answer", "gap_type": "tech_stack", "answer": "PostgreSQL"})
        answer2 = json.dumps({"type": "answer", "gap_type": "acceptance_criteria", "answer": "All tests pass"})
        mock_stdin = io.StringIO(f"{answer1}\n{answer2}\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            answers = handler.ask_questions_interactive()

        assert len(answers) == 2
        assert handler.all_answered

    def test_ask_single_question_pipe_mode(self, _clean_env: None) -> None:
        """Test asking a single question in pipe mode."""
        handler = QAHandler(questions=[], mode=QAMode.PIPE)

        answer_json = json.dumps({"type": "answer", "gap_type": "general", "answer": "My answer"})
        mock_stdin = io.StringIO(answer_json + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler.ask_single_question("Custom question?")

        assert result == "My answer"


# =============================================================================
# Test Multiple Q&A Rounds
# =============================================================================


class TestMultipleQARounds:
    """Test handling multiple Q&A rounds in a single session."""

    def test_multiple_rounds_pipe_mode(self, _clean_env: None) -> None:
        """Test multiple sequential Q&A rounds."""
        questions = ["Question 1?", "Question 2?", "Question 3?"]
        handler = QAHandler(questions=questions, mode=QAMode.PIPE)

        # All answers in sequence
        answers = [
            json.dumps({"type": "answer", "gap_type": "general", "answer": "Answer 1"}),
            json.dumps({"type": "answer", "gap_type": "general", "answer": "Answer 2"}),
            json.dumps({"type": "answer", "gap_type": "general", "answer": "Answer 3"}),
        ]
        mock_stdin = io.StringIO("\n".join(answers) + "\n")

        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler.ask_questions_interactive()

        assert len(result) == 3
        assert handler.all_answered


# =============================================================================
# End-to-End Simulation
# =============================================================================


class TestEndToEndPipeMode:
    """Simulate end-to-end Claude Code integration."""

    def test_simulate_claude_code_parent(self, _clean_env: None, sample_gap: Gap, capsys: pytest.CaptureFixture[str]) -> None:
        """Simulate a parent process (like Claude Code) interacting via pipe."""
        handler = QAHandler(
            questions=[sample_gap.suggested_question],
            gaps=[sample_gap],
            mode=QAMode.PIPE,
        )

        # Emit the question
        handler._emit_question_json(sample_gap.suggested_question)

        # Capture and verify the question
        captured = capsys.readouterr()
        question_data = json.loads(captured.out.strip())

        assert question_data["type"] == "question"
        assert question_data["gap_type"] == "tech_stack"

        # Prepare the answer (as Claude Code would)
        answer = QAAnswer(gap_type=question_data["gap_type"], answer="PostgreSQL")
        answer_json = answer.model_dump_json()

        # Read the answer
        mock_stdin = io.StringIO(answer_json + "\n")
        with patch.object(sys, "stdin", mock_stdin), patch("select.select", return_value=([mock_stdin], [], [])):
            result = handler._read_answer_json("tech_stack")

        assert result == "PostgreSQL"


# =============================================================================
# Test Windows Compatibility
# =============================================================================


class TestWindowsCompatibility:
    """Test behavior on Windows (where select doesn't work on stdin)."""

    def test_reads_without_select_on_windows(self, _clean_env: None) -> None:
        """Test that pipe mode works on Windows by skipping select."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        answer_json = json.dumps({"type": "answer", "gap_type": "general", "answer": "Windows answer"})
        mock_stdin = io.StringIO(answer_json + "\n")

        # Simulate Windows platform
        with patch.object(sys, "stdin", mock_stdin), patch.object(sys, "platform", "win32"):
            result = handler._read_answer_json("general")

        assert result == "Windows answer"
