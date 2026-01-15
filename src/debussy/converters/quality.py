"""Quality metrics for evaluating plan conversion fidelity.

This module provides metrics to evaluate how well a converted plan preserves
the content and intent of the original freeform plan.

Metrics are organized in tiers by complexity:
- Tier 1: Deterministic checks (phase count, agents, filenames)
- Tier 2: Keyword extraction (tech stack, task keywords, risk mentions)
- Tier 3a: Jaccard similarity (word-level overlap, no ML deps)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# =============================================================================
# Tier 1: Deterministic Checks
# =============================================================================


def count_phases_in_freeform(content: str) -> int:
    """Count phases in freeform plan content.

    Detects common patterns:
    - "### Phase:" or "## Phase:" headers
    - "Phase 1:", "Phase 2:" numbered
    - "Sprint 1:", "Sprint 2:" agile style
    - "Module 1:", "Module 2:" modular style

    Args:
        content: Raw markdown content of the source plan.

    Returns:
        Estimated number of phases/sprints/modules found.
    """
    patterns = [
        r"^#{1,3}\s*Phase[:\s]",  # ### Phase: or ## Phase
        r"^#{1,3}\s*Phase\s+\d+",  # ### Phase 1
        r"^#{1,3}\s*Sprint[:\s]",  # ### Sprint:
        r"^#{1,3}\s*Sprint\s+\d+",  # ### Sprint 1
        r"^#{1,3}\s*Module[:\s]",  # ### Module:
        r"^#{1,3}\s*Module\s+\d+",  # ### Module 1
        r"^\d+\.\s*(Phase|Sprint|Module)",  # 1. Phase, 2. Sprint
    ]

    combined = "|".join(f"({p})" for p in patterns)
    matches = re.findall(combined, content, re.MULTILINE | re.IGNORECASE)
    return len(matches)


def count_phases_in_directory(source_dir: Path) -> int:
    """Count phases by looking at separate phase files in directory.

    Args:
        source_dir: Directory containing source plan files.

    Returns:
        Number of phase-like files found (excluding master/overview files).
    """
    if not source_dir.is_dir():
        return 0

    # Common patterns for phase files
    phase_patterns = [
        r"phase[-_]?\d+",
        r"sprint[-_]?\d+",
        r"module[-_]?\d+",
        r".*_phase\.md$",
        r".*_sprint\.md$",
        r".*_module\.md$",
    ]

    # Files to exclude (master/overview)
    exclude_patterns = [
        r"master",
        r"overview",
        r"readme",
        r"project_plan",
        r"plan_overview",
    ]

    count = 0
    for md_file in source_dir.glob("*.md"):
        name = md_file.stem.lower()

        # Skip master/overview files
        if any(re.search(p, name) for p in exclude_patterns):
            continue

        # Count if matches phase pattern
        if any(re.search(p, name) for p in phase_patterns):
            count += 1

    return count


def check_filename_convention(output_dir: Path) -> tuple[bool, list[str]]:
    """Check if output files follow Debussy naming convention.

    Expected pattern: phase-{N}.md or phase-{N}-{title}.md

    Args:
        output_dir: Directory containing converted plan files.

    Returns:
        Tuple of (all_valid, list of invalid filenames).
    """
    invalid = []
    valid_pattern = re.compile(r"^phase-\d+(-[\w-]+)?\.md$", re.IGNORECASE)

    for md_file in output_dir.glob("phase-*.md"):
        if not valid_pattern.match(md_file.name.lower()):
            invalid.append(md_file.name)

    return len(invalid) == 0, invalid


def check_master_plan_exists(output_dir: Path) -> bool:
    """Check if MASTER_PLAN.md exists in output directory."""
    return (output_dir / "MASTER_PLAN.md").exists()


# =============================================================================
# Tier 2: Keyword Extraction
# =============================================================================


# Common technology keywords to look for
TECH_KEYWORDS = frozenset({
    # Languages
    "python", "javascript", "typescript", "go", "rust", "java", "ruby",
    # Backend frameworks
    "flask", "django", "fastapi", "express", "node", "nodejs", "rails",
    # Frontend frameworks
    "react", "vue", "angular", "svelte", "nextjs", "next.js",
    # Databases
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite",
    # Auth
    "jwt", "oauth", "auth0", "cognito",
    # Cloud/Infra
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
    # Testing
    "pytest", "jest", "mocha", "cypress",
    # Other
    "graphql", "rest", "api", "websocket", "celery", "rabbitmq",
})


# Agent names that should be preserved
AGENT_KEYWORDS = frozenset({
    "python-task-validator",
    "textual-tui-expert",
    "llm-security-expert",
    "explore",
    "debussy",
})


# Risk-related terms
RISK_KEYWORDS = frozenset({
    "risk", "risks", "mitigation", "mitigate",
    "blocker", "blockers", "dependency", "dependencies",
    "concern", "concerns", "issue", "issues",
    "critical", "high-priority", "security",
})


def extract_keywords(text: str, vocabulary: frozenset[str]) -> set[str]:
    """Extract keywords from text that match a vocabulary set.

    Args:
        text: Source text to search.
        vocabulary: Set of keywords to look for.

    Returns:
        Set of matched keywords found in text.
    """
    text_lower = text.lower()
    # Use word boundaries for more accurate matching
    found = set()
    for keyword in vocabulary:
        # Handle multi-word keywords (like "python-task-validator")
        if "-" in keyword or "_" in keyword:
            if keyword in text_lower:
                found.add(keyword)
        # Use word boundary matching for single words
        elif re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            found.add(keyword)
    return found


def extract_tech_stack(text: str) -> set[str]:
    """Extract technology keywords from text."""
    return extract_keywords(text, TECH_KEYWORDS)


def extract_agent_references(text: str) -> set[str]:
    """Extract agent names from text."""
    return extract_keywords(text, AGENT_KEYWORDS)


def extract_risk_mentions(text: str) -> set[str]:
    """Extract risk-related terms from text."""
    return extract_keywords(text, RISK_KEYWORDS)


def extract_task_keywords(text: str) -> set[str]:
    """Extract task action verbs from markdown task lines.

    Looks for `- [ ]` lines and extracts the main action verb.
    Handles numbered task prefixes like "1.1:" or "2.3:".

    Args:
        text: Markdown content with task checkboxes.

    Returns:
        Set of action verbs found in tasks.
    """
    action_verbs = set()

    # Match task lines: - [ ] or - [x] followed by text
    task_pattern = re.compile(r"^\s*-\s*\[[ x]\]\s*(.+)$", re.MULTILINE | re.IGNORECASE)

    # Pattern for numbered prefixes like "1.1:" or "2.3:"
    number_prefix = re.compile(r"^\d+(\.\d+)?:\s*")

    for match in task_pattern.finditer(text):
        task_text = match.group(1).strip()

        # Strip numbered prefix if present
        task_text = number_prefix.sub("", task_text)

        # Extract first word (likely the verb)
        words = task_text.split()
        if words:
            # Clean up: remove numbers, special chars
            verb = re.sub(r"[^a-zA-Z]", "", words[0].lower())
            if verb and len(verb) > 2:  # Filter out short non-words
                action_verbs.add(verb)

    return action_verbs


# =============================================================================
# Tier 3a: Jaccard Similarity
# =============================================================================

# Common stopwords to filter out (minimal set to avoid dependencies)
STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "our", "you", "your", "he", "she", "his", "her", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "also", "now", "here", "there", "when", "where", "why", "how", "what",
    "which", "who", "whom", "if", "then", "else", "because", "while",
    "although", "though", "after", "before", "during", "until", "unless",
})

# Template boilerplate phrases to strip (Debussy-specific)
TEMPLATE_BOILERPLATE = [
    # Process wrapper boilerplate
    r"Process Wrapper \(MANDATORY\)",
    r"Read previous notes:.*",
    r"\*\*\[IMPLEMENTATION - see Tasks below\]\*\*",
    r"Pre-validation \(ALL required\):",
    r"Fix loop: repeat pre-validation until clean",
    r"Write `notes/NOTES_.*\.md` \(REQUIRED\)",
    # Gate boilerplate
    r"Gates \(must pass before completion\)",
    r"\*\*ALL gates are BLOCKING\.\*\*",
    r"lint: 0 errors \(command:.*\)",
    r"type-check: 0 errors \(command:.*\)",
    r"tests: All tests pass \(command:.*\)",
    r"security: No high severity issues \(command:.*\)",
    # Common commands
    r"uv run ruff format.*",
    r"uv run ruff check.*",
    r"uv run pyright.*",
    r"uv run pytest.*",
    r"uv run bandit.*",
    r"npm run lint.*",
    r"npm run type-check.*",
    r"npm test.*",
    # Status markers
    r"\*\*Status:\*\* Pending",
    r"\*\*Master Plan:\*\*.*",
    r"\*\*Depends On:\*\*.*",
    r"\*\*Created:\*\*.*",
]


def preprocess_markdown(text: str, strip_boilerplate: bool = True) -> str:
    """Preprocess markdown text for similarity comparison.

    Removes:
    - Markdown syntax (headers, bold, italic, links, code blocks)
    - Table formatting
    - Template boilerplate (optional)
    - Extra whitespace

    Args:
        text: Raw markdown text.
        strip_boilerplate: Whether to remove Debussy template boilerplate.

    Returns:
        Cleaned plain text for comparison.
    """
    result = text

    # Remove code blocks (fenced and inline)
    result = re.sub(r"```[\s\S]*?```", " ", result)
    result = re.sub(r"`[^`]+`", " ", result)

    # Remove HTML tags if any
    result = re.sub(r"<[^>]+>", " ", result)

    # Remove markdown links but keep link text: [text](url) -> text
    result = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", result)

    # Remove image syntax: ![alt](url) -> alt
    result = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", result)

    # Remove headers (keep the text)
    result = re.sub(r"^#{1,6}\s+", "", result, flags=re.MULTILINE)

    # Remove bold/italic markers
    result = re.sub(r"\*\*([^*]+)\*\*", r"\1", result)
    result = re.sub(r"\*([^*]+)\*", r"\1", result)
    result = re.sub(r"__([^_]+)__", r"\1", result)
    result = re.sub(r"_([^_]+)_", r"\1", result)

    # Remove table formatting (keep cell content)
    result = re.sub(r"\|", " ", result)
    result = re.sub(r"^[\s\-:]+$", "", result, flags=re.MULTILINE)

    # Remove horizontal rules
    result = re.sub(r"^[\-*_]{3,}$", "", result, flags=re.MULTILINE)

    # Remove list markers
    result = re.sub(r"^\s*[-*+]\s+", " ", result, flags=re.MULTILINE)
    result = re.sub(r"^\s*\d+\.\s+", " ", result, flags=re.MULTILINE)

    # Remove checkbox markers
    result = re.sub(r"\[[ x]\]", " ", result, flags=re.IGNORECASE)

    # Remove blockquotes
    result = re.sub(r"^>\s*", "", result, flags=re.MULTILINE)

    # Strip template boilerplate if requested
    if strip_boilerplate:
        for pattern in TEMPLATE_BOILERPLATE:
            result = re.sub(pattern, " ", result, flags=re.IGNORECASE)

    # Normalize whitespace
    result = re.sub(r"\s+", " ", result)

    return result.strip()


def tokenize(text: str, preprocess: bool = False, remove_stopwords: bool = False) -> set[str]:
    """Tokenize text into lowercase words.

    Args:
        text: Text to tokenize.
        preprocess: Whether to apply markdown preprocessing first.
        remove_stopwords: Whether to remove common stopwords.

    Returns:
        Set of lowercase word tokens.
    """
    if preprocess:
        text = preprocess_markdown(text)

    # Remove remaining non-word chars, keep alphanumeric and hyphens
    cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
    words = cleaned.split()

    # Filter short words and pure numbers
    tokens = {w for w in words if len(w) > 2 and not w.isdigit()}

    if remove_stopwords:
        tokens = tokens - STOPWORDS

    return tokens


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts (raw, no preprocessing).

    Jaccard = |A intersection B| / |A union B|

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    words1 = tokenize(text1)
    words2 = tokenize(text2)

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def preprocessed_jaccard_similarity(
    text1: str,
    text2: str,
    remove_stopwords: bool = True,
) -> float:
    """Calculate Jaccard similarity with markdown preprocessing.

    Strips markdown syntax, template boilerplate, and optionally stopwords
    before calculating similarity. This gives a cleaner comparison of
    actual content.

    Args:
        text1: First markdown text.
        text2: Second markdown text.
        remove_stopwords: Whether to remove common stopwords.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    words1 = tokenize(text1, preprocess=True, remove_stopwords=remove_stopwords)
    words2 = tokenize(text2, preprocess=True, remove_stopwords=remove_stopwords)

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def weighted_jaccard_similarity(
    text1: str,
    text2: str,
    important_terms: frozenset[str] | set[str] | None = None,
    weight: float = 2.0,
) -> float:
    """Jaccard similarity with higher weight for important terms (raw, no preprocessing).

    Args:
        text1: First text.
        text2: Second text.
        important_terms: Terms to weight more heavily.
        weight: Multiplier for important terms (default 2.0).

    Returns:
        Weighted similarity score between 0.0 and 1.0.
    """
    words1 = tokenize(text1)
    words2 = tokenize(text2)

    if not words1 or not words2:
        return 0.0

    terms = TECH_KEYWORDS | AGENT_KEYWORDS if important_terms is None else important_terms

    # Calculate weighted intersection and union
    intersection = words1 & words2
    union = words1 | words2

    # Weight important terms
    weighted_intersection = 0.0
    weighted_union = 0.0

    for word in union:
        w = weight if word in terms else 1.0
        weighted_union += w
        if word in intersection:
            weighted_intersection += w

    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0


