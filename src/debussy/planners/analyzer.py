"""Issue analyzer for detecting gaps and quality issues in GitHub issues.

This module analyzes GitHub issues to detect missing information critical
for plan generation. It produces structured reports identifying gaps
(missing acceptance criteria, no tech hints, unclear scope) and generates
questions to fill those gaps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from debussy.planners.models import GitHubIssue, IssueSet


class GapType(str, Enum):
    """Types of gaps that can be detected in an issue."""

    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    TECH_STACK = "tech_stack"
    DEPENDENCIES = "dependencies"
    VALIDATION = "validation"
    SCOPE = "scope"
    CONTEXT = "context"


# Q&A section header that Debussy adds to issues
QA_SECTION_HEADER = "## 📝 Clarifications (via Debussy Q&A)"

# Mapping from Q&A label patterns to GapType
# These are the labels used in github_fetcher._extract_qa_label()
QA_LABEL_TO_GAP_TYPE: dict[str, GapType] = {
    "acceptance criteria": GapType.ACCEPTANCE_CRITERIA,
    "done when": GapType.ACCEPTANCE_CRITERIA,
    "tech stack": GapType.TECH_STACK,
    "technologies": GapType.TECH_STACK,
    "depends on": GapType.DEPENDENCIES,
    "blocked by": GapType.DEPENDENCIES,
    "dependencies": GapType.DEPENDENCIES,
    "testing": GapType.VALIDATION,
    "validation": GapType.VALIDATION,
    "scope": GapType.SCOPE,
    "requirements": GapType.SCOPE,
    "context": GapType.CONTEXT,
    "problem": GapType.CONTEXT,
}


# Severity type for gaps
GapSeverity = Literal["critical", "warning"]


def _parse_qa_section(body: str) -> set[GapType]:
    """Parse a Debussy Q&A section to find which gap types have been answered.

    Looks for the Q&A section header and extracts labels to determine
    which gaps have already been addressed.

    Args:
        body: The issue body text.

    Returns:
        Set of GapType values that have been answered in the Q&A section.
    """
    if not body or QA_SECTION_HEADER not in body:
        return set()

    # Extract the Q&A section content (everything after the header)
    qa_start = body.find(QA_SECTION_HEADER)
    qa_content = body[qa_start:].lower()

    answered_gaps: set[GapType] = set()

    # Check for each label pattern
    for label_pattern, gap_type in QA_LABEL_TO_GAP_TYPE.items():
        # Look for **Label:** or **Label: pattern (bold markdown labels)
        if f"**{label_pattern}" in qa_content:
            answered_gaps.add(gap_type)

    return answered_gaps


@dataclass
class Gap:
    """A gap detected in an issue that needs to be addressed."""

    gap_type: GapType
    severity: GapSeverity
    issue_number: int
    description: str
    suggested_question: str


@dataclass
class IssueQuality:
    """Quality assessment for a single GitHub issue."""

    issue_number: int
    score: int  # 0-100
    gaps: list[Gap] = field(default_factory=list)
    has_problem: bool = False
    has_solution: bool = False
    has_criteria: bool = False
    has_validation: bool = False

    @property
    def critical_gap_count(self) -> int:
        """Count of critical severity gaps."""
        return sum(1 for gap in self.gaps if gap.severity == "critical")

    @property
    def warning_gap_count(self) -> int:
        """Count of warning severity gaps."""
        return sum(1 for gap in self.gaps if gap.severity == "warning")


@dataclass
class AnalysisReport:
    """Report from analyzing a set of issues."""

    issues: list[IssueQuality] = field(default_factory=list)

    @property
    def total_gaps(self) -> int:
        """Total number of gaps across all issues."""
        return sum(len(iq.gaps) for iq in self.issues)

    @property
    def critical_gaps(self) -> int:
        """Total number of critical gaps across all issues."""
        return sum(iq.critical_gap_count for iq in self.issues)

    @property
    def questions_needed(self) -> list[str]:
        """List of questions to ask based on detected gaps."""
        questions = []
        for iq in self.issues:
            for gap in iq.gaps:
                questions.append(gap.suggested_question)
        return questions

    @property
    def average_score(self) -> float:
        """Average quality score across all issues."""
        if not self.issues:
            return 0.0
        return sum(iq.score for iq in self.issues) / len(self.issues)


# =============================================================================
# Gap Detection Keywords
# =============================================================================

# Keywords indicating acceptance criteria presence
ACCEPTANCE_CRITERIA_KEYWORDS = frozenset(
    {
        "acceptance",
        "criteria",
        "done when",
        "definition of done",
        "dod",
        "requirements",
        "must have",
        "should",
        "shall",
    }
)

# Tech stack keywords
TECH_STACK_KEYWORDS = frozenset(
    {
        # Languages
        "python",
        "javascript",
        "typescript",
        "go",
        "rust",
        "java",
        "ruby",
        "c#",
        "kotlin",
        "swift",
        # Backend frameworks
        "flask",
        "django",
        "fastapi",
        "express",
        "node",
        "nodejs",
        "rails",
        "spring",
        "asp.net",
        # Frontend frameworks
        "react",
        "vue",
        "angular",
        "svelte",
        "nextjs",
        "next.js",
        "gatsby",
        "nuxt",
        # Databases
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "sqlite",
        "dynamodb",
        "cassandra",
        # Testing
        "pytest",
        "jest",
        "mocha",
        "cypress",
        "selenium",
        "playwright",
        # Other
        "docker",
        "kubernetes",
        "k8s",
        "graphql",
        "rest",
        "api",
        "websocket",
        "grpc",
    }
)

# Dependency-related keywords
DEPENDENCY_KEYWORDS = frozenset(
    {
        "depends",
        "depends on",
        "requires",
        "requires that",
        "blocked",
        "blocked by",
        "after",
        "before",
        "prerequisite",
        "prerequisite for",
        "blocks",
        "dependent",
    }
)

# Validation/testing keywords
VALIDATION_KEYWORDS = frozenset(
    {
        "test",
        "tests",
        "testing",
        "pytest",
        "jest",
        "mocha",
        "coverage",
        "unit test",
        "integration test",
        "e2e",
        "end-to-end",
        "validation",
        "verify",
        "verified",
        "qa",
        "quality assurance",
    }
)

# Context/problem keywords
CONTEXT_KEYWORDS = frozenset(
    {
        "problem",
        "background",
        "context",
        "currently",
        "issue",
        "bug",
        "error",
        "situation",
        "use case",
        "scenario",
        "motivation",
        "reason",
        "why",
        "purpose",
    }
)


# =============================================================================
# Question Templates
# =============================================================================

QUESTION_TEMPLATES = {
    GapType.ACCEPTANCE_CRITERIA: ("Issue #{number} '{title}' has no acceptance criteria. What defines 'done' for this issue?"),
    GapType.TECH_STACK: ("Issue #{number} '{title}' doesn't mention technologies. What frameworks/languages will be used?"),
    GapType.DEPENDENCIES: ("Issue #{number} '{title}' has no dependency information. Does this issue depend on or block any other work?"),
    GapType.VALIDATION: ("Issue #{number} '{title}' has no validation requirements. What test framework and coverage target should be used?"),
    GapType.SCOPE: ("Issue #{number} '{title}' has limited details. Can you provide more information about the scope and requirements?"),
    GapType.CONTEXT: ("Issue #{number} '{title}' lacks problem context. What is the current situation and why is this change needed?"),
}


# =============================================================================
# Gap Detection Functions
# =============================================================================


def _has_checkbox_items(text: str) -> bool:
    """Check if text contains checkbox items."""
    return bool(re.search(r"- \[[ x]\]", text, re.IGNORECASE))


def _has_keywords(text: str, keywords: frozenset[str]) -> bool:
    """Check if text contains any of the given keywords."""
    text_lower = text.lower()
    for keyword in keywords:
        # Handle multi-word keywords
        if " " in keyword:
            if keyword in text_lower:
                return True
        # Use word boundary for single words
        elif re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return True
    return False


def _has_section(text: str, section_names: list[str]) -> bool:
    """Check if text contains a markdown section with one of the given names."""
    for name in section_names:
        # Match ## Section Name or ### Section Name
        pattern = rf"^#{1, 3}\s*{re.escape(name)}"
        if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
            return True
    return False


def detect_acceptance_criteria_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue is missing acceptance criteria.

    Checks for:
    - Checkbox items (- [ ])
    - Keywords like 'acceptance', 'criteria', 'done when'
    - Section headers like '## Acceptance Criteria'

    Returns:
        Gap if acceptance criteria is missing, None otherwise.
    """
    body = issue.body or ""

    # Check for checkbox items
    if _has_checkbox_items(body):
        return None

    # Check for acceptance criteria keywords
    if _has_keywords(body, ACCEPTANCE_CRITERIA_KEYWORDS):
        return None

    # Check for acceptance criteria section
    if _has_section(body, ["Acceptance Criteria", "Acceptance", "Criteria", "Definition of Done"]):
        return None

    return Gap(
        gap_type=GapType.ACCEPTANCE_CRITERIA,
        severity="critical",
        issue_number=issue.number,
        description="No acceptance criteria found",
        suggested_question=QUESTION_TEMPLATES[GapType.ACCEPTANCE_CRITERIA].format(number=issue.number, title=issue.title),
    )


