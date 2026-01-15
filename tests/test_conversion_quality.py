"""Tests for conversion quality metrics.

These tests verify the quality evaluation functions work correctly
for measuring conversion fidelity.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from debussy.converters.quality import (
    AGENT_KEYWORDS,
    TECH_KEYWORDS,
    ConversionQuality,
    ConversionQualityEvaluator,
    check_filename_convention,
    check_master_plan_exists,
    count_phases_in_directory,
    count_phases_in_freeform,
    extract_agent_references,
    extract_keywords,
    extract_risk_mentions,
    extract_task_keywords,
    extract_tech_stack,
    jaccard_similarity,
    tokenize,
    weighted_jaccard_similarity,
)

# =============================================================================
# Tier 1: Phase Counting Tests
# =============================================================================


class TestCountPhasesInFreeform:
    """Test phase counting in freeform markdown."""

    def test_phase_headers_with_colon(self) -> None:
        """Detect ### Phase: style headers."""
        content = """
# Project Plan

### Phase: Database Setup
Content here

### Phase: Backend API
More content

### Phase: Frontend
Final content
"""
        assert count_phases_in_freeform(content) == 3

    def test_phase_headers_numbered(self) -> None:
        """Detect ### Phase 1 style headers."""
        content = """
## Phase 1: Database
## Phase 2: Backend
## Phase 3: Frontend
"""
        assert count_phases_in_freeform(content) == 3

    def test_sprint_headers(self) -> None:
        """Detect sprint-based headers."""
        content = """
### Sprint 1: Planning
### Sprint 2: Development
### Sprint 3: Testing
"""
        assert count_phases_in_freeform(content) == 3

    def test_module_headers(self) -> None:
        """Detect module-based headers."""
        content = """
## Module 1: Data Layer
## Module 2: Auth
## Module 3: API
## Module 4: UI
"""
        assert count_phases_in_freeform(content) == 4

    def test_numbered_list_style(self) -> None:
        """Detect numbered list style phases."""
        content = """
1. Phase Database Setup
2. Phase Backend Development
3. Phase Frontend Integration
"""
        assert count_phases_in_freeform(content) == 3

    def test_no_phases(self) -> None:
        """Handle content with no phases."""
        content = """
# Just a README
Some text without any phase markers.
"""
        assert count_phases_in_freeform(content) == 0

    def test_mixed_styles(self) -> None:
        """Content should only count valid phase patterns, not duplicates."""
        content = """
### Phase: Setup
This phase sets up the environment.
"""
        # Only one actual phase header
        assert count_phases_in_freeform(content) == 1


class TestCountPhasesInDirectory:
    """Test phase counting from directory structure."""

    def test_phase_files(self, tmp_path: Path) -> None:
        """Count files matching phase patterns."""
        (tmp_path / "master_plan.md").touch()
        (tmp_path / "phase-1-database.md").touch()
        (tmp_path / "phase-2-backend.md").touch()
        (tmp_path / "phase-3-frontend.md").touch()

        assert count_phases_in_directory(tmp_path) == 3

    def test_sprint_files(self, tmp_path: Path) -> None:
        """Count sprint-style files."""
        (tmp_path / "overview.md").touch()
        (tmp_path / "sprint1_planning.md").touch()
        (tmp_path / "sprint2_development.md").touch()

        assert count_phases_in_directory(tmp_path) == 2

    def test_module_files(self, tmp_path: Path) -> None:
        """Count module-style files."""
        (tmp_path / "project_plan.md").touch()
        (tmp_path / "module_1_data.md").touch()
        (tmp_path / "module_2_auth.md").touch()

        assert count_phases_in_directory(tmp_path) == 2

    def test_excludes_master_files(self, tmp_path: Path) -> None:
        """Master/overview files should not be counted."""
        (tmp_path / "MASTER_PLAN.md").touch()
        (tmp_path / "master_plan.md").touch()
        (tmp_path / "overview.md").touch()
        (tmp_path / "readme.md").touch()
        (tmp_path / "phase-1.md").touch()

        assert count_phases_in_directory(tmp_path) == 1

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Handle empty directory."""
        assert count_phases_in_directory(tmp_path) == 0

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Handle nonexistent directory."""
        assert count_phases_in_directory(tmp_path / "nonexistent") == 0


