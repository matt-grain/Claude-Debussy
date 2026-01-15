"""Tests for convert feature using sample freeform plans.

These tests verify the complete convert workflow:
1. Audit fails on freeform plans (pre-conversion)
2. Converter processes the plans
3. Audit passes on converted plans (post-conversion)

See docs/CONVERT_TESTS.md for test strategy documentation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from debussy.converters import PlanConverter
from debussy.converters.plan_converter import PlanConverter as PlanConverterClass
from debussy.converters.quality import (
    ConversionQualityEvaluator,
    count_phases_in_freeform,
    extract_agent_references,
    extract_tech_stack,
)
from debussy.core.auditor import PlanAuditor
from debussy.templates import TEMPLATES_DIR

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_plans_dir() -> Path:
    """Get path to sample plans fixtures."""
    return Path(__file__).parent / "fixtures" / "sample_plans"


@pytest.fixture
def plan1_basic(sample_plans_dir: Path) -> Path:
    """Plan 1: Traditional phase-based structure."""
    return sample_plans_dir / "plan1_tasktracker_basic"


@pytest.fixture
def plan2_agile(sample_plans_dir: Path) -> Path:
    """Plan 2: Sprint-based agile structure."""
    return sample_plans_dir / "plan2_tasktracker_agile"


@pytest.fixture
def plan3_modular(sample_plans_dir: Path) -> Path:
    """Plan 3: Module-based structure."""
    return sample_plans_dir / "plan3_tasktracker_modular"


@pytest.fixture
def auditor() -> PlanAuditor:
    """Create a real PlanAuditor instance."""
    return PlanAuditor()


# =============================================================================
# Pre-Conversion Audit Tests (Should FAIL)
# =============================================================================


class TestPreConversionAudit:
    """Verify that freeform plans fail audit before conversion."""

    def test_plan1_basic_audit_fails(self, auditor: PlanAuditor, plan1_basic: Path) -> None:
        """Plan 1 (phase-based) should fail audit - doesn't match template."""
        master_plan = plan1_basic / "master_plan.md"
        result = auditor.audit(master_plan)

        assert not result.passed, "Freeform plan should fail audit"
        assert result.summary.errors > 0, "Should have audit errors"
        # Expect parse error or no phases error
        error_codes = [issue.code for issue in result.issues]
        assert any(code in error_codes for code in ["MASTER_PARSE_ERROR", "NO_PHASES"]), f"Expected parse/phases error, got: {error_codes}"

    def test_plan2_agile_audit_fails(self, auditor: PlanAuditor, plan2_agile: Path) -> None:
        """Plan 2 (sprint-based) should fail audit - doesn't match template."""
        master_plan = plan2_agile / "plan_overview.md"
        result = auditor.audit(master_plan)

        assert not result.passed, "Freeform plan should fail audit"
        assert result.summary.errors > 0, "Should have audit errors"

    def test_plan3_modular_audit_fails(self, auditor: PlanAuditor, plan3_modular: Path) -> None:
        """Plan 3 (module-based) should fail audit - doesn't match template."""
        master_plan = plan3_modular / "project_plan.md"
        result = auditor.audit(master_plan)

        assert not result.passed, "Freeform plan should fail audit"
        assert result.summary.errors > 0, "Should have audit errors"

    def test_compliance_score_zero_for_freeform(self, auditor: PlanAuditor, plan1_basic: Path) -> None:
        """Freeform plans should have zero compliance (no valid phases)."""
        master_plan = plan1_basic / "master_plan.md"
        result = auditor.audit(master_plan)

        # Compliance score = phases_valid / phases_found
        # For freeform plans, phases_found should be 0 (no table parsed)
        # or phases_valid should be 0 (none match template)
        phases_found = result.summary.phases_found
        phases_valid = result.summary.phases_valid

        if phases_found > 0:
            compliance = phases_valid / phases_found
            assert compliance < 1.0, f"Expected low compliance, got {compliance}"
        else:
            # No phases found at all - that's also a failure
            assert phases_found == 0, "Freeform plan shouldn't have parseable phases"


