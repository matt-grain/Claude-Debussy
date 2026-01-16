"""Unit tests for agent validation in PlanAuditor."""

from __future__ import annotations

from pathlib import Path

from debussy.core.audit import AuditSeverity
from debussy.core.auditor import (
    AGENT_MARKER_PATTERN,
    BUILTIN_AGENTS,
    SUBAGENT_JSON_PATTERN,
    SUBAGENT_YAML_PATTERN,
    PlanAuditor,
)


class TestAgentReferencePatterns:
    """Test regex patterns for detecting agent references."""

    def test_agent_marker_pattern_basic(self) -> None:
        """Test **AGENT:name** pattern detection."""
        content = "- [ ] **AGENT:my-custom-agent** - do something"
        matches = AGENT_MARKER_PATTERN.findall(content)
        assert matches == ["my-custom-agent"]

    def test_agent_marker_pattern_multiple(self) -> None:
        """Test multiple **AGENT:name** patterns."""
        content = """
        - [ ] **AGENT:doc-sync-manager** - sync tasks
        - [ ] **AGENT:task-validator** - validation
        """
        matches = AGENT_MARKER_PATTERN.findall(content)
        assert set(matches) == {"doc-sync-manager", "task-validator"}

    def test_agent_marker_pattern_case_insensitive(self) -> None:
        """Test case insensitivity for **AGENT:name**."""
        content = "- [ ] **agent:My-Agent** - task"
        matches = AGENT_MARKER_PATTERN.findall(content)
        assert matches == ["My-Agent"]

    def test_subagent_yaml_pattern(self) -> None:
        """Test subagent_type: name pattern."""
        content = "subagent_type: Explore"
        matches = SUBAGENT_YAML_PATTERN.findall(content)
        assert matches == ["Explore"]

    def test_subagent_yaml_pattern_with_spaces(self) -> None:
        """Test subagent_type:  name with extra spaces."""
        content = "subagent_type:   my-agent"
        matches = SUBAGENT_YAML_PATTERN.findall(content)
        assert matches == ["my-agent"]

    def test_subagent_json_pattern_double_quotes(self) -> None:
        """Test subagent_type="name" pattern."""
        content = 'subagent_type="my-agent"'
        matches = SUBAGENT_JSON_PATTERN.findall(content)
        assert matches == ["my-agent"]

    def test_subagent_json_pattern_single_quotes(self) -> None:
        """Test subagent_type='name' pattern."""
        content = "subagent_type='my-agent'"
        matches = SUBAGENT_JSON_PATTERN.findall(content)
        assert matches == ["my-agent"]

    def test_subagent_json_pattern_with_equals(self) -> None:
        """Test subagent_type = "name" with spaces."""
        content = 'subagent_type = "custom-agent"'
        matches = SUBAGENT_JSON_PATTERN.findall(content)
        assert matches == ["custom-agent"]


class TestBuiltinAgentsList:
    """Test the built-in agents constant."""

    def test_builtin_agents_contains_expected(self) -> None:
        """Test that BUILTIN_AGENTS contains expected core agents."""
        expected = {"Bash", "Explore", "Plan", "general-purpose"}
        assert expected.issubset(BUILTIN_AGENTS)

    def test_builtin_agents_includes_debussy(self) -> None:
        """Test that debussy is in BUILTIN_AGENTS."""
        assert "debussy" in BUILTIN_AGENTS

    def test_builtin_agents_includes_custom_agents(self) -> None:
        """Test that project-specific built-in agents are included."""
        expected = {
            "llm-security-expert",
            "python-task-validator",
            "textual-tui-expert",
        }
        assert expected.issubset(BUILTIN_AGENTS)


