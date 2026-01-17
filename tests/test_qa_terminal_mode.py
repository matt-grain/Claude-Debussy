"""Tests for Q&A handler terminal mode functionality.

Tests the interactive Q&A behavior including terminal prompts,
answer recording, question batching, and pre-loaded answers.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from debussy.planners.analyzer import Gap, GapType
from debussy.planners.qa_handler import (
    QAHandler,
    QuestionBatch,
)


# =============================================================================
# Fixtures
# =============================================================================


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
# Test Default Behavior
# =============================================================================


class TestTerminalModeDefault:
    """Test default Q&A handler behavior."""

    def test_initialization_without_gaps(self, sample_questions: list[str]) -> None:
        """Test handler initialization without gaps."""
        handler = QAHandler(questions=sample_questions)
        assert len(handler.pending_questions) == 3

    def test_initialization_with_gaps(self, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test handler initialization with gaps."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps)
        assert len(handler.pending_questions) == 3


# =============================================================================
# Test Terminal Prompt Method
# =============================================================================


class TestTerminalPromptMethod:
    """Test the _prompt_terminal method directly."""

    def test_prompt_returns_answer(self) -> None:
        """Test that prompt returns user's answer."""
        handler = QAHandler(questions=["Test?"])

        with patch("builtins.input", return_value="My answer"):
            result = handler._prompt_terminal("Test question?")

        assert result == "My answer"

    def test_prompt_returns_none_on_skip(self) -> None:
        """Test that 'skip' input returns None."""
        handler = QAHandler(questions=["Test?"])

        with patch("builtins.input", return_value="skip"):
            result = handler._prompt_terminal("Test question?")

        assert result is None

    def test_prompt_skip_case_insensitive(self) -> None:
        """Test that skip is case insensitive."""
        handler = QAHandler(questions=["Test?"])

        for skip_variant in ["SKIP", "Skip", "sKiP"]:
            with patch("builtins.input", return_value=skip_variant):
                result = handler._prompt_terminal("Test?")
            assert result is None

    def test_prompt_strips_whitespace(self) -> None:
        """Test that whitespace is stripped from answers."""
        handler = QAHandler(questions=["Test?"])

        with patch("builtins.input", return_value="  my answer  "):
            result = handler._prompt_terminal("Test?")

        assert result == "my answer"


# =============================================================================
# Test Interactive Q&A Session
# =============================================================================