# =============================================================================
# Conversion Tests
# =============================================================================


class TestSamplePlanConversion:
    """Test conversion of sample freeform plans."""

    def _mock_claude_output_for_plan1(self) -> str:
        """Generate mock Claude output for plan1 conversion."""
        return """
---FILE: MASTER_PLAN.md---
# TaskTracker Application - Master Plan

**Created:** 2024-01-15
**Status:** Draft

---

## Overview

TaskTracker is a web-based task management application with user authentication, RESTful API, and React frontend.

## Goals

1. **User Management** - Secure user registration and authentication
2. **Task Management** - Full CRUD operations for tasks
3. **Modern UI** - Responsive React-based dashboard

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Database Setup](phase-1-database.md) | Database schema and models | Low | Pending |
| 2 | [Backend API](phase-2-backend.md) | REST API development | Medium | Pending |
| 3 | [Frontend](phase-3-frontend.md) | React dashboard | Medium | Pending |

## Success Metrics

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| Test Coverage | 0% | 80% | 85% | 90% |
| API Endpoints | 0 | 2 | 10 | 10 |

## Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema changes | Low | Medium | Migration scripts |
| API performance | Medium | Medium | Caching layer |

## Out of Scope

- Mobile native apps
- Real-time WebSocket features

## Review Checkpoints

- After Phase 1: Database migrations work
- After Phase 2: All API tests pass
- After Phase 3: UI renders correctly
---END FILE---

---FILE: phase-1-database.md---
# TaskTracker Phase 1: Database Setup

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: N/A (first phase)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/
  uv run pytest tests/ -v
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_1.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: 0 errors (command: `uv run ruff check .`)
- type-check: 0 errors (command: `uv run pyright src/`)
- tests: All tests pass (command: `uv run pytest tests/`)

---

## Overview

Set up PostgreSQL database with SQLAlchemy models for users and tasks.

## Tasks

### 1. Database Configuration
- [ ] 1.1: Set up PostgreSQL connection
- [ ] 1.2: Configure SQLAlchemy ORM

### 2. Model Implementation
- [ ] 2.1: Create User model with password hashing
- [ ] 2.2: Create Task model with relationships
- [ ] 2.3: Create migration scripts

## Validation

- Use `python-task-validator` to verify model code quality

## Acceptance Criteria

- [ ] All models defined with appropriate fields
- [ ] Relationships correctly established
- [ ] Migration scripts run without errors
---END FILE---

---FILE: phase-2-backend.md---
# TaskTracker Phase 2: Backend API

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** [Phase 1](phase-1-database.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_1.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/
  uv run pytest tests/ -v
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_2.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: 0 errors (command: `uv run ruff check .`)
- type-check: 0 errors (command: `uv run pyright src/`)
- tests: All tests pass (command: `uv run pytest tests/`)
- security: No high severity issues (command: `uv run bandit -r src/`)

---

## Overview

Develop Flask REST API with authentication and CRUD endpoints.

## Tasks

### 1. Authentication
- [ ] 1.1: Implement user registration endpoint
- [ ] 1.2: Implement login with JWT tokens
- [ ] 1.3: Create auth middleware

### 2. Task Endpoints
- [ ] 2.1: Create task endpoint
- [ ] 2.2: Read task(s) endpoint
- [ ] 2.3: Update task endpoint
- [ ] 2.4: Delete task endpoint

## Validation

- Use `python-task-validator` to verify API implementation

## Acceptance Criteria

- [ ] All endpoints return appropriate status codes
- [ ] Authentication blocks unauthorized access
- [ ] Input validation catches malformed requests
---END FILE---

---FILE: phase-3-frontend.md---
# TaskTracker Phase 3: Frontend Dashboard

**Status:** Pending
**Master Plan:** [MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** [Phase 2](phase-2-backend.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_2.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  npm run lint --fix
  npm run type-check
  npm test
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_3.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: 0 errors (command: `npm run lint`)
- type-check: 0 errors (command: `npm run type-check`)
- tests: All tests pass (command: `npm test`)

---

## Overview

Build React frontend with authentication and task management UI.

## Tasks

### 1. Authentication UI
- [ ] 1.1: Login form component
- [ ] 1.2: Registration form component
- [ ] 1.3: Auth state management

### 2. Dashboard
- [ ] 2.1: Task list component
- [ ] 2.2: Task creation form
- [ ] 2.3: Task editing modal
- [ ] 2.4: Filtering and sorting

## Acceptance Criteria

- [ ] UI responsive on mobile and desktop
- [ ] All API calls handle errors gracefully
- [ ] Auth state persists across sessions
---END FILE---
"""

    @patch.object(PlanConverterClass, "_run_claude")
    def test_convert_plan1_basic(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Convert plan1 (phase-based) and verify it passes audit."""
        mock_run_claude.return_value = self._mock_claude_output_for_plan1()

        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=3,
            model="haiku",
        )

        output_dir = tmp_path / "converted_plan1"
        result = converter.convert(
            source_plan=plan1_basic / "master_plan.md",
            output_dir=output_dir,
        )

        # Conversion should succeed
        assert result.success, f"Conversion failed: {result.warnings}"
        assert result.iterations <= 3, "Should not exhaust retries"
        assert len(result.files_created) >= 2, "Should create master + phase files"

        # Verify files exist
        assert (output_dir / "MASTER_PLAN.md").exists()

    @patch.object(PlanConverterClass, "_run_claude")
    def test_converted_plan1_passes_audit(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Verify converted plan1 passes audit."""
        mock_run_claude.return_value = self._mock_claude_output_for_plan1()

        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
        )

        output_dir = tmp_path / "converted_plan1"
        converter.convert(
            source_plan=plan1_basic / "master_plan.md",
            output_dir=output_dir,
        )

        # Run audit on converted plan
        audit_result = auditor.audit(output_dir / "MASTER_PLAN.md")

        assert audit_result.passed, f"Converted plan should pass audit: {[i.message for i in audit_result.issues]}"
        assert audit_result.summary.errors == 0
        assert audit_result.summary.phases_found == 3
        assert audit_result.summary.phases_valid == 3