def preprocessed_weighted_jaccard(
    text1: str,
    text2: str,
    important_terms: frozenset[str] | set[str] | None = None,
    weight: float = 2.0,
    remove_stopwords: bool = True,
) -> float:
    """Weighted Jaccard with markdown preprocessing.

    Combines preprocessing (strip markdown, boilerplate) with weighted
    scoring for important terms.

    Args:
        text1: First markdown text.
        text2: Second markdown text.
        important_terms: Terms to weight more heavily.
        weight: Multiplier for important terms (default 2.0).
        remove_stopwords: Whether to remove common stopwords.

    Returns:
        Weighted similarity score between 0.0 and 1.0.
    """
    words1 = tokenize(text1, preprocess=True, remove_stopwords=remove_stopwords)
    words2 = tokenize(text2, preprocess=True, remove_stopwords=remove_stopwords)

    if not words1 or not words2:
        return 0.0

    terms = TECH_KEYWORDS | AGENT_KEYWORDS if important_terms is None else important_terms

    intersection = words1 & words2
    union = words1 | words2

    weighted_intersection = 0.0
    weighted_union = 0.0

    for word in union:
        w = weight if word in terms else 1.0
        weighted_union += w
        if word in intersection:
            weighted_intersection += w

    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0


# =============================================================================
# ConversionQuality Dataclass
# =============================================================================