def detect_tech_stack_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue is missing technology/framework mentions.

    Returns:
        Gap if tech stack is missing, None otherwise.
    """
    body = issue.body or ""
    title = issue.title or ""
    combined = f"{title} {body}"

    if _has_keywords(combined, TECH_STACK_KEYWORDS):
        return None

    return Gap(
        gap_type=GapType.TECH_STACK,
        severity="warning",
        issue_number=issue.number,
        description="No technology or framework mentions found",
        suggested_question=QUESTION_TEMPLATES[GapType.TECH_STACK].format(number=issue.number, title=issue.title),
    )


def detect_dependencies_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue has no dependency information.

    Returns:
        Gap if dependencies info is missing, None otherwise.
    """
    body = issue.body or ""
    title = issue.title or ""
    combined = f"{title} {body}"

    if _has_keywords(combined, DEPENDENCY_KEYWORDS):
        return None

    # Also check for GitHub-style references like #123
    if re.search(r"#\d+", combined):
        return None

    return Gap(
        gap_type=GapType.DEPENDENCIES,
        severity="warning",
        issue_number=issue.number,
        description="No dependency information found",
        suggested_question=QUESTION_TEMPLATES[GapType.DEPENDENCIES].format(number=issue.number, title=issue.title),
    )


def detect_validation_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue has no validation/testing requirements.

    Returns:
        Gap if validation info is missing, None otherwise.
    """
    body = issue.body or ""
    title = issue.title or ""
    combined = f"{title} {body}"

    if _has_keywords(combined, VALIDATION_KEYWORDS):
        return None

    # Check for testing section
    if _has_section(body, ["Test", "Tests", "Testing", "Validation", "QA"]):
        return None

    return Gap(
        gap_type=GapType.VALIDATION,
        severity="critical",
        issue_number=issue.number,
        description="No validation or testing requirements found",
        suggested_question=QUESTION_TEMPLATES[GapType.VALIDATION].format(number=issue.number, title=issue.title),
    )


def detect_scope_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue has unclear or minimal scope.

    Warns if:
    - Body is less than 100 characters
    - Body lacks markdown structure (no headers)

    Returns:
        Gap if scope is unclear, None otherwise.
    """
    body = issue.body or ""

    # Check minimum length
    if len(body) < 100:
        return Gap(
            gap_type=GapType.SCOPE,
            severity="warning",
            issue_number=issue.number,
            description=f"Issue body is too short ({len(body)} chars < 100)",
            suggested_question=QUESTION_TEMPLATES[GapType.SCOPE].format(number=issue.number, title=issue.title),
        )

    # Check for markdown structure (headers or lists)
    # No headers and no list structure is a warning
    has_headers = bool(re.search(r"^#{1,3}\s+", body, re.MULTILINE))
    has_lists = bool(re.search(r"^[-*]\s+", body, re.MULTILINE))
    if not has_headers and not has_lists:
        return Gap(
            gap_type=GapType.SCOPE,
            severity="warning",
            issue_number=issue.number,
            description="Issue body lacks markdown structure",
            suggested_question=QUESTION_TEMPLATES[GapType.SCOPE].format(number=issue.number, title=issue.title),
        )

    return None