# =============================================================================
# Compliance Comparison Tests
# =============================================================================


class TestComplianceImprovement:
    """Test that conversion improves compliance scores."""

    @patch.object(PlanConverterClass, "_run_claude")
    def test_compliance_before_and_after(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Compliance should improve from 0 to 1 after conversion."""
        # Pre-conversion audit
        pre_result = auditor.audit(plan1_basic / "master_plan.md")

        # Calculate pre-compliance (should be 0 or very low)
        pre_phases_valid = pre_result.summary.phases_valid
        pre_phases_found = pre_result.summary.phases_found
        pre_compliance = pre_phases_valid / pre_phases_found if pre_phases_found > 0 else 0.0

        # Run conversion with mock
        mock_run_claude.return_value = TestSamplePlanConversion()._mock_claude_output_for_plan1()

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        # Post-conversion audit
        post_result = auditor.audit(output_dir / "MASTER_PLAN.md")

        # Calculate post-compliance (should be 1.0)
        post_phases_valid = post_result.summary.phases_valid
        post_phases_found = post_result.summary.phases_found
        post_compliance = post_phases_valid / post_phases_found if post_phases_found > 0 else 0.0

        # Verify improvement
        assert post_compliance > pre_compliance, f"Compliance should improve: {pre_compliance:.2f} -> {post_compliance:.2f}"
        assert post_compliance == 1.0, f"Post-conversion compliance should be 1.0, got {post_compliance:.2f}"


# =============================================================================
# Content Preservation Tests
# =============================================================================


class TestContentPreservation:
    """Test that conversion preserves key content from source."""

    @patch.object(PlanConverterClass, "_run_claude")
    def test_phase_count_preserved(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Converted plan should have same number of phases as source intent."""
        # Source plan1 has 3 phases: Database, Backend API, Frontend
        expected_phases = 3

        mock_run_claude.return_value = TestSamplePlanConversion()._mock_claude_output_for_plan1()

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        # Check converted plan has same phase count
        result = auditor.audit(output_dir / "MASTER_PLAN.md")
        assert result.summary.phases_found == expected_phases, f"Expected {expected_phases} phases, got {result.summary.phases_found}"

    @patch.object(PlanConverterClass, "_run_claude")
    def test_validator_agent_preserved(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Converted plan should mention python-task-validator if source did."""
        mock_output = TestSamplePlanConversion()._mock_claude_output_for_plan1()
        mock_run_claude.return_value = mock_output

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        # Check that python-task-validator is mentioned in at least one phase file
        phase_files = list(output_dir.glob("phase-*.md"))
        validator_mentioned = False

        for phase_file in phase_files:
            content = phase_file.read_text()
            if "python-task-validator" in content.lower():
                validator_mentioned = True
                break

        assert validator_mentioned, "Converted plan should preserve python-task-validator reference"


# =============================================================================
# Comprehensive Quality Evaluation Tests
# =============================================================================


class TestConversionQualityEvaluation:
    """Test comprehensive quality evaluation using ConversionQualityEvaluator."""

    @patch.object(PlanConverterClass, "_run_claude")
    def test_full_quality_evaluation(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Run full quality evaluation on converted plan."""
        mock_run_claude.return_value = TestSamplePlanConversion()._mock_claude_output_for_plan1()

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        # Get audit result for gate info
        audit_result = auditor.audit(output_dir / "MASTER_PLAN.md")

        # Run quality evaluation
        evaluator = ConversionQualityEvaluator(
            source_dir=plan1_basic,
            output_dir=output_dir,
        )
        quality = evaluator.evaluate(audit_result=audit_result)

        # Tier 1: Structural checks
        assert quality.master_plan_exists, "MASTER_PLAN.md should exist"
        assert quality.filenames_valid, f"Filenames should be valid: {quality.invalid_filenames}"
        assert quality.phase_count_match, (
            f"Phase count should match: source={quality.source_phase_count}, "
            f"converted={quality.converted_phase_count}"
        )
        assert quality.gates_valid, "Gates should be valid (audit passes)"

        # Tier 2: Content preservation
        assert quality.agents_preserved, (
            f"Agent references should be preserved. Lost: {quality.agents_lost}"
        )
        # Tech stack may not fully match due to template rewriting, but core should be there
        core_tech = {"flask", "postgresql", "react"}
        assert core_tech <= quality.converted_tech_stack, (
            f"Core tech should be preserved. Found: {quality.converted_tech_stack}"
        )

        # Tier 3a: Similarity (threshold of 0.15 accounts for template rewriting)
        assert quality.jaccard_similarity > 0.15, (
            f"Jaccard similarity should be > 0.15, got {quality.jaccard_similarity:.2%}"
        )

        # Overall scores
        assert quality.tier1_score >= 0.75, f"Tier 1 score too low: {quality.tier1_score:.0%}"
        assert quality.quick_score >= 0.6, f"Quick score too low: {quality.quick_score:.0%}"

    @patch.object(PlanConverterClass, "_run_claude")
    def test_quality_summary_output(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Quality summary should produce readable report."""
        mock_run_claude.return_value = TestSamplePlanConversion()._mock_claude_output_for_plan1()

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        audit_result = auditor.audit(output_dir / "MASTER_PLAN.md")
        evaluator = ConversionQualityEvaluator(plan1_basic, output_dir)
        quality = evaluator.evaluate(audit_result=audit_result)

        summary = quality.summary()

        # Summary should contain key sections
        assert "Tier 1" in summary
        assert "Tier 2" in summary
        assert "Tier 3a" in summary
        assert "Quick Score" in summary
        assert "Full Score" in summary

    def test_source_plan_analysis(self, plan1_basic: Path) -> None:
        """Verify source plan has expected characteristics."""
        source_content = (plan1_basic / "master_plan.md").read_text()

        # Should detect 3 phases
        phase_count = count_phases_in_freeform(source_content)
        assert phase_count == 3, f"Expected 3 phases, found {phase_count}"

        # Should find expected tech stack
        tech = extract_tech_stack(source_content)
        assert "flask" in tech, f"Flask not found in: {tech}"
        assert "postgresql" in tech, f"PostgreSQL not found in: {tech}"
        assert "react" in tech, f"React not found in: {tech}"

        # Should find agent reference
        agents = extract_agent_references(source_content)
        assert "python-task-validator" in agents, f"Validator not found in: {agents}"

    @patch.object(PlanConverterClass, "_run_claude")
    def test_quality_score_thresholds(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Quality scores should meet minimum thresholds for good conversion."""
        mock_run_claude.return_value = TestSamplePlanConversion()._mock_claude_output_for_plan1()

        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)
        output_dir = tmp_path / "converted"
        converter.convert(source_plan=plan1_basic / "master_plan.md", output_dir=output_dir)

        audit_result = auditor.audit(output_dir / "MASTER_PLAN.md")
        evaluator = ConversionQualityEvaluator(plan1_basic, output_dir)
        quality = evaluator.evaluate(audit_result=audit_result)

        # Define minimum acceptable thresholds
        MIN_TIER1_SCORE = 0.75  # Structural correctness is critical
        MIN_TIER2_SCORE = 0.33  # At least 1/3 of content preserved
        MIN_QUICK_SCORE = 0.50  # Overall minimum
        MIN_JACCARD = 0.15  # Basic word overlap

        assert quality.tier1_score >= MIN_TIER1_SCORE, (
            f"Tier 1 below threshold: {quality.tier1_score:.0%} < {MIN_TIER1_SCORE:.0%}"
        )
        assert quality.tier2_score >= MIN_TIER2_SCORE, (
            f"Tier 2 below threshold: {quality.tier2_score:.0%} < {MIN_TIER2_SCORE:.0%}"
        )
        assert quality.quick_score >= MIN_QUICK_SCORE, (
            f"Quick score below threshold: {quality.quick_score:.0%} < {MIN_QUICK_SCORE:.0%}"
        )
        assert quality.jaccard_similarity >= MIN_JACCARD, (
            f"Jaccard below threshold: {quality.jaccard_similarity:.0%} < {MIN_JACCARD:.0%}"
        )


# =============================================================================
# Edge Cases
# =============================================================================


class TestConversionEdgeCases:
    """Test edge cases in conversion."""

    def test_nonexistent_source_plan(self, auditor: PlanAuditor, tmp_path: Path) -> None:
        """Converter handles missing source gracefully."""
        converter = PlanConverter(auditor=auditor, templates_dir=TEMPLATES_DIR)

        result = converter.convert(
            source_plan=tmp_path / "nonexistent.md",
            output_dir=tmp_path / "output",
        )

        assert not result.success
        assert result.iterations == 0
        assert any("not found" in w.lower() for w in result.warnings)

    @patch.object(PlanConverterClass, "_run_claude")
    def test_empty_claude_response(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Converter handles empty Claude response."""
        mock_run_claude.return_value = ""

        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=1,
        )

        result = converter.convert(
            source_plan=plan1_basic / "master_plan.md",
            output_dir=tmp_path / "output",
        )

        assert not result.success
        assert any("did not produce any valid file output" in w.lower() for w in result.warnings)

    @patch.object(PlanConverterClass, "_run_claude")
    def test_malformed_file_blocks(
        self,
        mock_run_claude: MagicMock,
        auditor: PlanAuditor,
        plan1_basic: Path,
        tmp_path: Path,
    ) -> None:
        """Converter handles malformed file blocks in Claude response."""
        # Missing ---END FILE--- markers
        mock_run_claude.return_value = """
---FILE: MASTER_PLAN.md---
# Some content without end marker

---FILE: phase-1.md
Also malformed
"""

        converter = PlanConverter(
            auditor=auditor,
            templates_dir=TEMPLATES_DIR,
            max_iterations=1,
        )

        result = converter.convert(
            source_plan=plan1_basic / "master_plan.md",
            output_dir=tmp_path / "output",
        )

        # Should fail because no valid files were parsed
        assert not result.success
