"""Regression tests for Q&A terminal mode functionality.

Ensures that the original terminal-based interactive Q&A behavior remains
unchanged after adding pipe mode support. These tests verify backward
compatibility with the existing workflow.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from debussy.planners.analyzer import Gap, GapType
from debussy.planners.models import QAMode
from debussy.planners.qa_handler import (
    ENV_QA_PIPE,
    QAHandler,
    QuestionBatch,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def _clean_env():
    """Ensure DEBUSSY_QA_PIPE is not set for terminal mode tests."""
    old_pipe = os.environ.pop(ENV_QA_PIPE, None)
    yield
    if old_pipe is not None:
        os.environ[ENV_QA_PIPE] = old_pipe
    else:
        os.environ.pop(ENV_QA_PIPE, None)


@pytest.fixture
def sample_questions() -> list[str]:
    """Sample questions for testing."""
    return [
        "Which database will this project use?",
        "What defines 'done' for this issue?",
        "What test framework should be used?",
    ]


@pytest.fixture
def sample_gaps() -> list[Gap]:
    """Create sample gaps for testing."""
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
        Gap(
            gap_type=GapType.VALIDATION,
            severity="critical",
            issue_number=1,
            description="No validation mentioned",
            suggested_question="What test framework should be used?",
        ),
    ]


# =============================================================================
# Test Terminal Mode Default Behavior
# =============================================================================


class TestTerminalModeDefault:
    """Test that terminal mode is the default when DEBUSSY_QA_PIPE is not set."""

    def test_default_mode_is_terminal(self, _clean_env: None) -> None:
        """Verify default mode is TERMINAL."""
        handler = QAHandler(questions=["Test question?"])
        assert handler.mode == QAMode.TERMINAL

    def test_terminal_mode_without_gaps(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test handler initialization without gaps in terminal mode."""
        handler = QAHandler(questions=sample_questions)
        assert handler.mode == QAMode.TERMINAL
        assert len(handler.pending_questions) == 3

    def test_terminal_mode_with_gaps(self, _clean_env: None, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test handler initialization with gaps in terminal mode."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps)
        assert handler.mode == QAMode.TERMINAL
        assert len(handler.pending_questions) == 3


# =============================================================================
# Test Terminal Prompt Method
# =============================================================================


class TestTerminalPromptMethod:
    """Test the _prompt_terminal method directly."""

    def test_prompt_returns_answer(self, _clean_env: None) -> None:
        """Test that prompt returns user's answer."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        with patch("builtins.input", return_value="My answer"):
            result = handler._prompt_terminal("Test question?")

        assert result == "My answer"

    def test_prompt_returns_none_on_skip(self, _clean_env: None) -> None:
        """Test that 'skip' input returns None."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        with patch("builtins.input", return_value="skip"):
            result = handler._prompt_terminal("Test question?")

        assert result is None

    def test_prompt_skip_case_insensitive(self, _clean_env: None) -> None:
        """Test that skip is case insensitive."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        for skip_variant in ["SKIP", "Skip", "sKiP"]:
            with patch("builtins.input", return_value=skip_variant):
                result = handler._prompt_terminal("Test?")
            assert result is None

    def test_prompt_strips_whitespace(self, _clean_env: None) -> None:
        """Test that whitespace is stripped from answers."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        with patch("builtins.input", return_value="  my answer  "):
            result = handler._prompt_terminal("Test?")

        assert result == "my answer"


# =============================================================================
# Test Interactive Q&A Session (Terminal Mode)
# =============================================================================


class TestTerminalInteractiveSession:
    """Test the full interactive Q&A session in terminal mode."""

    def test_ask_questions_interactive_all_answered(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test answering all questions interactively."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)

        answers = ["PostgreSQL", "All tests pass", "pytest"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        assert len(result) == 3
        assert handler.all_answered

    def test_ask_questions_interactive_some_skipped(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test skipping some questions."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)

        answers = ["PostgreSQL", "skip", "pytest"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        # Only 2 answered (one skipped)
        assert len(result) == 2
        assert handler.all_answered  # All processed (answered or skipped)

    def test_ask_questions_interactive_all_skipped(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test skipping all questions."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)

        answers = ["skip", "skip", "skip"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        assert len(result) == 0
        assert handler.all_answered


# =============================================================================
# Test Answer Recording and Retrieval
# =============================================================================


class TestAnswerRecording:
    """Test answer recording functionality (unchanged from original)."""

    def test_record_answer(self, _clean_env: None) -> None:
        """Test recording an answer."""
        handler = QAHandler(questions=["Q1?", "Q2?"], mode=QAMode.TERMINAL)

        handler.record_answer("Q1?", "Answer 1")

        assert len(handler.answers) == 1
        assert len(handler.pending_questions) == 1

    def test_get_answers_by_question(self, _clean_env: None) -> None:
        """Test getting answers keyed by question text."""
        handler = QAHandler(questions=["Q1?", "Q2?"], mode=QAMode.TERMINAL)

        handler.record_answer("Q1?", "Answer 1")
        handler.record_answer("Q2?", "Answer 2")

        result = handler.get_answers_by_question()
        assert result["Q1?"] == "Answer 1"
        assert result["Q2?"] == "Answer 2"

    def test_answers_property_returns_copy(self, _clean_env: None) -> None:
        """Test that answers property returns a copy."""
        handler = QAHandler(questions=["Q?"], mode=QAMode.TERMINAL)
        handler.record_answer("Q?", "A")

        answers = handler.answers
        answers["new"] = "value"  # Modify the copy

        # Original should be unchanged
        assert "new" not in handler.answers


# =============================================================================
# Test Question Skipping
# =============================================================================


class TestQuestionSkipping:
    """Test question skipping functionality (unchanged from original)."""

    def test_skip_question(self, _clean_env: None) -> None:
        """Test skipping a single question."""
        handler = QAHandler(questions=["Q1?", "Q2?"], mode=QAMode.TERMINAL)

        handler.skip_question("Q1?")

        assert len(handler.pending_questions) == 1
        assert handler.pending_questions[0] == "Q2?"

    def test_skip_all_optional(self, _clean_env: None, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test skipping all warning-severity questions."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps, mode=QAMode.TERMINAL)

        # Sample gaps have 1 warning (tech_stack) and 2 critical
        skipped = handler.skip_all_optional()

        assert skipped == 1
        assert len(handler.pending_questions) == 2  # Critical ones remain

    def test_skip_all_optional_without_gaps(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that skip_all_optional does nothing without gaps."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)

        skipped = handler.skip_all_optional()

        assert skipped == 0
        assert len(handler.pending_questions) == 3


# =============================================================================
# Test Question Batching
# =============================================================================


class TestQuestionBatching:
    """Test question batching functionality (unchanged from original)."""

    def test_batch_questions_without_gaps(self, _clean_env: None) -> None:
        """Test batching without gap info."""
        questions = ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]
        handler = QAHandler(questions=questions, mode=QAMode.TERMINAL)

        batches = handler.batch_questions()

        # 5 questions, max 4 per batch = 2 batches
        assert len(batches) == 2
        assert len(batches[0].questions) == 4
        assert len(batches[1].questions) == 1

    def test_batch_questions_with_gaps(self, _clean_env: None, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test batching with gap info prioritizes critical."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps, mode=QAMode.TERMINAL)

        batches = handler.batch_questions()

        # Critical gaps should come first
        critical_batches = [b for b in batches if b.severity == "critical"]
        warning_batches = [b for b in batches if b.severity == "warning"]

        assert len(critical_batches) >= 1
        assert len(warning_batches) >= 1

        # Critical should be first in the list
        first_critical_idx = next(i for i, b in enumerate(batches) if b.severity == "critical")
        first_warning_idx = next(i for i, b in enumerate(batches) if b.severity == "warning")
        assert first_critical_idx < first_warning_idx

    def test_batch_size_limit(self, _clean_env: None) -> None:
        """Test that batches respect MAX_QUESTIONS_PER_BATCH."""
        questions = [f"Q{i}?" for i in range(10)]
        handler = QAHandler(questions=questions, mode=QAMode.TERMINAL)

        batches = handler.batch_questions()

        for batch in batches:
            assert len(batch.questions) <= handler.MAX_QUESTIONS_PER_BATCH


# =============================================================================
# Test TUI Formatting
# =============================================================================


class TestTUIFormatting:
    """Test question formatting for TUI (unchanged from original)."""

    def test_format_question_for_tui_default_options(self, _clean_env: None) -> None:
        """Test formatting with default options."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        formatted = handler.format_question_for_tui("Test question?")

        assert formatted["question"] == "Test question?"
        assert len(formatted["options"]) == 4
        assert formatted["multiSelect"] is False

    def test_format_question_for_tui_custom_options(self, _clean_env: None) -> None:
        """Test formatting with custom options."""
        handler = QAHandler(questions=["Test?"], mode=QAMode.TERMINAL)

        formatted = handler.format_question_for_tui("DB?", default_options=["PostgreSQL", "MySQL"])

        assert len(formatted["options"]) == 2
        assert formatted["options"][0]["label"] == "PostgreSQL"

    def test_format_question_header_extraction(self, _clean_env: None) -> None:
        """Test header extraction from question."""
        handler = QAHandler(questions=[], mode=QAMode.TERMINAL)

        # Should extract "Tech" from tech-related question
        formatted = handler.format_question_for_tui("What tech stack will be used?")
        assert formatted["header"] == "Tech"

        # Should extract "Validation" from validation question
        formatted = handler.format_question_for_tui("What validation is needed?")
        assert formatted["header"] == "Validation"

    def test_format_batch_for_tui(self, _clean_env: None) -> None:
        """Test formatting a batch of questions."""
        handler = QAHandler(questions=["Q1?", "Q2?"], mode=QAMode.TERMINAL)
        batch = QuestionBatch(questions=["Q1?", "Q2?"], gap_type="general", severity="warning")

        formatted = handler.format_batch_for_tui(batch)

        assert len(formatted) == 2
        assert all("question" in f for f in formatted)


# =============================================================================
# Test Pending Questions Property
# =============================================================================


class TestPendingQuestions:
    """Test pending questions property (unchanged from original)."""

    def test_pending_questions_initial(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that all questions are pending initially."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        assert handler.pending_questions == sample_questions

    def test_pending_questions_after_answer(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that answered questions are removed from pending."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        handler.record_answer(sample_questions[0], "answer")

        assert sample_questions[0] not in handler.pending_questions
        assert len(handler.pending_questions) == 2

    def test_pending_questions_after_skip(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that skipped questions are removed from pending."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        handler.skip_question(sample_questions[0])

        assert sample_questions[0] not in handler.pending_questions


# =============================================================================
# Test All Answered Property
# =============================================================================


class TestAllAnswered:
    """Test all_answered property (unchanged from original)."""

    def test_all_answered_false_initially(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that all_answered is False initially."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        assert handler.all_answered is False

    def test_all_answered_after_answering_all(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that all_answered is True after answering all."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        for q in sample_questions:
            handler.record_answer(q, "answer")

        assert handler.all_answered is True

    def test_all_answered_with_skips(self, _clean_env: None, sample_questions: list[str]) -> None:
        """Test that all_answered counts skipped questions."""
        handler = QAHandler(questions=sample_questions, mode=QAMode.TERMINAL)
        handler.record_answer(sample_questions[0], "answer")
        handler.skip_question(sample_questions[1])
        handler.skip_question(sample_questions[2])

        assert handler.all_answered is True


# =============================================================================
# Test Explicit Mode Override
# =============================================================================


class TestExplicitModeOverride:
    """Test that explicit mode parameter overrides environment."""

    def test_explicit_terminal_mode(self, _clean_env: None) -> None:
        """Test explicit terminal mode."""
        os.environ[ENV_QA_PIPE] = "1"  # Would normally enable pipe mode
        handler = QAHandler(questions=["Q?"], mode=QAMode.TERMINAL)

        assert handler.mode == QAMode.TERMINAL

    def test_explicit_pipe_mode_in_terminal_test(self, _clean_env: None) -> None:
        """Test that explicit pipe mode works even when env says terminal."""
        # No env var set (would default to terminal)
        handler = QAHandler(questions=["Q?"], mode=QAMode.PIPE)

        assert handler.mode == QAMode.PIPE