class TestExtractAgentReferences:
    """Test _extract_agent_references method."""

    def test_extract_no_agents(self) -> None:
        """Test extraction from content with no agent references."""
        auditor = PlanAuditor()
        content = """
        # Phase 1: Setup

        ## Tasks
        - [ ] 1.1: Do something basic
        """
        agents = auditor._extract_agent_references(content)
        assert agents == set()

    def test_extract_marker_agents(self) -> None:
        """Test extraction of **AGENT:name** markers."""
        auditor = PlanAuditor()
        content = """
        ## Process Wrapper
        - [ ] **AGENT:doc-sync-manager** - sync
        - [ ] **AGENT:task-validator** - validate
        """
        agents = auditor._extract_agent_references(content)
        assert agents == {"doc-sync-manager", "task-validator"}

    def test_extract_subagent_yaml(self) -> None:
        """Test extraction of subagent_type: name patterns."""
        auditor = PlanAuditor()
        content = """
        Use Task tool with subagent_type: Explore to find files.
        Then use subagent_type: Plan for planning.
        """
        agents = auditor._extract_agent_references(content)
        assert agents == {"Explore", "Plan"}

    def test_extract_subagent_json(self) -> None:
        """Test extraction of subagent_type="name" patterns."""
        auditor = PlanAuditor()
        content = """
        <invoke name="Task">
        subagent_type="my-custom-agent"
        subagent_type='another-agent'
        """
        agents = auditor._extract_agent_references(content)
        assert agents == {"my-custom-agent", "another-agent"}

    def test_extract_mixed_patterns(self) -> None:
        """Test extraction from content with all pattern types."""
        auditor = PlanAuditor()
        content = """
        ## Process Wrapper
        - [ ] **AGENT:doc-sync** - sync

        Use subagent_type: Explore for search.
        Use subagent_type="custom-tool" for processing.
        """
        agents = auditor._extract_agent_references(content)
        assert agents == {"doc-sync", "Explore", "custom-tool"}


class TestScanAgentsDirectory:
    """Test _scan_agents_directory method."""

    def test_scan_empty_directory(self, temp_dir: Path) -> None:
        """Test scanning empty agents directory."""
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()

        auditor = PlanAuditor()
        agents = auditor._scan_agents_directory(agents_dir)
        assert agents == set()

    def test_scan_directory_with_agents(self, temp_dir: Path) -> None:
        """Test scanning directory with agent files."""
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "my-agent.md").write_text("# My Agent")
        (agents_dir / "another-agent.md").write_text("# Another Agent")

        auditor = PlanAuditor()
        agents = auditor._scan_agents_directory(agents_dir)
        assert agents == {"my-agent", "another-agent"}

    def test_scan_nonexistent_directory(self, temp_dir: Path) -> None:
        """Test scanning non-existent agents directory."""
        agents_dir = temp_dir / "nonexistent"

        auditor = PlanAuditor()
        agents = auditor._scan_agents_directory(agents_dir)
        assert agents == set()

    def test_scan_ignores_non_md_files(self, temp_dir: Path) -> None:
        """Test that non-.md files are ignored."""
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "my-agent.md").write_text("# My Agent")
        (agents_dir / "readme.txt").write_text("Not an agent")
        (agents_dir / "config.json").write_text("{}")

        auditor = PlanAuditor()
        agents = auditor._scan_agents_directory(agents_dir)
        assert agents == {"my-agent"}

    def test_scan_caches_results(self, temp_dir: Path) -> None:
        """Test that directory scan results are cached."""
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "agent1.md").write_text("# Agent 1")

        auditor = PlanAuditor()

        # First scan
        agents1 = auditor._scan_agents_directory(agents_dir)
        assert agents1 == {"agent1"}

        # Add another agent file
        (agents_dir / "agent2.md").write_text("# Agent 2")

        # Second scan should return cached result
        agents2 = auditor._scan_agents_directory(agents_dir)
        assert agents2 == {"agent1"}  # Still cached

        # Reset cache
        auditor._cached_agents = None
        agents3 = auditor._scan_agents_directory(agents_dir)
        assert agents3 == {"agent1", "agent2"}  # Now includes new agent