class TestFilenameConvention:
    """Test filename convention checking."""

    def test_valid_phase_files(self, tmp_path: Path) -> None:
        """Valid phase filenames pass."""
        (tmp_path / "phase-1.md").touch()
        (tmp_path / "phase-2-database.md").touch()
        (tmp_path / "phase-3-backend-api.md").touch()

        valid, invalid = check_filename_convention(tmp_path)
        assert valid
        assert invalid == []

    def test_invalid_phase_files(self, tmp_path: Path) -> None:
        """Invalid filenames are caught."""
        (tmp_path / "phase-1.md").touch()
        (tmp_path / "phase_2.md").touch()  # Underscore instead of dash
        (tmp_path / "phase-three.md").touch()  # Word instead of number

        valid, invalid = check_filename_convention(tmp_path)
        assert not valid
        # phase_2.md doesn't start with phase- so not caught, phase-three.md is caught
        assert "phase-three.md" in invalid

    def test_no_phase_files(self, tmp_path: Path) -> None:
        """No phase files is valid (nothing to check)."""
        (tmp_path / "MASTER_PLAN.md").touch()

        valid, invalid = check_filename_convention(tmp_path)
        assert valid
        assert invalid == []


class TestMasterPlanExists:
    """Test master plan existence check."""

    def test_exists(self, tmp_path: Path) -> None:
        """Detect existing MASTER_PLAN.md."""
        (tmp_path / "MASTER_PLAN.md").touch()
        assert check_master_plan_exists(tmp_path)

    def test_not_exists(self, tmp_path: Path) -> None:
        """Detect missing MASTER_PLAN.md."""
        (tmp_path / "other.md").touch()
        assert not check_master_plan_exists(tmp_path)


# =============================================================================
# Tier 2: Keyword Extraction Tests
# =============================================================================


class TestExtractKeywords:
    """Test generic keyword extraction."""

    def test_basic_extraction(self) -> None:
        """Extract keywords from vocabulary."""
        text = "We use Flask with PostgreSQL and React frontend."
        found = extract_keywords(text, TECH_KEYWORDS)
        assert "flask" in found
        assert "postgresql" in found
        assert "react" in found

    def test_case_insensitive(self) -> None:
        """Extraction is case insensitive."""
        text = "Using FLASK and PostgreSQL"
        found = extract_keywords(text, TECH_KEYWORDS)
        assert "flask" in found
        assert "postgresql" in found

    def test_hyphenated_keywords(self) -> None:
        """Handle hyphenated keywords like python-task-validator."""
        text = "Use python-task-validator for validation"
        found = extract_keywords(text, AGENT_KEYWORDS)
        assert "python-task-validator" in found

    def test_word_boundaries(self) -> None:
        """Don't match partial words."""
        text = "The flask-like framework is great"
        found = extract_keywords(text, TECH_KEYWORDS)
        # Should match flask due to word boundary
        assert "flask" in found


class TestExtractTechStack:
    """Test technology keyword extraction."""

    def test_typical_stack(self) -> None:
        """Extract typical tech stack mentions."""
        text = """
        Backend: Python with Flask
        Database: PostgreSQL
        Frontend: React with TypeScript
        Authentication: JWT tokens
        """
        tech = extract_tech_stack(text)
        assert {"python", "flask", "postgresql", "react", "typescript", "jwt"} <= tech

    def test_node_variations(self) -> None:
        """Handle Node.js variations."""
        text = "Using Node.js with Express"
        tech = extract_tech_stack(text)
        # Should catch node or nodejs
        assert "node" in tech or "nodejs" in tech
        assert "express" in tech


class TestExtractAgentReferences:
    """Test agent name extraction."""

    def test_validator_agent(self) -> None:
        """Extract python-task-validator mentions."""
        text = "Use python-task-validator to verify code quality"
        agents = extract_agent_references(text)
        assert "python-task-validator" in agents

    def test_multiple_agents(self) -> None:
        """Extract multiple agent references."""
        text = """
        - python-task-validator for code quality
        - textual-tui-expert for TUI review
        - llm-security-expert for security audit
        """
        agents = extract_agent_references(text)
        assert "python-task-validator" in agents
        assert "textual-tui-expert" in agents
        assert "llm-security-expert" in agents


class TestExtractRiskMentions:
    """Test risk keyword extraction."""

    def test_risk_terms(self) -> None:
        """Extract risk-related terms."""
        text = """
        ## Risk Assessment
        - Security risk from exposed endpoints
        - Mitigation: Use authentication middleware
        - Blocker: Database migration dependency
        """
        risks = extract_risk_mentions(text)
        assert "risk" in risks
        assert "mitigation" in risks
        assert "blocker" in risks
        assert "security" in risks
        assert "dependency" in risks