class TestInteractiveSession:
    """Test the full interactive Q&A session."""

    def test_ask_questions_interactive_all_answered(self, sample_questions: list[str]) -> None:
        """Test answering all questions interactively."""
        handler = QAHandler(questions=sample_questions)

        answers = ["PostgreSQL", "All tests pass", "pytest"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        assert len(result) == 3
        assert handler.all_answered

    def test_ask_questions_interactive_some_skipped(self, sample_questions: list[str]) -> None:
        """Test skipping some questions."""
        handler = QAHandler(questions=sample_questions)

        answers = ["PostgreSQL", "skip", "pytest"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        # Only 2 answered (one skipped)
        assert len(result) == 2
        assert handler.all_answered  # All processed (answered or skipped)

    def test_ask_questions_interactive_all_skipped(self, sample_questions: list[str]) -> None:
        """Test skipping all questions."""
        handler = QAHandler(questions=sample_questions)

        answers = ["skip", "skip", "skip"]
        with patch("builtins.input", side_effect=answers):
            result = handler.ask_questions_interactive()

        assert len(result) == 0
        assert handler.all_answered


# =============================================================================
# Test Pre-loaded Answers
# =============================================================================


class TestPreloadedAnswers:
    """Test pre-loaded answers from file."""

    def test_load_answers_from_file(self, sample_questions: list[str]) -> None:
        """Test loading answers from JSON file."""
        answers_data = {
            "answers": [
                {"question": sample_questions[0], "answer": "PostgreSQL"},
                {"question": sample_questions[1], "answer": "All tests pass"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(answers_data, f)
            answers_file = Path(f.name)

        try:
            handler = QAHandler(questions=sample_questions, answers_file=answers_file)

            # Should use pre-loaded answers without prompting
            with patch("builtins.input", return_value="manual answer") as mock_input:
                handler.ask_questions_interactive()

            # Only called once for the third question (not pre-loaded)
            assert mock_input.call_count == 1

            answers = handler.get_answers_by_question()
            assert answers[sample_questions[0]] == "PostgreSQL"
            assert answers[sample_questions[1]] == "All tests pass"
            assert answers[sample_questions[2]] == "manual answer"
        finally:
            answers_file.unlink()

    def test_preloaded_answers_fallback_to_prompt(self, sample_questions: list[str]) -> None:
        """Test that missing pre-loaded answers fall back to prompt."""
        answers_data = {
            "answers": [
                {"question": sample_questions[0], "answer": "PostgreSQL"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(answers_data, f)
            answers_file = Path(f.name)

        try:
            handler = QAHandler(questions=sample_questions, answers_file=answers_file)

            with patch("builtins.input", side_effect=["answer2", "answer3"]):
                handler.ask_questions_interactive()

            answers = handler.get_answers_by_question()
            assert answers[sample_questions[0]] == "PostgreSQL"
            assert answers[sample_questions[1]] == "answer2"
            assert answers[sample_questions[2]] == "answer3"
        finally:
            answers_file.unlink()

    def test_invalid_answers_file_handled_gracefully(self, sample_questions: list[str]) -> None:
        """Test that invalid answers file doesn't crash."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            answers_file = Path(f.name)

        try:
            # Should not raise, just log warning
            handler = QAHandler(questions=sample_questions, answers_file=answers_file)
            assert len(handler.pending_questions) == 3
        finally:
            answers_file.unlink()


# =============================================================================
# Test Question Export
# =============================================================================


class TestQuestionExport:
    """Test question export functionality."""

    def test_export_questions_json(self, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test exporting questions as JSON."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps)

        json_str = handler.export_questions_json()
        data = json.loads(json_str)

        assert "questions" in data
        assert len(data["questions"]) == 3
        assert data["questions"][0]["question"] == sample_questions[0]
        assert data["questions"][0]["gap_type"] == "tech_stack"

    def test_export_questions_json_with_issue_numbers(self) -> None:
        """Test that issue numbers are extracted from questions."""
        questions = [
            "Issue #42 'Test': What database to use?",
            "Issue #99 'Other': What framework?",
        ]
        handler = QAHandler(questions=questions)

        json_str = handler.export_questions_json()
        data = json.loads(json_str)

        assert data["questions"][0]["issue_number"] == 42
        assert data["questions"][1]["issue_number"] == 99


# =============================================================================
# Test Answer Recording and Retrieval
# =============================================================================


class TestAnswerRecording:
    """Test answer recording functionality."""

    def test_record_answer(self) -> None:
        """Test recording an answer."""
        handler = QAHandler(questions=["Q1?", "Q2?"])

        handler.record_answer("Q1?", "Answer 1")

        assert len(handler.answers) == 1
        assert len(handler.pending_questions) == 1

    def test_get_answers_by_question(self) -> None:
        """Test getting answers keyed by question text."""
        handler = QAHandler(questions=["Q1?", "Q2?"])

        handler.record_answer("Q1?", "Answer 1")
        handler.record_answer("Q2?", "Answer 2")

        result = handler.get_answers_by_question()
        assert result["Q1?"] == "Answer 1"
        assert result["Q2?"] == "Answer 2"

    def test_answers_property_returns_copy(self) -> None:
        """Test that answers property returns a copy."""
        handler = QAHandler(questions=["Q?"])
        handler.record_answer("Q?", "A")

        answers = handler.answers
        answers["new"] = "value"  # Modify the copy

        # Original should be unchanged
        assert "new" not in handler.answers


# =============================================================================
# Test Question Skipping
# =============================================================================


class TestQuestionSkipping:
    """Test question skipping functionality."""

    def test_skip_question(self) -> None:
        """Test skipping a single question."""
        handler = QAHandler(questions=["Q1?", "Q2?"])

        handler.skip_question("Q1?")

        assert len(handler.pending_questions) == 1
        assert handler.pending_questions[0] == "Q2?"

    def test_skip_all_optional(self, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test skipping all warning-severity questions."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps)

        # Sample gaps have 1 warning (tech_stack) and 2 critical
        skipped = handler.skip_all_optional()

        assert skipped == 1
        assert len(handler.pending_questions) == 2  # Critical ones remain

    def test_skip_all_optional_without_gaps(self, sample_questions: list[str]) -> None:
        """Test that skip_all_optional does nothing without gaps."""
        handler = QAHandler(questions=sample_questions)

        skipped = handler.skip_all_optional()

        assert skipped == 0
        assert len(handler.pending_questions) == 3


# =============================================================================
# Test Question Batching
# =============================================================================


class TestQuestionBatching:
    """Test question batching functionality."""

    def test_batch_questions_without_gaps(self) -> None:
        """Test batching without gap info."""
        questions = ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]
        handler = QAHandler(questions=questions)

        batches = handler.batch_questions()

        # 5 questions, max 4 per batch = 2 batches
        assert len(batches) == 2
        assert len(batches[0].questions) == 4
        assert len(batches[1].questions) == 1

    def test_batch_questions_with_gaps(self, sample_questions: list[str], sample_gaps: list[Gap]) -> None:
        """Test batching with gap info prioritizes critical."""
        handler = QAHandler(questions=sample_questions, gaps=sample_gaps)

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

    def test_batch_size_limit(self) -> None:
        """Test that batches respect MAX_QUESTIONS_PER_BATCH."""
        questions = [f"Q{i}?" for i in range(10)]
        handler = QAHandler(questions=questions)

        batches = handler.batch_questions()

        for batch in batches:
            assert len(batch.questions) <= handler.MAX_QUESTIONS_PER_BATCH


# =============================================================================
# Test TUI Formatting
# =============================================================================


class TestTUIFormatting:
    """Test question formatting for TUI."""

    def test_format_question_for_tui_default_options(self) -> None:
        """Test formatting with default options."""
        handler = QAHandler(questions=["Test?"])

        formatted = handler.format_question_for_tui("Test question?")

        assert formatted["question"] == "Test question?"
        assert len(formatted["options"]) == 4
        assert formatted["multiSelect"] is False

    def test_format_question_for_tui_custom_options(self) -> None:
        """Test formatting with custom options."""
        handler = QAHandler(questions=["Test?"])

        formatted = handler.format_question_for_tui("DB?", default_options=["PostgreSQL", "MySQL"])

        assert len(formatted["options"]) == 2
        assert formatted["options"][0]["label"] == "PostgreSQL"

    def test_format_question_header_extraction(self) -> None:
        """Test header extraction from question."""
        handler = QAHandler(questions=[])

        # Should extract "Tech" from tech-related question
        formatted = handler.format_question_for_tui("What tech stack will be used?")
        assert formatted["header"] == "Tech"

        # Should extract "Validation" from validation question
        formatted = handler.format_question_for_tui("What validation is needed?")
        assert formatted["header"] == "Validation"

    def test_format_batch_for_tui(self) -> None:
        """Test formatting a batch of questions."""
        handler = QAHandler(questions=["Q1?", "Q2?"])
        batch = QuestionBatch(questions=["Q1?", "Q2?"], gap_type="general", severity="warning")

        formatted = handler.format_batch_for_tui(batch)

        assert len(formatted) == 2
        assert all("question" in f for f in formatted)


# =============================================================================
# Test Pending Questions Property
# =============================================================================


class TestPendingQuestions:
    """Test pending questions property."""

    def test_pending_questions_initial(self, sample_questions: list[str]) -> None:
        """Test that all questions are pending initially."""
        handler = QAHandler(questions=sample_questions)
        assert handler.pending_questions == sample_questions

    def test_pending_questions_after_answer(self, sample_questions: list[str]) -> None:
        """Test that answered questions are removed from pending."""
        handler = QAHandler(questions=sample_questions)
        handler.record_answer(sample_questions[0], "answer")

        assert sample_questions[0] not in handler.pending_questions
        assert len(handler.pending_questions) == 2

    def test_pending_questions_after_skip(self, sample_questions: list[str]) -> None:
        """Test that skipped questions are removed from pending."""
        handler = QAHandler(questions=sample_questions)
        handler.skip_question(sample_questions[0])

        assert sample_questions[0] not in handler.pending_questions


# =============================================================================
# Test All Answered Property
# =============================================================================


class TestAllAnswered:
    """Test all_answered property."""

    def test_all_answered_false_initially(self, sample_questions: list[str]) -> None:
        """Test that all_answered is False initially."""
        handler = QAHandler(questions=sample_questions)
        assert handler.all_answered is False

    def test_all_answered_after_answering_all(self, sample_questions: list[str]) -> None:
        """Test that all_answered is True after answering all."""
        handler = QAHandler(questions=sample_questions)
        for q in sample_questions:
            handler.record_answer(q, "answer")

        assert handler.all_answered is True

    def test_all_answered_with_skips(self, sample_questions: list[str]) -> None:
        """Test that all_answered counts skipped questions."""
        handler = QAHandler(questions=sample_questions)
        handler.record_answer(sample_questions[0], "answer")
        handler.skip_question(sample_questions[1])
        handler.skip_question(sample_questions[2])

        assert handler.all_answered is True