class TestAgentValidation:
    """Integration tests for agent validation in audit."""

    def test_valid_custom_agents_pass(self, temp_dir: Path) -> None:
        """Test that valid custom agents pass audit."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with custom agent reference
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **AGENT:my-custom-agent** - do task
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        # Create agents directory with the custom agent
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "my-custom-agent.md").write_text("# My Custom Agent\n\nDoes tasks.")

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass - custom agent exists
        assert result.passed
        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 0

    def test_missing_custom_agent_fails(self, temp_dir: Path) -> None:
        """Test that missing custom agents cause audit failure."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with custom agent reference
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **AGENT:nonexistent-agent** - do task
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        # Create empty agents directory
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should fail - custom agent missing
        assert not result.passed
        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 1
        assert missing_agents[0].severity == AuditSeverity.ERROR
        assert "nonexistent-agent" in missing_agents[0].message

    def test_error_message_includes_expected_path(self, temp_dir: Path) -> None:
        """Test that error message includes expected file path."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with custom agent reference
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **AGENT:my-missing-agent** - do task

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        # Create empty agents directory
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 1
        assert missing_agents[0].suggestion is not None
        assert "my-missing-agent.md" in missing_agents[0].suggestion
        # Check for path (handle both Unix and Windows separators)
        suggestion = str(missing_agents[0].suggestion)
        assert ".claude" in suggestion and "agents" in suggestion

    def test_builtin_agents_not_flagged(self, temp_dir: Path) -> None:
        """Test that built-in agents are not flagged as missing."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with built-in agent references
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **AGENT:Explore** - search codebase
- [ ] **AGENT:Plan** - plan implementation
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Use subagent_type: Bash for commands
- [ ] 1.2: Use subagent_type="general-purpose" for general tasks
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        # No agents directory needed for built-ins

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass - only built-in agents
        assert result.passed
        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 0

    def test_plans_with_no_agents_pass(self, temp_dir: Path) -> None:
        """Test that plans with no agent references pass."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with no agent references
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something manually
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass - no agents to validate
        assert result.passed
        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 0

    def test_verbose_mode_lists_agents(self, temp_dir: Path) -> None:
        """Test that verbose mode lists all detected agents."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with agent references
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper (MANDATORY)
- [ ] **AGENT:my-agent** - custom task
- [ ] Use subagent_type: Explore for search

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        # Create custom agent
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "my-agent.md").write_text("# My Agent")

        auditor = PlanAuditor()
        result = auditor.audit(master_path, verbose=True)

        # Should have INFO issues for detected agents
        info_issues = [i for i in result.issues if i.severity == AuditSeverity.INFO]
        assert len(info_issues) >= 2  # At least built-in and custom agent

        # Check for built-in agent info
        builtin_info = [i for i in info_issues if i.code == "BUILTIN_AGENT"]
        assert len(builtin_info) >= 1

        # Check for custom agent info
        custom_info = [i for i in info_issues if i.code == "CUSTOM_AGENT"]
        assert len(custom_info) == 1
        assert "my-agent" in custom_info[0].message

    def test_builtin_agent_case_insensitive(self, temp_dir: Path) -> None:
        """Test that built-in agent matching is case insensitive."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Create phase with various case built-in agents
        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Use subagent_type: explore
- [ ] 1.2: Use subagent_type: BASH
- [ ] 1.3: Use subagent_type: General-Purpose
"""
        phase_path = temp_dir / "phase-1.md"
        phase_path.write_text(phase_content)

        auditor = PlanAuditor()
        result = auditor.audit(master_path)

        # Should pass - all are built-in agents (case insensitive)
        missing_agents = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing_agents) == 0

    def test_get_detected_agents(self, temp_dir: Path) -> None:
        """Test get_detected_agents returns all detected agents."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
| 2 | [Phase Two](phase-2.md) | Build | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        # Phase 1 references agent-a
        phase1_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper
- [ ] **AGENT:agent-a** - task

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        (temp_dir / "phase-1.md").write_text(phase1_content)

        # Phase 2 references agent-a and agent-b
        phase2_content = """\
# Phase 2: Phase Two

**Status:** Pending
**Depends On:** [Phase 1](phase-1.md)

## Process Wrapper
- [ ] **AGENT:agent-a** - task a
- [ ] **AGENT:agent-b** - task b

