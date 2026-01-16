"""Plan auditor for deterministic validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from debussy.core.audit import AuditIssue, AuditResult, AuditSeverity, AuditSummary
from debussy.parsers.master import parse_master_plan
from debussy.parsers.phase import parse_phase

if TYPE_CHECKING:
    from debussy.core.models import MasterPlan, Phase

# Built-in agents provided by Claude Code's Task tool
# Update this list when the Task tool's available agents change
BUILTIN_AGENTS: frozenset[str] = frozenset(
    {
        "Bash",
        "general-purpose",
        "statusline-setup",
        "Explore",
        "Plan",
        "claude-code-guide",
        "debussy",
        "llm-security-expert",
        "python-task-validator",
        "textual-tui-expert",
    }
)

# Patterns to detect agent references in phase files
# Pattern 1: **AGENT:agent-name** in Process Wrapper
AGENT_MARKER_PATTERN = re.compile(r"\*\*AGENT:([a-zA-Z0-9_-]+)\*\*", re.IGNORECASE)
# Pattern 2: subagent_type: agent-name (YAML-style)
SUBAGENT_YAML_PATTERN = re.compile(r"subagent_type:\s*([a-zA-Z0-9_-]+)", re.IGNORECASE)
# Pattern 3: subagent_type="agent-name" or subagent_type='agent-name' (JSON-style)
SUBAGENT_JSON_PATTERN = re.compile(r'subagent_type\s*[=:]\s*["\']([a-zA-Z0-9_-]+)["\']', re.IGNORECASE)


class PlanAuditor:
    """Auditor for validating plan structure deterministically."""

    def __init__(self, agents_dir: Path | None = None) -> None:
        """Initialize the auditor.

        Args:
            agents_dir: Path to the custom agents directory.
                       Defaults to .claude/agents/ relative to master plan.
        """
        self._agents_dir = agents_dir
        self._cached_agents: set[str] | None = None
        self._detected_agents: dict[str, list[str]] = {}  # agent -> list of phase paths

    def audit(self, master_plan_path: Path, verbose: bool = False) -> AuditResult:
        """Run all audit checks on a master plan.

        Args:
            master_plan_path: Path to the master plan markdown file.
            verbose: If True, include extra information in the result.

        Returns:
            AuditResult with pass/fail and list of issues.
        """
        issues: list[AuditIssue] = []
        self._detected_agents = {}  # Reset for each audit run
        self._cached_agents = None  # Reset cache for each run

        # Check master plan exists and can be parsed
        try:
            master = parse_master_plan(master_plan_path)
        except FileNotFoundError:
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.ERROR,
                    code="MASTER_NOT_FOUND",
                    message=f"Master plan not found: {master_plan_path}",
                    location=str(master_plan_path),
                    suggestion="Create a master plan file with a '## Phases' table listing all phase files",
                )
            )
            return AuditResult(
                passed=False,
                issues=issues,
                summary=AuditSummary(
                    master_plan=str(master_plan_path),
                    phases_found=0,
                    phases_valid=0,
                    gates_total=0,
                    errors=1,
                    warnings=0,
                ),
            )
        except Exception as e:
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.ERROR,
                    code="MASTER_PARSE_ERROR",
                    message=f"Failed to parse master plan: {e}",
                    location=str(master_plan_path),
                    suggestion="Check the master plan format. Ensure it has a '## Phases' table with columns: Phase, Title, Focus, Risk, Status",
                )
            )
            return AuditResult(
                passed=False,
                issues=issues,
                summary=AuditSummary(
                    master_plan=str(master_plan_path),
                    phases_found=0,
                    phases_valid=0,
                    gates_total=0,
                    errors=1,
                    warnings=0,
                ),
            )

        # Validate master plan structure
        issues.extend(self._check_master_plan(master))

        # Parse and validate each phase
        phases_valid = 0
        gates_total = 0
        parsed_phases: list[Phase] = []

        for phase in master.phases:
            phase_issues = self._check_phase_file(phase)
            issues.extend(phase_issues)

            # Only parse if phase file exists
            if phase.path.exists():
                try:
                    detailed_phase = parse_phase(phase.path, phase.id)
                    parsed_phases.append(detailed_phase)

                    # Check gates and notes paths
                    issues.extend(self._check_gates(detailed_phase))
                    issues.extend(self._check_notes_paths(detailed_phase))

                    gates_total += len(detailed_phase.gates)
                    if not any(i.severity == AuditSeverity.ERROR for i in phase_issues):
                        phases_valid += 1
                except Exception as e:
                    issues.append(
                        AuditIssue(
                            severity=AuditSeverity.ERROR,
                            code="PHASE_PARSE_ERROR",
                            message=f"Failed to parse phase: {e}",
                            location=str(phase.path),
                            suggestion="Check the phase file format. Ensure it has '## Gates' and '## Tasks' sections",
                        )
                    )

        # Check dependency graph
        issues.extend(self._check_dependencies(parsed_phases))

        # Check custom agent references exist
        agents_dir = self._agents_dir or master_plan_path.parent / ".claude" / "agents"
        issues.extend(self._check_custom_agents(parsed_phases, agents_dir, verbose))

        # Calculate summary
        errors = sum(1 for i in issues if i.severity == AuditSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == AuditSeverity.WARNING)

        summary = AuditSummary(
            master_plan=master.name,
            phases_found=len(master.phases),
            phases_valid=phases_valid,
            gates_total=gates_total,
            errors=errors,
            warnings=warnings,
        )

        passed = errors == 0

        return AuditResult(passed=passed, issues=issues, summary=summary)

    def _check_master_plan(self, master: MasterPlan) -> list[AuditIssue]:
        """Validate master plan structure.

        Args:
            master: Parsed master plan.

        Returns:
            List of audit issues found.
        """
        issues: list[AuditIssue] = []

        # Check if phases table is empty
        if not master.phases:
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.ERROR,
                    code="NO_PHASES",
                    message="Master plan has no phases defined",
                    location=str(master.path),
                    suggestion="Add rows to the '## Phases' table. Each row should link to a phase file: | 1 | [Phase Title](phase-1.md) | Focus | Risk | Pending |",
                )
            )

        return issues

    def _check_phase_file(self, phase: Phase) -> list[AuditIssue]:
        """Validate phase file exists.

        Args:
            phase: Phase metadata from master plan.

        Returns:
            List of audit issues found.
        """
        issues: list[AuditIssue] = []

        if not phase.path.exists():
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.ERROR,
                    code="PHASE_NOT_FOUND",
                    message=f"Phase file not found: {phase.path.name}",
                    location=str(phase.path),
                    suggestion=f"Create the phase file at '{phase.path.name}' or update the master plan to point to an existing file",
                )
            )

        return issues

    def _check_gates(self, phase: Phase) -> list[AuditIssue]:
        """Validate phase has gates defined.

        Args:
            phase: Parsed phase.

        Returns:
            List of audit issues found.
        """
        issues: list[AuditIssue] = []

        if not phase.gates:
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.ERROR,
                    code="MISSING_GATES",
                    message=f"Phase {phase.id} has no gates defined (critical for validation)",
                    location=str(phase.path),
                    suggestion="Add a '## Gates' section with validation commands, e.g.:\n- ruff: 0 errors (command: `uv run ruff check .`)\n- tests: pass (command: `uv run pytest tests/`)",
                )
            )

        return issues

    def _check_notes_paths(self, phase: Phase) -> list[AuditIssue]:
        """Validate notes paths are specified.

        Args:
            phase: Parsed phase.

        Returns:
            List of audit issues found.
        """
        issues: list[AuditIssue] = []

        if not phase.notes_output:
            issues.append(
                AuditIssue(
                    severity=AuditSeverity.WARNING,
                    code="NO_NOTES_OUTPUT",
                    message=f"Phase {phase.id} has no notes output path specified",
                    location=str(phase.path),
                    suggestion="Add '- [ ] Write notes to: `notes/NOTES_phase_X.md`' to the Process Wrapper section",
                )
            )

        return issues

    def _check_dependencies(self, phases: list[Phase]) -> list[AuditIssue]:
        """Validate dependency graph is valid.

        Args:
            phases: List of parsed phases.

        Returns:
            List of audit issues found.
        """
        issues: list[AuditIssue] = []

        phase_ids = {p.id for p in phases}

        for phase in phases:
            # Check if dependencies exist
            for dep_id in phase.depends_on:
                if dep_id not in phase_ids:
                    issues.append(
                        AuditIssue(
                            severity=AuditSeverity.WARNING,
                            code="MISSING_DEPENDENCY",
                            message=f"Phase {phase.id} depends on non-existent phase {dep_id}",
                            location=str(phase.path),
                            suggestion=f"Either add phase {dep_id} to the master plan, or remove the dependency from phase {phase.id}",
                        )
                    )

            # Check for circular dependencies (simple case: self-reference)
            if phase.id in phase.depends_on:
                issues.append(
                    AuditIssue(
                        severity=AuditSeverity.ERROR,
                        code="CIRCULAR_DEPENDENCY",
                        message=f"Phase {phase.id} depends on itself",
                        location=str(phase.path),
                        suggestion=f"Remove the self-dependency from phase {phase.id}'s 'Depends On' field",
                    )
                )

        # Check for circular dependencies (complex case: cycles in graph)
        issues.extend(self._check_dependency_cycles(phases))

        return issues

    def _check_dependency_cycles(self, phases: list[Phase]) -> list[AuditIssue]:
        """Check for circular dependencies in phase graph.

        Args:
            phases: List of parsed phases.

        Returns:
            List of audit issues for circular dependencies.
        """
        issues: list[AuditIssue] = []

        # Build adjacency list
        graph: dict[str, list[str]] = {p.id: p.depends_on for p in phases}

        # DFS to detect cycles
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str, path: list[str]) -> list[str] | None:
            """DFS helper to detect cycles.

            Args:
                node: Current node ID.
                path: Current path from root.

            Returns:
                Path forming the cycle if found, None otherwise.
            """
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    cycle = has_cycle(neighbor, path[:])
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return [*path[cycle_start:], neighbor]

            rec_stack.remove(node)
            return None

        # Check each unvisited node
        for phase in phases:
            if phase.id not in visited:
                cycle = has_cycle(phase.id, [])
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    issues.append(
                        AuditIssue(
                            severity=AuditSeverity.ERROR,
                            code="CIRCULAR_DEPENDENCY",
                            message=f"Circular dependency detected: {cycle_str}",
                            location=None,
                            suggestion=f"Break the cycle by removing one of the dependencies in: {cycle_str}",
                        )
                    )
                    break  # Only report first cycle found

        return issues

    def _extract_agent_references(self, content: str) -> set[str]:
        """Extract all agent references from phase file content.

        Detects agents referenced via:
        - **AGENT:agent-name** markers in Process Wrapper
        - subagent_type: agent-name (YAML-style)
        - subagent_type="agent-name" or subagent_type='agent-name' (JSON-style)

        Args:
            content: The phase file content.

        Returns:
            Set of agent names referenced in the content.
        """
        agents: set[str] = set()

        # Find **AGENT:xxx** markers
        for match in AGENT_MARKER_PATTERN.finditer(content):
            agents.add(match.group(1))

        # Find subagent_type: xxx (YAML-style)
        for match in SUBAGENT_YAML_PATTERN.finditer(content):
            agents.add(match.group(1))

        # Find subagent_type="xxx" or subagent_type='xxx' (JSON-style)
        for match in SUBAGENT_JSON_PATTERN.finditer(content):
            agents.add(match.group(1))

        return agents

    def _scan_agents_directory(self, agents_dir: Path) -> set[str]:
        """Scan the agents directory for available custom agents.

        Caches the result for performance during a single audit run.

        Args:
            agents_dir: Path to the .claude/agents/ directory.

        Returns:
            Set of available agent names (without .md extension).
        """
        if self._cached_agents is not None:
            return self._cached_agents

        agents: set[str] = set()

        if agents_dir.exists() and agents_dir.is_dir():
            for agent_file in agents_dir.glob("*.md"):
                # Agent name is the filename without .md extension
                agents.add(agent_file.stem)

        self._cached_agents = agents
        return agents

    def _check_custom_agents(
        self,
        phases: list[Phase],
        agents_dir: Path,
        verbose: bool = False,
    ) -> list[AuditIssue]:
        """Check that all referenced custom agents exist.

        Args:
            phases: List of parsed phases.
            agents_dir: Path to the .claude/agents/ directory.
            verbose: If True, report all detected agent references as INFO.

        Returns:
            List of audit issues for missing agents.
        """
        issues: list[AuditIssue] = []

        # Collect all agent references from all phases
        for phase in phases:
            if not phase.path.exists():
                continue

            content = phase.path.read_text(encoding="utf-8")
            agents = self._extract_agent_references(content)

            # Track which phases reference each agent
            for agent in agents:
                if agent not in self._detected_agents:
                    self._detected_agents[agent] = []
                self._detected_agents[agent].append(str(phase.path.name))

        # Get available custom agents
        available_agents = self._scan_agents_directory(agents_dir)

        # Check each referenced agent
        for agent, phase_files in sorted(self._detected_agents.items()):
            # Skip built-in agents (case-insensitive comparison)
            if agent.lower() in {b.lower() for b in BUILTIN_AGENTS}:
                if verbose:
                    issues.append(
                        AuditIssue(
                            severity=AuditSeverity.INFO,
                            code="BUILTIN_AGENT",
                            message=f"Built-in agent '{agent}' referenced in: {', '.join(phase_files)}",
                            location=None,
                        )
                    )
                continue

            # Check if custom agent exists
            if agent not in available_agents:
                expected_path = agents_dir / f"{agent}.md"
                issues.append(
                    AuditIssue(
                        severity=AuditSeverity.ERROR,
                        code="MISSING_AGENT",
                        message=f"Missing custom agent '{agent}'",
                        location=f"Referenced in: {', '.join(phase_files)}",
                        suggestion=f"Create the agent file at: {expected_path}",
                    )
                )
            elif verbose:
                issues.append(
                    AuditIssue(
                        severity=AuditSeverity.INFO,
                        code="CUSTOM_AGENT",
                        message=f"Custom agent '{agent}' found in: {', '.join(phase_files)}",
                        location=str(agents_dir / f"{agent}.md"),
                    )
                )

        return issues

    def get_detected_agents(self) -> dict[str, list[str]]:
        """Get all detected agent references from the last audit.

        Returns:
            Dict mapping agent names to lists of phase file names.
        """
        return dict(self._detected_agents)