def detect_context_gap(issue: GitHubIssue) -> Gap | None:
    """Detect if an issue lacks problem/background context.

    Returns:
        Gap if context is missing, None otherwise.
    """
    body = issue.body or ""
    title = issue.title or ""
    combined = f"{title} {body}"

    if _has_keywords(combined, CONTEXT_KEYWORDS):
        return None

    # Check for context sections
    if _has_section(body, ["Problem", "Background", "Context", "Motivation", "Why"]):
        return None

    return Gap(
        gap_type=GapType.CONTEXT,
        severity="warning",
        issue_number=issue.number,
        description="No problem or context description found",
        suggested_question=QUESTION_TEMPLATES[GapType.CONTEXT].format(number=issue.number, title=issue.title),
    )


# =============================================================================
# Quality Score Calculation
# =============================================================================

# Quality score weights (must sum to 100)
QUALITY_WEIGHTS = {
    "acceptance_criteria": 30,
    "validation": 25,
    "tech_stack": 15,
    "context": 10,
    "dependencies": 10,
    "structured_body": 10,
}


def calculate_quality_score(issue: GitHubIssue) -> tuple[int, dict[str, bool]]:
    """Calculate quality score for an issue.

    Returns:
        Tuple of (score 0-100, dict of which criteria are met).
    """
    body = issue.body or ""
    title = issue.title or ""
    combined = f"{title} {body}"

    criteria_met: dict[str, bool] = {
        "acceptance_criteria": False,
        "validation": False,
        "tech_stack": False,
        "context": False,
        "dependencies": False,
        "structured_body": False,
    }

    # Check acceptance criteria
    if _has_checkbox_items(body) or _has_keywords(body, ACCEPTANCE_CRITERIA_KEYWORDS) or _has_section(body, ["Acceptance Criteria", "Acceptance", "Criteria"]):
        criteria_met["acceptance_criteria"] = True

    # Check validation
    if _has_keywords(combined, VALIDATION_KEYWORDS) or _has_section(body, ["Test", "Tests", "Testing", "Validation"]):
        criteria_met["validation"] = True

    # Check tech stack
    if _has_keywords(combined, TECH_STACK_KEYWORDS):
        criteria_met["tech_stack"] = True

    # Check context
    if _has_keywords(combined, CONTEXT_KEYWORDS) or _has_section(body, ["Problem", "Background", "Context", "Motivation"]):
        criteria_met["context"] = True

    # Check dependencies
    if _has_keywords(combined, DEPENDENCY_KEYWORDS) or re.search(r"#\d+", combined):
        criteria_met["dependencies"] = True

    # Check structured body (>200 chars and has headers or lists)
    has_structure = len(body) > 200 and (re.search(r"^#{1,3}\s+", body, re.MULTILINE) or re.search(r"^[-*]\s+", body, re.MULTILINE))
    if has_structure:
        criteria_met["structured_body"] = True

    # Calculate score
    score = sum(QUALITY_WEIGHTS[key] for key, met in criteria_met.items() if met)

    return score, criteria_met