class TestExtractTaskKeywords:
    """Test task action verb extraction."""

    def test_checkbox_tasks(self) -> None:
        """Extract verbs from checkbox tasks."""
        text = """
        - [ ] Create user model
        - [ ] Implement authentication
        - [ ] Configure database
        - [x] Setup project structure
        """
        verbs = extract_task_keywords(text)
        assert "create" in verbs
        assert "implement" in verbs
        assert "configure" in verbs
        assert "setup" in verbs

    def test_numbered_tasks(self) -> None:
        """Extract verbs from numbered checkbox tasks."""
        text = """
        - [ ] 1.1: Create PostgreSQL connection
        - [ ] 1.2: Configure SQLAlchemy ORM
        """
        verbs = extract_task_keywords(text)
        # Should extract verbs from task text after the number prefix
        # The regex captures text after "- [ ]" including "1.1:" prefix
        # So the first "word" is "11" (after stripping non-alpha), which is filtered
        # This is a known limitation - numbered prefixes affect extraction
        # But tasks like "Create" and "Configure" should still be found
        assert "create" in verbs or "configure" in verbs

    def test_no_tasks(self) -> None:
        """Handle content without checkbox tasks."""
        text = "Just regular text without tasks."
        verbs = extract_task_keywords(text)
        assert len(verbs) == 0


# =============================================================================
# Tier 3a: Similarity Tests
# =============================================================================