@dataclass
class ConversionQuality:
    """Comprehensive conversion quality metrics.

    Combines Tier 1-3a metrics for evaluating conversion fidelity.
    """

    # Tier 1: Deterministic checks
    source_phase_count: int = 0
    converted_phase_count: int = 0
    phase_count_match: bool = False

    master_plan_exists: bool = False
    filenames_valid: bool = False
    invalid_filenames: list[str] = field(default_factory=list)

    # Tier 2: Keyword preservation
    source_tech_stack: set[str] = field(default_factory=set)
    converted_tech_stack: set[str] = field(default_factory=set)
    tech_preserved: bool = False
    tech_lost: set[str] = field(default_factory=set)

    source_agents: set[str] = field(default_factory=set)
    converted_agents: set[str] = field(default_factory=set)
    agents_preserved: bool = False
    agents_lost: set[str] = field(default_factory=set)

    source_risks: set[str] = field(default_factory=set)
    converted_risks: set[str] = field(default_factory=set)
    risks_preserved: bool = False
    risks_lost: set[str] = field(default_factory=set)

    source_task_verbs: set[str] = field(default_factory=set)
    converted_task_verbs: set[str] = field(default_factory=set)

    # Tier 3a: Similarity metrics (raw)
    jaccard_similarity: float = 0.0
    weighted_jaccard_similarity: float = 0.0

    # Tier 3a: Similarity metrics (preprocessed - more accurate)
    preprocessed_jaccard: float = 0.0
    preprocessed_weighted_jaccard: float = 0.0

    # Gate validation (from audit)
    gates_valid: bool = False
    gates_count: int = 0

    @property
    def tier1_score(self) -> float:
        """Score from Tier 1 checks (0-1)."""
        checks = [
            self.phase_count_match,
            self.master_plan_exists,
            self.filenames_valid,
            self.gates_valid,
        ]
        return sum(checks) / len(checks) if checks else 0.0

    @property
    def tier2_score(self) -> float:
        """Score from Tier 2 keyword preservation (0-1)."""
        checks = [
            self.tech_preserved,
            self.agents_preserved,
            self.risks_preserved,
        ]
        return sum(checks) / len(checks) if checks else 0.0

    @property
    def tier3a_score(self) -> float:
        """Score from Tier 3a similarity (0-1).

        Uses preprocessed metrics if available, falls back to raw.
        """
        # Prefer preprocessed metrics (more accurate)
        if self.preprocessed_jaccard > 0 or self.preprocessed_weighted_jaccard > 0:
            return (self.preprocessed_jaccard + self.preprocessed_weighted_jaccard) / 2
        # Fall back to raw metrics
        return (self.jaccard_similarity + self.weighted_jaccard_similarity) / 2

    @property
    def quick_score(self) -> float:
        """Quick overall quality score using Tier 1-2 metrics (0-1)."""
        # Use preprocessed similarity if available (threshold 0.3 for preprocessed)
        similarity_ok = (
            self.preprocessed_jaccard > 0.3
            if self.preprocessed_jaccard > 0
            else self.jaccard_similarity > 0.2
        )
        checks = [
            self.phase_count_match,
            self.master_plan_exists,
            self.filenames_valid,
            self.gates_valid,
            self.tech_preserved,
            self.agents_preserved,
            similarity_ok,
        ]
        return sum(checks) / len(checks) if checks else 0.0

    @property
    def full_score(self) -> float:
        """Comprehensive quality score (0-1).

        Weighted combination of all tiers:
        - Tier 1: 40% (structural correctness is critical)
        - Tier 2: 35% (content preservation matters)
        - Tier 3a: 25% (similarity is a softer signal)
        """
        return (
            self.tier1_score * 0.40
            + self.tier2_score * 0.35
            + self.tier3a_score * 0.25
        )

    def summary(self) -> str:
        """Human-readable summary of quality metrics."""
        lines = [
            "Conversion Quality Report",
            "=" * 40,
            "",
            "Tier 1: Structural Checks",
            f"  Phase count: {self.source_phase_count} → {self.converted_phase_count} {'✓' if self.phase_count_match else '✗'}",
            f"  Master plan exists: {'✓' if self.master_plan_exists else '✗'}",
            f"  Filename convention: {'✓' if self.filenames_valid else '✗'}",
            f"  Gates valid: {'✓' if self.gates_valid else '✗'} ({self.gates_count} gates)",
            f"  Tier 1 Score: {self.tier1_score:.0%}",
            "",
            "Tier 2: Content Preservation",
            f"  Tech stack: {len(self.converted_tech_stack)}/{len(self.source_tech_stack)} preserved {'✓' if self.tech_preserved else '✗'}",
        ]

        if self.tech_lost:
            lines.append(f"    Lost: {', '.join(sorted(self.tech_lost))}")

        lines.extend([
            f"  Agents: {len(self.converted_agents)}/{len(self.source_agents)} preserved {'✓' if self.agents_preserved else '✗'}",
        ])

        if self.agents_lost:
            lines.append(f"    Lost: {', '.join(sorted(self.agents_lost))}")

        # Risk preservation: source risks should appear in converted (more is OK)
        risk_status = "✓" if self.risks_preserved else "✗"
        if len(self.source_risks) == 0:
            risk_display = "N/A (none in source)"
        elif self.risks_preserved:
            extra = len(self.converted_risks) - len(self.source_risks)
            risk_display = f"all {len(self.source_risks)} preserved (+{extra} added)" if extra > 0 else f"all {len(self.source_risks)} preserved"
        else:
            risk_display = f"{len(self.source_risks - self.risks_lost)}/{len(self.source_risks)} preserved"

        lines.append(f"  Risk mentions: {risk_display} {risk_status}")

        if self.risks_lost:
            lines.append(f"    Lost: {', '.join(sorted(self.risks_lost))}")

        lines.extend([
            f"  Tier 2 Score: {self.tier2_score:.0%}",
            "",
            "Tier 3a: Text Similarity",
            f"  Raw Jaccard: {self.jaccard_similarity:.2%}",
            f"  Raw Weighted: {self.weighted_jaccard_similarity:.2%}",
            f"  Preprocessed Jaccard: {self.preprocessed_jaccard:.2%}",
            f"  Preprocessed Weighted: {self.preprocessed_weighted_jaccard:.2%}",
            f"  Tier 3a Score: {self.tier3a_score:.0%}",
            "",
            "=" * 40,
            f"Quick Score: {self.quick_score:.0%}",
            f"Full Score:  {self.full_score:.0%}",
        ])

        return "\n".join(lines)


