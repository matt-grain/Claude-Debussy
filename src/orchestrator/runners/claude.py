"""Claude CLI subprocess runner."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from orchestrator.core.models import ComplianceIssue, ExecutionResult, Phase


class ClaudeRunner:
    """Spawns and monitors Claude CLI sessions."""

    def __init__(
        self,
        project_root: Path,
        timeout: int = 1800,
        claude_command: str = "claude",
    ) -> None:
        self.project_root = project_root
        self.timeout = timeout
        self.claude_command = claude_command

    async def execute_phase(
        self,
        phase: Phase,
        custom_prompt: str | None = None,
    ) -> ExecutionResult:
        """Execute a phase using Claude CLI.

        Args:
            phase: The phase to execute
            custom_prompt: Optional custom prompt (for remediation sessions)

        Returns:
            ExecutionResult with success status and session log
        """
        prompt = custom_prompt or self._build_phase_prompt(phase)

        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                self.claude_command,
                "--print",  # Non-interactive mode
                "-p",
                prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    session_log=f"TIMEOUT after {self.timeout} seconds",
                    exit_code=-1,
                    duration_seconds=time.time() - start_time,
                    pid=process.pid,
                )

            session_log = stdout.decode("utf-8", errors="replace")
            if stderr:
                session_log += f"\n\nSTDERR:\n{stderr.decode('utf-8', errors='replace')}"

            return ExecutionResult(
                success=process.returncode == 0,
                session_log=session_log,
                exit_code=process.returncode or 0,
                duration_seconds=time.time() - start_time,
                pid=process.pid,
            )

        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                session_log=f"Claude CLI not found: {self.claude_command}",
                exit_code=-1,
                duration_seconds=time.time() - start_time,
                pid=None,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                session_log=f"Error spawning Claude: {e}",
                exit_code=-1,
                duration_seconds=time.time() - start_time,
                pid=None,
            )

    def _build_phase_prompt(self, phase: Phase) -> str:
        """Build the prompt for a phase execution."""
        notes_context = ""
        if phase.notes_input and phase.notes_input.exists():
            notes_context = f"""
## Previous Phase Notes
Read the context from the previous phase: `{phase.notes_input}`
"""

        required_agents = ""
        if phase.required_agents:
            agents_list = ", ".join(phase.required_agents)
            required_agents = f"""
## Required Agents
You MUST invoke these agents using the Task tool: {agents_list}
"""

        notes_output = ""
        if phase.notes_output:
            notes_output = f"""
## Notes Output
When complete, write notes to: `{phase.notes_output}`
"""

        return f"""Execute the implementation phase defined in: `{phase.path}`

Read the phase plan file and follow the Process Wrapper EXACTLY.
{notes_context}
{required_agents}
{notes_output}
## Completion

When the phase is complete (all tasks done, all gates passing):
1. Write notes to the specified output path
2. Run: `orchestrate done --phase {phase.id} --report '{{...}}'`

If you encounter a blocker that prevents completion:
- Run: `orchestrate done --phase {phase.id} --status blocked --reason "description"`

## Important

- Follow the template Process Wrapper exactly
- Use the Task tool to invoke required agents (don't do their work yourself)
- Run all pre-validation commands until they pass
- The orchestrator will verify your work - be thorough
"""

    def build_remediation_prompt(
        self,
        phase: Phase,
        issues: list[ComplianceIssue],
    ) -> str:
        """Build a remediation prompt for a failed compliance check."""
        issues_text = "\n".join(
            f"- [{issue.severity.upper()}] {issue.type.value}: {issue.details}" for issue in issues
        )

        required_actions: list[str] = []
        for issue in issues:
            if issue.type.value == "agent_skipped":
                agent_name = issue.details.split("'")[1]
                required_actions.append(f"- Invoke the {agent_name} agent using Task tool")
            elif issue.type.value == "notes_missing":
                required_actions.append(f"- Write notes to: {phase.notes_output}")
            elif issue.type.value == "notes_incomplete":
                required_actions.append("- Complete all required sections in the notes file")
            elif issue.type.value == "gates_failed":
                required_actions.append(f"- Fix failing gate: {issue.details}")
            elif issue.type.value == "step_skipped":
                required_actions.append(f"- Complete step: {issue.details}")

        default_action = "- Review and fix all issues"
        actions_text = "\n".join(required_actions) if required_actions else default_action

        return f"""REMEDIATION SESSION for Phase {phase.id}: {phase.title}

The previous attempt FAILED compliance checks.

## Issues Found
{issues_text}

## Required Actions
{actions_text}

## Original Phase Plan
Read and follow: `{phase.path}`

## When Complete
Run: `orchestrate done --phase {phase.id} --report '{{...}}'`

IMPORTANT: This is a remediation session. Follow the template EXACTLY.
All required agents MUST be invoked via the Task tool - do not do their work yourself.
"""