# =============================================================================
# Issue Analyzer Class
# =============================================================================


class IssueAnalyzer:
    """Analyzes GitHub issues for gaps and quality."""

    def analyze_issue(self, issue: GitHubIssue) -> IssueQuality:
        """Analyze a single issue and return its quality assessment.

        Args:
            issue: The GitHub issue to analyze.

        Returns:
            IssueQuality with gaps and score.
        """
        gaps: list[Gap] = []

        # Check if issue has a Debussy Q&A section with answered gaps
        answered_gaps = _parse_qa_section(issue.body or "")

        # Run all gap detection functions
        gap_detectors = [
            detect_acceptance_criteria_gap,
            detect_tech_stack_gap,
            detect_dependencies_gap,
            detect_validation_gap,
            detect_scope_gap,
            detect_context_gap,
        ]

        for detector in gap_detectors:
            gap = detector(issue)
            if gap is not None:
                # Skip gaps that were already answered in Q&A section
                if gap.gap_type in answered_gaps:
                    continue
                gaps.append(gap)

        # Calculate quality score and criteria
        score, criteria_met = calculate_quality_score(issue)

        return IssueQuality(
            issue_number=issue.number,
            score=score,
            gaps=gaps,
            has_problem=criteria_met["context"],
            has_solution=False,  # Would need more sophisticated detection
            has_criteria=criteria_met["acceptance_criteria"],
            has_validation=criteria_met["validation"],
        )

    def analyze_issue_set(self, issue_set: IssueSet) -> AnalysisReport:
        """Analyze a set of issues and return an aggregated report.

        Args:
            issue_set: The set of issues to analyze.

        Returns:
            AnalysisReport with all issue assessments.
        """
        issue_qualities = [self.analyze_issue(issue) for issue in issue_set.issues]
        return AnalysisReport(issues=issue_qualities)

    def generate_questions(self, report: AnalysisReport) -> list[str]:
        """Generate user-friendly questions from an analysis report.

        Args:
            report: The analysis report to generate questions from.

        Returns:
            List of questions to ask the user.
        """
        return report.questions_needed

    def prioritize_gaps(self, report: AnalysisReport) -> list[Gap]:
        """Get all gaps sorted by severity and grouped by type.

        Critical gaps come first, then warnings.
        Within each severity level, gaps are grouped by type.

        Args:
            report: The analysis report.

        Returns:
            Sorted list of gaps.
        """
        all_gaps: list[Gap] = []
        for iq in report.issues:
            all_gaps.extend(iq.gaps)

        # Sort by severity (critical first), then by gap type
        return sorted(
            all_gaps,
            key=lambda g: (0 if g.severity == "critical" else 1, g.gap_type.value),
        )
