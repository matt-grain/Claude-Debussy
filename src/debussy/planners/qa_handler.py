"""Q&A handler for interactive gap-filling during plan generation.

This module provides the QAHandler class that manages interactive
question-and-answer sessions to fill gaps detected in issue analysis.

Supports two modes:
    TERMINAL: Traditional interactive prompts via stdin/stdout (default).
    PIPE: JSON IPC for integration with parent processes like Claude Code.
          Enabled via DEBUSSY_QA_PIPE=1 environment variable.

In pipe mode:
    - Questions are emitted as JSON to stdout
    - Answers are read as JSON from stdin
    - Logs go to stderr to keep stdout clean for IPC
    - Timeout is configurable via DEBUSSY_QA_TIMEOUT (default: 30 seconds)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import select
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

from pydantic import ValidationError

from debussy.planners.models import QAAnswer, QAMode, QAQuestion

if TYPE_CHECKING:
    from debussy.planners.analyzer import Gap

# Configure module logger - stderr only to keep stdout clean in pipe mode
logger = logging.getLogger(__name__)

# Environment variable names
ENV_QA_PIPE = "DEBUSSY_QA_PIPE"
ENV_QA_TIMEOUT = "DEBUSSY_QA_TIMEOUT"

# Default timeout for pipe mode stdin reads (seconds)
DEFAULT_PIPE_TIMEOUT = 30


class QuestionOption(TypedDict):
    """Option for a question in AskUserQuestion format."""

    label: str
    description: str


class FormattedQuestion(TypedDict):
    """Question formatted for AskUserQuestion tool."""

    question: str
    header: str
    options: list[QuestionOption]
    multiSelect: bool


@dataclass
class QuestionBatch:
    """A batch of related questions to ask together."""

    questions: list[str]
    gap_type: str
    severity: str


class PipeTimeoutError(Exception):
    """Raised when pipe mode times out waiting for input."""

    pass


class PipeProtocolError(Exception):
    """Raised when pipe mode receives invalid JSON or protocol errors."""

    pass


def _detect_qa_mode() -> QAMode:
    """Detect which Q&A mode to use based on environment.

    Returns:
        QAMode.PIPE if DEBUSSY_QA_PIPE=1 is set, otherwise QAMode.TERMINAL.
    """
    pipe_enabled = os.environ.get(ENV_QA_PIPE, "").strip()
    if pipe_enabled == "1":
        return QAMode.PIPE
    return QAMode.TERMINAL


def _get_pipe_timeout() -> int:
    """Get the timeout for pipe mode stdin reads.

    Returns:
        Timeout in seconds (default: 30).
    """
    timeout_str = os.environ.get(ENV_QA_TIMEOUT, "").strip()
    if timeout_str:
        try:
            return int(timeout_str)
        except ValueError:
            logger.warning(f"Invalid {ENV_QA_TIMEOUT} value '{timeout_str}', using default {DEFAULT_PIPE_TIMEOUT}")
    return DEFAULT_PIPE_TIMEOUT


class QAHandler:
    """Manages interactive Q&A sessions for gap-filling.

    Handles batching related questions, formatting for TUI display,
    and tracking user answers.

    Supports two modes:
        TERMINAL: Interactive prompts via stdin/stdout (default).
        PIPE: JSON IPC for integration with Claude Code. Enabled via
              DEBUSSY_QA_PIPE=1 environment variable.
    """

    MAX_QUESTIONS_PER_BATCH = 4

    def __init__(
        self,
        questions: list[str],
        gaps: list[Gap] | None = None,
        mode: QAMode | None = None,
    ) -> None:
        """Initialize the Q&A handler.

        Args:
            questions: List of questions to ask.
            gaps: Optional list of Gap objects for context. If provided,
                  enables better question batching by gap type and severity.
            mode: Explicit mode override. If None, auto-detected from environment.
        """
        self._questions = questions
        self._gaps = gaps
        self._answers: dict[str, str] = {}
        self._skipped: set[str] = set()

        # Detect or use explicit mode
        self._mode = mode if mode is not None else _detect_qa_mode()
        self._pipe_timeout = _get_pipe_timeout()

        # Log which mode is active
        logger.info(f"QAHandler initialized in {self._mode.value} mode")

    @property
    def mode(self) -> QAMode:
        """Get the current Q&A mode."""
        return self._mode

    @property
    def answers(self) -> dict[str, str]:
        """Get all collected answers."""
        return self._answers.copy()

    @property
    def pending_questions(self) -> list[str]:
        """Get questions that haven't been answered or skipped."""
        return [q for q in self._questions if self._question_hash(q) not in self._answers and self._question_hash(q) not in self._skipped]

    @property
    def all_answered(self) -> bool:
        """Check if all questions have been answered or skipped."""
        return len(self.pending_questions) == 0

    def _question_hash(self, question: str) -> str:
        """Generate a hash key for a question.

        Args:
            question: The question text.

        Returns:
            Short hash string suitable for use as a dictionary key.
        """
        return hashlib.md5(question.encode(), usedforsecurity=False).hexdigest()[:12]

    def _get_gap_for_question(self, question: str) -> Gap | None:
        """Find the Gap object associated with a question.

        Args:
            question: The question text.

        Returns:
            The Gap object if found, None otherwise.
        """
        if not self._gaps:
            return None
        for gap in self._gaps:
            if gap.suggested_question == question:
                return gap
        return None

    # =========================================================================
    # Terminal Mode Methods
    # =========================================================================

    def _prompt_terminal(self, question: str) -> str | None:
        """Prompt for an answer in terminal mode.

        Args:
            question: The question to ask.

        Returns:
            The user's answer, or None if skipped.
        """
        print(f"\n{question}")
        print("(Enter your answer, or 'skip' to skip this question)")
        answer = input("> ").strip()

        if answer.lower() == "skip":
            return None
        return answer

    # =========================================================================
    # Pipe Mode Methods
    # =========================================================================

    def _emit_question_json(self, question: str, gap_type: str = "general", context: str = "") -> None:
        """Emit a question as JSON to stdout for pipe mode.

        Args:
            question: The question text.
            gap_type: The type of gap this question addresses.
            context: Additional context about why this question is being asked.
        """
        # Get options from the associated gap if available
        options: list[str] = []
        gap = self._get_gap_for_question(question)
        if gap:
            gap_type = gap.gap_type.value
            context = gap.description

        qa_question = QAQuestion(
            gap_type=gap_type,
            question=question,
            options=options,
            context=context,
        )

        # Write to stdout as a single line of JSON
        json_str = qa_question.model_dump_json()
        print(json_str, flush=True)
        logger.debug(f"Emitted question: {json_str}")

    def _read_answer_json(self, expected_gap_type: str) -> str | None:
        """Read an answer from stdin in pipe mode with timeout.

        Args:
            expected_gap_type: The gap type we expect the answer for.

        Returns:
            The answer text, or None if skipped/timeout.

        Raises:
            PipeTimeoutError: If stdin times out.
            PipeProtocolError: If the JSON is malformed or invalid.
        """
        # Check if stdin has data available (with timeout)
        # Note: select doesn't work well on Windows, so we have a fallback
        if hasattr(select, "select") and sys.platform != "win32":
            readable, _, _ = select.select([sys.stdin], [], [], self._pipe_timeout)
            if not readable:
                raise PipeTimeoutError(f"Timeout ({self._pipe_timeout}s) waiting for answer to '{expected_gap_type}'")
        # On Windows or if select unavailable, we just read and trust the timeout

        try:
            line = sys.stdin.readline()
            if not line:
                raise PipeProtocolError("EOF received on stdin - no answer provided")

            line = line.strip()
            if not line:
                raise PipeProtocolError("Empty line received on stdin")

            logger.debug(f"Received answer: {line}")

            # Parse and validate JSON
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise PipeProtocolError(f"Invalid JSON received: {e}") from e

            # Validate with Pydantic
            try:
                answer = QAAnswer.model_validate(data)
            except ValidationError as e:
                raise PipeProtocolError(f"Invalid answer format: {e}") from e

            # Check gap type matches
            if answer.gap_type != expected_gap_type:
                logger.warning(f"Gap type mismatch: expected '{expected_gap_type}', got '{answer.gap_type}'")
                # Still accept the answer, but log the mismatch

            # Handle skip
            if answer.answer.lower() == "skip":
                return None

            return answer.answer

        except PipeTimeoutError:
            raise
        except PipeProtocolError:
            raise
        except Exception as e:
            raise PipeProtocolError(f"Error reading answer: {e}") from e

    def _ask_question_pipe(self, question: str) -> str | None:
        """Ask a question in pipe mode.

        Emits JSON question to stdout, reads JSON answer from stdin.
        Falls back to terminal mode on errors.

        Args:
            question: The question to ask.

        Returns:
            The user's answer, or None if skipped.
        """
        gap = self._get_gap_for_question(question)
        gap_type = gap.gap_type.value if gap else "general"
        context = gap.description if gap else ""

        try:
            self._emit_question_json(question, gap_type, context)
            answer = self._read_answer_json(gap_type)
            return answer
        except (PipeTimeoutError, PipeProtocolError) as e:
            # Log error and fall back to terminal mode
            logger.error(f"Pipe mode error: {e}. Falling back to terminal mode.")
            print(f"[Pipe mode error: {e}. Falling back to interactive prompt.]", file=sys.stderr)
            return self._prompt_terminal(question)

    # =========================================================================
    # Main Q&A Methods
    # =========================================================================

    def ask_questions_interactive(self) -> dict[str, str]:
        """Conduct interactive Q&A session.

        Prompts user for each pending question. Uses terminal mode or pipe mode
        depending on configuration.

        Returns:
            Dictionary mapping question hashes to user answers.
        """
        for question in self.pending_questions:
            answer = self._ask_question_pipe(question) if self._mode == QAMode.PIPE else self._prompt_terminal(question)

            if answer is None:
                self.skip_question(question)
            else:
                self._answers[self._question_hash(question)] = answer

        return self.answers

    def ask_single_question(self, question: str) -> str | None:
        """Ask a single question and return the answer.

        Useful for ad-hoc questions outside of the main Q&A flow.

        Args:
            question: The question to ask.

        Returns:
            The user's answer, or None if skipped.
        """
        if self._mode == QAMode.PIPE:
            return self._ask_question_pipe(question)
        return self._prompt_terminal(question)

    def format_question_for_tui(
        self,
        question: str,
        default_options: list[str] | None = None,
    ) -> FormattedQuestion:
        """Format a single question for AskUserQuestion tool.

        Args:
            question: The question to format.
            default_options: Optional list of default answer options.

        Returns:
            Dictionary in AskUserQuestion tool format.
        """
        # Generate header from question (max 12 chars)
        header = self._generate_header(question)

        # Generate options
        options: list[QuestionOption]
        if default_options:
            options = [QuestionOption(label=opt, description=f"Select {opt}") for opt in default_options[:4]]
        else:
            # Generic options for open-ended questions
            options = [
                QuestionOption(label="Yes", description="Confirm this requirement"),
                QuestionOption(label="No", description="Reject this requirement"),
                QuestionOption(label="Partial", description="Some aspects apply"),
                QuestionOption(label="Unsure", description="Need more information"),
            ]

        return FormattedQuestion(
            question=question,
            header=header,
            options=options,
            multiSelect=False,
        )

    def _generate_header(self, question: str) -> str:
        """Generate a short header for a question.

        Extracts key words from the question to create a header.

        Args:
            question: The question text.

        Returns:
            Header string (max 12 chars).
        """
        # Try to extract key terms
        keywords = ["tech", "stack", "criteria", "validation", "scope", "context", "dependency"]

        question_lower = question.lower()
        for keyword in keywords:
            if keyword in question_lower:
                return keyword.title()[:12]

        # Fallback: use first significant word
        words = question.split()
        for word in words:
            if len(word) > 3 and word.lower() not in {"what", "which", "does", "this", "that", "have", "with"}:
                return word[:12]

        return "Question"

    def batch_questions(self) -> list[QuestionBatch]:
        """Group questions into batches for efficient asking.

        Groups questions by gap type, with critical gaps first.
        Each batch has at most MAX_QUESTIONS_PER_BATCH questions.

        Returns:
            List of QuestionBatch objects.
        """
        if not self._gaps:
            # No gap info - batch by position only
            batches: list[QuestionBatch] = []
            pending = self.pending_questions

            for i in range(0, len(pending), self.MAX_QUESTIONS_PER_BATCH):
                chunk = pending[i : i + self.MAX_QUESTIONS_PER_BATCH]
                batches.append(
                    QuestionBatch(
                        questions=chunk,
                        gap_type="general",
                        severity="warning",
                    )
                )
            return batches

        # Group by gap type and severity
        critical_by_type: dict[str, list[str]] = {}
        warning_by_type: dict[str, list[str]] = {}

        pending_set = set(self.pending_questions)

        for gap in self._gaps:
            if gap.suggested_question not in pending_set:
                continue

            gap_type = gap.gap_type.value
            if gap.severity == "critical":
                if gap_type not in critical_by_type:
                    critical_by_type[gap_type] = []
                critical_by_type[gap_type].append(gap.suggested_question)
            else:
                if gap_type not in warning_by_type:
                    warning_by_type[gap_type] = []
                warning_by_type[gap_type].append(gap.suggested_question)

        # Build batches: critical first, then warnings
        batches = []

        for gap_type, questions in critical_by_type.items():
            for i in range(0, len(questions), self.MAX_QUESTIONS_PER_BATCH):
                chunk = questions[i : i + self.MAX_QUESTIONS_PER_BATCH]
                batches.append(
                    QuestionBatch(
                        questions=chunk,
                        gap_type=gap_type,
                        severity="critical",
                    )
                )

        for gap_type, questions in warning_by_type.items():
            for i in range(0, len(questions), self.MAX_QUESTIONS_PER_BATCH):
                chunk = questions[i : i + self.MAX_QUESTIONS_PER_BATCH]
                batches.append(
                    QuestionBatch(
                        questions=chunk,
                        gap_type=gap_type,
                        severity="warning",
                    )
                )

        return batches

    def skip_question(self, question: str) -> None:
        """Mark a question as skipped.

        Args:
            question: The question to skip.
        """
        self._skipped.add(self._question_hash(question))

    def skip_all_optional(self) -> int:
        """Skip all questions with warning severity.

        Returns:
            Number of questions skipped.
        """
        if not self._gaps:
            return 0

        skipped_count = 0
        for gap in self._gaps:
            if gap.severity == "warning":
                question = gap.suggested_question
                if self._question_hash(question) not in self._answers:
                    self.skip_question(question)
                    skipped_count += 1

        return skipped_count

    def record_answer(self, question: str, answer: str) -> None:
        """Record an answer for a question.

        Args:
            question: The question that was answered.
            answer: The user's answer.
        """
        self._answers[self._question_hash(question)] = answer

    def get_answers_by_question(self) -> dict[str, str]:
        """Get answers keyed by question text (not hash).

        Returns:
            Dictionary mapping question text to answers.
        """
        result: dict[str, str] = {}
        for question in self._questions:
            q_hash = self._question_hash(question)
            if q_hash in self._answers:
                result[question] = self._answers[q_hash]
        return result

    def format_batch_for_tui(self, batch: QuestionBatch) -> list[FormattedQuestion]:
        """Format a batch of questions for AskUserQuestion tool.

        Args:
            batch: The question batch to format.

        Returns:
            List of formatted questions (max 4).
        """
        return [self.format_question_for_tui(q) for q in batch.questions[: self.MAX_QUESTIONS_PER_BATCH]]