## Gates

- ruff: 0 errors

## Tasks

### 1. Build
- [ ] 1.1: Build something
"""
        (temp_dir / "phase-2.md").write_text(phase2_content)

        # Create agents directory with both agents
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "agent-a.md").write_text("# Agent A")
        (agents_dir / "agent-b.md").write_text("# Agent B")

        auditor = PlanAuditor()
        auditor.audit(master_path)

        detected = auditor.get_detected_agents()
        assert "agent-a" in detected
        assert "agent-b" in detected
        assert len(detected["agent-a"]) == 2  # Referenced in both phases
        assert len(detected["agent-b"]) == 1  # Referenced in phase 2 only


class TestAuditorAgentsDirParameter:
    """Test custom agents_dir parameter."""

    def test_custom_agents_dir(self, temp_dir: Path) -> None:
        """Test using custom agents_dir parameter."""
        # Create master plan
        master_content = """\
# Test Plan

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase-1.md) | Setup | Low | Pending |
"""
        master_path = temp_dir / "MASTER_PLAN.md"
        master_path.write_text(master_content)

        phase_content = """\
# Phase 1: Phase One

**Status:** Pending

## Process Wrapper
- [ ] **AGENT:custom-agent** - task

## Gates

- ruff: 0 errors

## Tasks

### 1. Setup
- [ ] 1.1: Do something
"""
        (temp_dir / "phase-1.md").write_text(phase_content)

        # Create agent in custom location
        custom_agents_dir = temp_dir / "custom-agents"
        custom_agents_dir.mkdir()
        (custom_agents_dir / "custom-agent.md").write_text("# Custom Agent")

        # Audit with custom agents_dir
        auditor = PlanAuditor(agents_dir=custom_agents_dir)
        result = auditor.audit(master_path)

        # Should pass - agent exists in custom directory
        assert result.passed
        missing = [i for i in result.issues if i.code == "MISSING_AGENT"]
        assert len(missing) == 0


class TestAgentValidationEdgeCases:
    """Edge case tests for agent validation."""

    def test_empty_phase_file(self) -> None:
        """Test handling of empty phase file content."""
        auditor = PlanAuditor()
        agents = auditor._extract_agent_references("")
        assert agents == set()

    def test_agent_name_with_underscores(self) -> None:
        """Test agent names with underscores."""
        auditor = PlanAuditor()
        content = "**AGENT:my_agent_name** - task"
        agents = auditor._extract_agent_references(content)
        assert agents == {"my_agent_name"}

    def test_agent_name_with_numbers(self) -> None:
        """Test agent names with numbers."""
        auditor = PlanAuditor()
        content = "**AGENT:agent123** and subagent_type: version2-agent"
        agents = auditor._extract_agent_references(content)
        assert agents == {"agent123", "version2-agent"}

    def test_multiple_same_agent_references(self) -> None:
        """Test same agent referenced multiple times."""
        auditor = PlanAuditor()
        content = """
        **AGENT:my-agent** - first
        **AGENT:my-agent** - second
        subagent_type: my-agent
        """
        agents = auditor._extract_agent_references(content)
        # Should only appear once (set)
        assert agents == {"my-agent"}

    def test_subagent_in_code_block(self) -> None:
        """Test subagent_type patterns in code blocks are still detected."""
        auditor = PlanAuditor()
        content = """
        ```python
        task_tool.invoke(subagent_type="code-reviewer")
        ```
        """
        agents = auditor._extract_agent_references(content)
        assert agents == {"code-reviewer"}

    def test_agents_dir_with_subdirectories(self, temp_dir: Path) -> None:
        """Test that subdirectories in agents dir don't cause issues."""
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "valid-agent.md").write_text("# Valid")
        (agents_dir / "subdir").mkdir()
        (agents_dir / "subdir" / "nested-agent.md").write_text("# Nested")

        auditor = PlanAuditor()
        agents = auditor._scan_agents_directory(agents_dir)
        # Should only find top-level .md files
        assert agents == {"valid-agent"}
