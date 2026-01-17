"""Q&A handler for interactive gap-filling during plan generation.

This module provides the QAHandler class that manages interactive
question-and-answer sessions to fill gaps detected in issue analysis.

Two-pass integration with Claude Code:
    1. Run with --questions-only to collect all questions as JSON
    2. Claude Code presents questions via AskUserQuestion
    3. Run with --answers-file to inject pre-collected answers
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from debussy.planners.analyzer import Gap

# Configure module logger
logger = logging.getLogger(__name__)


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


@dataclass
class CollectedQuestion:
    """A question collected for the two-pass flow."""

    question: str
    gap_type: str
    context: str
    issue_number: int | None = None


class QAHandler:
    """Manages interactive Q&A sessions for gap-filling.

    Handles batching related questions, formatting for TUI display,
    and tracking user answers.

    Supports two modes of operation:
        - Interactive: Direct terminal prompts (default)
        - Pre-answered: Load answers from JSON file (--answers-file)
    """

    MAX_QUESTIONS_PER_BATCH = 4

    def __init__(
        self,
        questions: list[str],
        gaps: list[Gap] | None = None,
        answers_file: Path | None = None,
    ) -> None:
        """Initialize the Q&A handler.

        Args:
            questions: List of questions to ask.
            gaps: Optional list of Gap objects for context. If provided,
                  enables better question batching by gap type and severity.
            answers_file: Optional path to JSON file with pre-collected answers.
        """
        self._questions = questions
        self._gaps = gaps
        self._answers: dict[str, str] = {}
        self._skipped: set[str] = set()
        self._pre_loaded_answers: dict[str, str] = {}

        # Load pre-collected answers if provided
        if answers_file:
            self._load_answers_file(answers_file)

    def _load_answers_file(self, answers_file: Path) -> None:
        """Load pre-collected answers from a JSON file.

        Args:
            answers_file: Path to JSON file with answers.
        """
        try:
            with answers_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Expected format: {"answers": [{"question": "...", "answer": "..."}, ...]}
            if isinstance(data, dict) and "answers" in data:
                for item in data["answers"]:
                    if "question" in item and "answer" in item:
                        self._pre_loaded_answers[item["question"]] = item["answer"]
                logger.info(f"Loaded {len(self._pre_loaded_answers)} pre-collected answers from {answers_file}")
            else:
                logger.warning(f"Invalid answers file format: {answers_file}")
        except Exception as e:
            logger.error(f"Failed to load answers file {answers_file}: {e}")

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

    def ask_questions_interactive(self) -> dict[str, str]:
        """Conduct interactive Q&A session.

        If pre-loaded answers are available, uses those instead of prompting.
        Falls back to terminal prompts for questions without pre-loaded answers.

        Returns:
            Dictionary mapping question hashes to user answers.
        """
        for question in self.pending_questions:
            # Check for pre-loaded answer first
            if question in self._pre_loaded_answers:
                answer = self._pre_loaded_answers[question]
                logger.debug(f"Using pre-loaded answer for: {question[:50]}...")
            else:
                # Fall back to terminal prompt
                answer = self._prompt_terminal(question)

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
        # Check for pre-loaded answer first
        if question in self._pre_loaded_answers:
            return self._pre_loaded_answers[question]
        return self._prompt_terminal(question)

    def collect_questions_for_export(self) -> list[CollectedQuestion]:
        """Collect all questions in a structured format for export.

        Used by --questions-only mode to output questions as JSON.

        Returns:
            List of CollectedQuestion objects ready for JSON serialization.
        """
        import re

        collected: list[CollectedQuestion] = []

        for question in self._questions:
            gap = self._get_gap_for_question(question)
            gap_type = gap.gap_type.value if gap else "general"
            context = gap.description if gap else ""

            # Extract issue number from question text
            issue_number = None
            match = re.search(r"Issue #(\d+)", question)
            if match:
                issue_number = int(match.group(1))

            collected.append(
                CollectedQuestion(
                    question=question,
                    gap_type=gap_type,
                    context=context,
                    issue_number=issue_number,
                )
            )

        return collected

    def export_questions_json(self) -> str:
        """Export all questions as JSON string.

        Returns:
            JSON string with questions array.
        """
        questions = self.collect_questions_for_export()
        data = {
            "questions": [
                {
                    "question": q.question,
                    "gap_type": q.gap_type,
                    "context": q.context,
                    "issue_number": q.issue_number,
                }
                for q in questions
            ]
        }
        return json.dumps(data, indent=2)

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