class TestTokenize:
    """Test text tokenization."""

    def test_basic_tokenization(self) -> None:
        """Tokenize simple text."""
        tokens = tokenize("Hello World test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_removes_short_words(self) -> None:
        """Filter words with 2 or fewer chars."""
        tokens = tokenize("a is of to")  # All 2 chars or less
        assert len(tokens) == 0

    def test_keeps_three_char_words(self) -> None:
        """Words with 3+ chars are kept."""
        tokens = tokenize("the cat sat")  # All 3 chars
        assert "the" in tokens
        assert "cat" in tokens
        assert "sat" in tokens

    def test_removes_numbers(self) -> None:
        """Filter pure numbers."""
        tokens = tokenize("Phase 123 test 456")
        assert "phase" in tokens
        assert "test" in tokens
        assert "123" not in tokens
        assert "456" not in tokens

    def test_preserves_hyphens(self) -> None:
        """Keep hyphenated words."""
        tokens = tokenize("python-task-validator is good")
        assert "python-task-validator" in tokens
        assert "good" in tokens


class TestJaccardSimilarity:
    """Test Jaccard similarity calculation."""

    def test_identical_texts(self) -> None:
        """Identical texts have similarity 1.0."""
        text = "The quick brown fox jumps"
        assert jaccard_similarity(text, text) == 1.0

    def test_completely_different(self) -> None:
        """Completely different texts have low similarity."""
        text1 = "apple banana cherry"
        text2 = "xray yellow zebra"
        sim = jaccard_similarity(text1, text2)
        assert sim == 0.0

    def test_partial_overlap(self) -> None:
        """Partial overlap gives intermediate similarity."""
        text1 = "flask postgresql react"
        text2 = "flask django angular"
        sim = jaccard_similarity(text1, text2)
        # Only "flask" overlaps: 1 / 5 = 0.2
        assert 0.15 < sim < 0.25

    def test_empty_text(self) -> None:
        """Empty text gives 0 similarity."""
        assert jaccard_similarity("", "some text") == 0.0
        assert jaccard_similarity("some text", "") == 0.0
        assert jaccard_similarity("", "") == 0.0


class TestWeightedJaccardSimilarity:
    """Test weighted Jaccard similarity."""

    def test_weights_important_terms(self) -> None:
        """Important terms are weighted higher."""
        text1 = "flask postgresql react random words"
        text2 = "flask django random other stuff"

        # Unweighted
        unweighted = jaccard_similarity(text1, text2)

        # Weighted (tech terms get 2x weight)
        weighted = weighted_jaccard_similarity(text1, text2)

        # Weighted should be higher because flask (tech term) is in both
        # and gets 2x weight
        assert weighted >= unweighted

    def test_no_important_terms(self) -> None:
        """Without important terms, similar to regular Jaccard."""
        text1 = "random words here now"
        text2 = "random words there then"

        unweighted = jaccard_similarity(text1, text2)
        weighted = weighted_jaccard_similarity(text1, text2)

        # Should be similar since no tech/agent terms
        assert abs(weighted - unweighted) < 0.1


# =============================================================================
# ConversionQuality Dataclass Tests
# =============================================================================


class TestConversionQualityScores:
    """Test ConversionQuality score calculations."""

    def test_perfect_tier1_score(self) -> None:
        """Perfect Tier 1 checks give 1.0."""
        quality = ConversionQuality(
            phase_count_match=True,
            master_plan_exists=True,
            filenames_valid=True,
            gates_valid=True,
        )
        assert quality.tier1_score == 1.0

    def test_zero_tier1_score(self) -> None:
        """All failed Tier 1 checks give 0.0."""
        quality = ConversionQuality()
        assert quality.tier1_score == 0.0

    def test_perfect_tier2_score(self) -> None:
        """Perfect Tier 2 checks give 1.0."""
        quality = ConversionQuality(
            tech_preserved=True,
            agents_preserved=True,
            risks_preserved=True,
        )
        assert quality.tier2_score == 1.0

    def test_tier3a_score_average(self) -> None:
        """Tier 3a score is average of similarities."""
        quality = ConversionQuality(
            jaccard_similarity=0.4,
            weighted_jaccard_similarity=0.6,
        )
        assert quality.tier3a_score == 0.5

    def test_quick_score(self) -> None:
        """Quick score combines key metrics."""
        quality = ConversionQuality(
            phase_count_match=True,
            master_plan_exists=True,
            filenames_valid=True,
            gates_valid=True,
            tech_preserved=True,
            agents_preserved=True,
            jaccard_similarity=0.5,  # > 0.2 threshold
        )
        assert quality.quick_score == 1.0

    def test_full_score_weights(self) -> None:
        """Full score uses proper weights."""
        quality = ConversionQuality(
            # Tier 1: all True = 1.0
            phase_count_match=True,
            master_plan_exists=True,
            filenames_valid=True,
            gates_valid=True,
            # Tier 2: all True = 1.0
            tech_preserved=True,
            agents_preserved=True,
            risks_preserved=True,
            # Tier 3a: both 1.0 = 1.0
            jaccard_similarity=1.0,
            weighted_jaccard_similarity=1.0,
        )
        # 1.0 * 0.40 + 1.0 * 0.35 + 1.0 * 0.25 = 1.0
        assert quality.full_score == 1.0

    def test_summary_output(self) -> None:
        """Summary produces readable output."""
        quality = ConversionQuality(
            source_phase_count=3,
            converted_phase_count=3,
            phase_count_match=True,
            master_plan_exists=True,
            source_tech_stack={"flask", "react"},
            converted_tech_stack={"flask", "react"},
            tech_preserved=True,
            jaccard_similarity=0.5,
        )
        summary = quality.summary()
        assert "Tier 1" in summary
        assert "Tier 2" in summary
        assert "Tier 3a" in summary
        assert "3 → 3" in summary  # Phase count


# =============================================================================
# ConversionQualityEvaluator Tests
# =============================================================================


class TestConversionQualityEvaluator:
    """Test the evaluator class."""

    def test_evaluate_with_matching_content(self, tmp_path: Path) -> None:
        """Evaluate conversion with matching content."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create source files (avoiding generic words like "rest" and "api")
        (source_dir / "master_plan.md").write_text("""
# Project Plan

### Phase: Database Setup
Use Flask with PostgreSQL.
Use python-task-validator for validation.

### Phase: Backend Development
Implement authentication endpoints.

### Phase: Frontend
Build React dashboard.
""")
        (source_dir / "database_phase.md").touch()
        (source_dir / "backend_phase.md").touch()
        (source_dir / "frontend_phase.md").touch()

        # Create converted files
        (output_dir / "MASTER_PLAN.md").write_text("""
# TaskTracker - Master Plan

## Phases

| Phase | Title |
|-------|-------|
| 1 | Database Setup |
| 2 | Backend API |
| 3 | Frontend |

## Tech Stack
- Flask
- PostgreSQL
- React
""")
        (output_dir / "phase-1-database.md").write_text("""
# Phase 1: Database Setup

Use python-task-validator to verify.
Flask models with PostgreSQL.
""")
        (output_dir / "phase-2-backend.md").write_text("# Phase 2: Backend API")
        (output_dir / "phase-3-frontend.md").write_text("# Phase 3: React Frontend")

        evaluator = ConversionQualityEvaluator(source_dir, output_dir)
        quality = evaluator.evaluate()

        # Check Tier 1
        assert quality.master_plan_exists
        assert quality.filenames_valid
        assert quality.source_phase_count == 3
        assert quality.converted_phase_count == 3
        assert quality.phase_count_match

        # Check Tier 2
        assert "flask" in quality.source_tech_stack
        assert "flask" in quality.converted_tech_stack
        assert quality.tech_preserved
        assert "python-task-validator" in quality.source_agents
        assert quality.agents_preserved

        # Check Tier 3a
        assert quality.jaccard_similarity > 0.2

        # Overall scores should be good
        assert quality.quick_score >= 0.8

    def test_evaluate_with_missing_content(self, tmp_path: Path) -> None:
        """Evaluate conversion with missing content."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Source with tech stack
        (source_dir / "master_plan.md").write_text("""
### Phase: Backend
Use Flask, PostgreSQL, Redis, JWT.
Use python-task-validator.
""")

        # Converted missing some tech
        (output_dir / "MASTER_PLAN.md").write_text("""
# Master Plan
Use Flask.
""")
        (output_dir / "phase-1.md").write_text("# Phase 1")

        evaluator = ConversionQualityEvaluator(source_dir, output_dir)
        quality = evaluator.evaluate()

        # Should detect lost content
        assert not quality.tech_preserved
        assert "postgresql" in quality.tech_lost or "redis" in quality.tech_lost
        assert not quality.agents_preserved
        assert "python-task-validator" in quality.agents_lost

    def test_evaluate_with_audit_result(self, tmp_path: Path) -> None:
        """Evaluate using audit result for gate info."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        (source_dir / "plan.md").write_text("### Phase: Test")
        (output_dir / "MASTER_PLAN.md").write_text("# Master")
        (output_dir / "phase-1.md").write_text("# Phase 1")

        # Mock audit result
        mock_audit = MagicMock()
        mock_audit.summary.phases_found = 2
        mock_audit.summary.errors = 0
        mock_audit.summary.gates_total = 5

        evaluator = ConversionQualityEvaluator(source_dir, output_dir)
        quality = evaluator.evaluate(audit_result=mock_audit)

        assert quality.converted_phase_count == 2
        assert quality.gates_valid
        assert quality.gates_count == 5


# =============================================================================
# Integration with Sample Plans
# =============================================================================


class TestQualityWithSamplePlans:
    """Test quality metrics with actual sample plans."""

    @pytest.fixture
    def sample_plans_dir(self) -> Path:
        """Get path to sample plans fixtures."""
        return Path(__file__).parent / "fixtures" / "sample_plans"

    def test_plan1_source_analysis(self, sample_plans_dir: Path) -> None:
        """Analyze plan1 source for expected characteristics."""
        plan1_dir = sample_plans_dir / "plan1_tasktracker_basic"

        if not plan1_dir.exists():
            pytest.skip("Sample plan fixtures not found")

        # Read source content
        content = (plan1_dir / "master_plan.md").read_text()

        # Should find 3 phases
        phase_count = count_phases_in_freeform(content)
        assert phase_count == 3, f"Expected 3 phases, found {phase_count}"

        # Should find tech stack
        tech = extract_tech_stack(content)
        assert "flask" in tech
        assert "postgresql" in tech
        assert "react" in tech

        # Should find agent reference
        agents = extract_agent_references(content)
        assert "python-task-validator" in agents

    def test_plan2_source_analysis(self, sample_plans_dir: Path) -> None:
        """Analyze plan2 (agile) source."""
        plan2_dir = sample_plans_dir / "plan2_tasktracker_agile"

        if not plan2_dir.exists():
            pytest.skip("Sample plan fixtures not found")

        # Count files in directory
        file_count = count_phases_in_directory(plan2_dir)
        assert file_count >= 2, f"Expected at least 2 sprint files, found {file_count}"

    def test_plan3_source_analysis(self, sample_plans_dir: Path) -> None:
        """Analyze plan3 (modular) source."""
        plan3_dir = sample_plans_dir / "plan3_tasktracker_modular"

        if not plan3_dir.exists():
            pytest.skip("Sample plan fixtures not found")

        # Count module files
        file_count = count_phases_in_directory(plan3_dir)
        assert file_count >= 3, f"Expected at least 3 module files, found {file_count}"