# =============================================================================
# Evaluator Class
# =============================================================================


class ConversionQualityEvaluator:
    """Evaluates the quality of a plan conversion."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        source_content: str | None = None,
        converted_content: str | None = None,
    ):
        """Initialize the evaluator.

        Args:
            source_dir: Directory containing source freeform plan.
            output_dir: Directory containing converted Debussy plan.
            source_content: Optional pre-loaded source content.
            converted_content: Optional pre-loaded converted content.
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self._source_content = source_content
        self._converted_content = converted_content

    def _load_source_content(self) -> str:
        """Load all source markdown files into single string."""
        if self._source_content:
            return self._source_content

        content_parts = []
        for md_file in sorted(self.source_dir.glob("*.md")):
            content_parts.append(md_file.read_text(encoding="utf-8"))

        return "\n\n".join(content_parts)

    def _load_converted_content(self) -> str:
        """Load all converted markdown files into single string."""
        if self._converted_content:
            return self._converted_content

        content_parts = []
        for md_file in sorted(self.output_dir.glob("*.md")):
            content_parts.append(md_file.read_text(encoding="utf-8"))

        return "\n\n".join(content_parts)

    def evaluate(
        self,
        audit_result: Any | None = None,
    ) -> ConversionQuality:
        """Evaluate conversion quality.

        Args:
            audit_result: Optional AuditResult from PlanAuditor for gate info.

        Returns:
            ConversionQuality with all metrics populated.
        """
        source = self._load_source_content()
        converted = self._load_converted_content()

        quality = ConversionQuality()

        # Tier 1: Structural checks
        quality.source_phase_count = max(
            count_phases_in_freeform(source),
            count_phases_in_directory(self.source_dir),
        )

        # Count converted phases from audit or files
        if audit_result and hasattr(audit_result, "summary"):
            quality.converted_phase_count = audit_result.summary.phases_found
            quality.gates_valid = audit_result.summary.errors == 0
            quality.gates_count = audit_result.summary.gates_total
        else:
            quality.converted_phase_count = len(list(self.output_dir.glob("phase-*.md")))

        quality.phase_count_match = quality.source_phase_count == quality.converted_phase_count

        quality.master_plan_exists = check_master_plan_exists(self.output_dir)

        quality.filenames_valid, quality.invalid_filenames = check_filename_convention(
            self.output_dir
        )

        # Tier 2: Keyword preservation
        quality.source_tech_stack = extract_tech_stack(source)
        quality.converted_tech_stack = extract_tech_stack(converted)
        quality.tech_lost = quality.source_tech_stack - quality.converted_tech_stack
        quality.tech_preserved = len(quality.tech_lost) == 0

        quality.source_agents = extract_agent_references(source)
        quality.converted_agents = extract_agent_references(converted)
        quality.agents_lost = quality.source_agents - quality.converted_agents
        quality.agents_preserved = len(quality.agents_lost) == 0

        quality.source_risks = extract_risk_mentions(source)
        quality.converted_risks = extract_risk_mentions(converted)
        quality.risks_lost = quality.source_risks - quality.converted_risks
        # Risk preservation = all source risks appear in converted
        # Having MORE risk terms in converted is fine (template adds standard terms)
        quality.risks_preserved = quality.source_risks <= quality.converted_risks

        quality.source_task_verbs = extract_task_keywords(source)
        quality.converted_task_verbs = extract_task_keywords(converted)

        # Tier 3a: Similarity metrics (raw)
        quality.jaccard_similarity = jaccard_similarity(source, converted)
        quality.weighted_jaccard_similarity = weighted_jaccard_similarity(source, converted)

        # Tier 3a: Similarity metrics (preprocessed - strips markdown & boilerplate)
        quality.preprocessed_jaccard = preprocessed_jaccard_similarity(source, converted)
        quality.preprocessed_weighted_jaccard = preprocessed_weighted_jaccard(source, converted)

        return quality
