"""Data models for GitHub issue representation and Q&A pipe protocol.

These models represent the structure of GitHub issues as fetched
via the gh CLI tool, as well as the structured IPC protocol for
pipe-mode Q&A communication with Claude Code.

Q&A Pipe Protocol:
    When DEBUSSY_QA_PIPE=1 is set, questions are emitted as JSON to stdout
    and answers are read as JSON from stdin. This enables parent processes
    (like Claude Code) to intercept Q&A sessions and route them through
    their own UI (e.g., AskUserQuestion tool).

    Question format (stdout):
        {"type": "question", "gap_type": "tech_stack", "question": "...", "options": [...], "context": "..."}

    Answer format (stdin):
        {"type": "answer", "gap_type": "tech_stack", "answer": "PostgreSQL"}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Q&A Pipe Protocol Models
# =============================================================================


class QAMode(str, Enum):
    """Mode for Q&A interaction.

    TERMINAL: Interactive prompts via stdin/stdout (default behavior).
    PIPE: JSON IPC via stdout (questions) and stdin (answers) for
          integration with parent processes like Claude Code.
    """

    TERMINAL = "terminal"
    PIPE = "pipe"


class QAQuestion(BaseModel):
    """A question emitted in pipe mode for the parent process.

    JSON Schema:
        {
            "type": "question",
            "gap_type": "tech_stack",
            "question": "Which database will this project use?",
            "options": ["PostgreSQL", "MySQL", "SQLite", "MongoDB"],
            "context": "No database mentioned in issues"
        }
    """

    type: Literal["question"] = Field(default="question", description="Message type discriminator")
    gap_type: str = Field(..., description="The type of gap this question addresses (e.g., tech_stack, acceptance_criteria)")
    question: str = Field(..., description="The question text to present to the user")
    options: list[str] = Field(default_factory=list, description="Suggested answer options (may be empty for open-ended questions)")
    context: str = Field(default="", description="Additional context about why this question is being asked")


class QAAnswer(BaseModel):
    """An answer received in pipe mode from the parent process.

    JSON Schema:
        {
            "type": "answer",
            "gap_type": "tech_stack",
            "answer": "PostgreSQL"
        }
    """

    type: Literal["answer"] = Field(default="answer", description="Message type discriminator")
    gap_type: str = Field(..., description="The type of gap this answer addresses (must match the question's gap_type)")
    answer: str = Field(..., description="The user's answer to the question")


# Union type for type-safe message handling
QAMessage = QAQuestion | QAAnswer


@dataclass
class IssueLabel:
    """A label attached to a GitHub issue."""

    name: str
    description: str | None = None


@dataclass
class IssueMilestone:
    """A milestone associated with a GitHub issue."""

    title: str
    description: str | None = None
    due_on: datetime | None = None


@dataclass
class GitHubIssue:
    """A GitHub issue with its metadata.

    Represents an issue as returned by `gh issue list --json`.
    """

    number: int
    title: str
    body: str
    labels: list[IssueLabel] = field(default_factory=list)
    state: str = "OPEN"
    milestone: IssueMilestone | None = None
    assignees: list[str] = field(default_factory=list)
    url: str = ""

    @property
    def is_open(self) -> bool:
        """Check if the issue is open."""
        return self.state.upper() == "OPEN"

    @property
    def is_closed(self) -> bool:
        """Check if the issue is closed."""
        return self.state.upper() == "CLOSED"

    @property
    def label_names(self) -> list[str]:
        """Get a list of label names for this issue."""
        return [label.name for label in self.labels]


@dataclass
class IssueSet:
    """A collection of GitHub issues with metadata about the fetch.

    Stores the issues along with information about how and when
    they were fetched.
    """

    issues: list[GitHubIssue] = field(default_factory=list)
    source: str = ""
    filter_used: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)

    def __len__(self) -> int:
        """Return the number of issues in the set."""
        return len(self.issues)

    def __iter__(self):
        """Iterate over the issues."""
        return iter(self.issues)

    @property
    def open_issues(self) -> list[GitHubIssue]:
        """Get all open issues in the set."""
        return [issue for issue in self.issues if issue.is_open]

    @property
    def closed_issues(self) -> list[GitHubIssue]:
        """Get all closed issues in the set."""
        return [issue for issue in self.issues if issue.is_closed]
