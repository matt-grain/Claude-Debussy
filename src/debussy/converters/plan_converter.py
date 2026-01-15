"""Convert freeform plans to Debussy format using Claude."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from debussy.converters.prompts import CONVERSION_PROMPT, REMEDIATION_SECTION

if TYPE_CHECKING:
    from debussy.core.audit import AuditIssue
    from debussy.core.auditor import PlanAuditor


class ConversionResult(BaseModel):
    """Result of a plan conversion attempt."""

    success: bool = Field(description="Whether conversion succeeded and passed audit")
    iterations: int = Field(description="Number of conversion attempts made")
    files_created: list[str] = Field(default_factory=list, description="Paths to created files")
    audit_passed: bool = Field(default=False, description="Whether final audit passed")
    audit_errors: int = Field(default=0, description="Number of audit errors")
    audit_warnings: int = Field(default=0, description="Number of audit warnings")
    warnings: list[str] = Field(default_factory=list, description="Conversion warnings")


class PlanConverter:
    """Convert freeform plans to Debussy format using Claude."""

    def __init__(
        self,
        auditor: PlanAuditor,
        templates_dir: Path,
        max_iterations: int = 3,
        model: str = "haiku",
        timeout: int = 120,
    ) -> None:
        """Initialize the plan converter.

        Args:
            auditor: PlanAuditor instance for validating output
            templates_dir: Path to templates directory
            max_iterations: Maximum conversion attempts before giving up
            model: Claude model to use (haiku recommended for cost)
            timeout: Timeout for Claude CLI calls in seconds
        """
        self.auditor = auditor
        self.templates_dir = templates_dir
        self.max_iterations = max_iterations
        self.model = model
        self.timeout = timeout

    def convert(  # noqa: PLR0911
        self,
        source_plan: Path,
        output_dir: Path,
        interactive: bool = False,  # noqa: ARG002
    ) -> ConversionResult:
        """Convert a freeform plan to structured format.

        Args:
            source_plan: Path to freeform plan markdown
            output_dir: Directory to write structured files
            interactive: If True, ask clarifying questions (not implemented yet)

        Returns:
            ConversionResult with success status and created files.
        """
        # Read source content
        if not source_plan.exists():
            return ConversionResult(
                success=False,
                iterations=0,
                warnings=[f"Source plan not found: {source_plan}"],
            )

        source_content = source_plan.read_text(encoding="utf-8")

        # Load templates
        try:
            master_template = self._load_template("MASTER_TEMPLATE.md")
            phase_template = self._load_template("PHASE_GENERIC.md")
        except FileNotFoundError as e:
            return ConversionResult(
                success=False,
                iterations=0,
                warnings=[str(e)],
            )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Conversion loop with audit feedback
        previous_issues: list[AuditIssue] | None = None
        files_created: list[str] = []

        for iteration in range(1, self.max_iterations + 1):
            # Build prompt
            prompt = self._build_conversion_prompt(
                source_content=source_content,
                master_template=master_template,
                phase_template=phase_template,
                previous_issues=previous_issues,
            )

            # Run Claude to generate files
            try:
                claude_output = self._run_claude(prompt)
            except subprocess.TimeoutExpired:
                return ConversionResult(
                    success=False,
                    iterations=iteration,
                    files_created=files_created,
                    warnings=[f"Claude timed out after {self.timeout}s"],
                )
            except FileNotFoundError:
                return ConversionResult(
                    success=False,
                    iterations=iteration,
                    files_created=files_created,
                    warnings=["Claude CLI not found. Install it first."],
                )

            # Parse output and write files
            generated_files = self._parse_file_output(claude_output)
            if not generated_files:
                return ConversionResult(
                    success=False,
                    iterations=iteration,
                    files_created=files_created,
                    warnings=["Claude did not produce any valid file output"],
                )

            # Write files to output directory
            files_created = []
            for filename, content in generated_files.items():
                file_path = output_dir / filename
                file_path.write_text(content, encoding="utf-8")
                files_created.append(str(file_path))

            # Run audit on generated master plan
            master_plan_path = output_dir / "MASTER_PLAN.md"
            if not master_plan_path.exists():
                # Claude didn't generate master plan - critical error
                previous_issues = None  # Reset issues
                continue

            audit_result = self.auditor.audit(master_plan_path)

            if audit_result.passed:
                return ConversionResult(
                    success=True,
                    iterations=iteration,
                    files_created=files_created,
                    audit_passed=True,
                    audit_errors=audit_result.summary.errors,
                    audit_warnings=audit_result.summary.warnings,
                )

            # Audit failed - use issues to guide next iteration
            previous_issues = audit_result.issues

        # All iterations exhausted
        final_audit = self.auditor.audit(output_dir / "MASTER_PLAN.md")
        return ConversionResult(
            success=False,
            iterations=self.max_iterations,
            files_created=files_created,
            audit_passed=final_audit.passed,
            audit_errors=final_audit.summary.errors,
            audit_warnings=final_audit.summary.warnings,
            warnings=[f"Conversion failed after {self.max_iterations} attempts"],
        )

    def _load_template(self, name: str) -> str:
        """Load template content from file.

        Args:
            name: Template filename (e.g., "MASTER_TEMPLATE.md")

        Returns:
            Template content as string.

        Raises:
            FileNotFoundError: If template file doesn't exist.
        """
        template_path = self.templates_dir / "plans" / name
        if not template_path.exists():
            msg = f"Template not found: {template_path}"
            raise FileNotFoundError(msg)
        return template_path.read_text(encoding="utf-8")

    def _build_conversion_prompt(
        self,
        source_content: str,
        master_template: str,
        phase_template: str,
        previous_issues: list[AuditIssue] | None = None,
    ) -> str:
        """Build prompt for Claude to do conversion.

        Args:
            source_content: Content of the source freeform plan
            master_template: Master plan template content
            phase_template: Phase file template content
            previous_issues: Issues from previous attempt (for remediation)

        Returns:
            Complete prompt string for Claude.
        """
        # Build previous issues section if needed
        previous_issues_section = ""
        if previous_issues:
            issues_text = "\n".join(f"- [{issue.severity.value}] {issue.code}: {issue.message}" for issue in previous_issues)
            previous_issues_section = REMEDIATION_SECTION.format(issues=issues_text)

        return CONVERSION_PROMPT.format(
            source_content=source_content,
            master_template=master_template,
            phase_template=phase_template,
            previous_issues_section=previous_issues_section,
        )

    def _run_claude(self, prompt: str) -> str:
        """Run Claude CLI with the given prompt.

        Uses stdin to pass the prompt to avoid command-line length limits
        on Windows (32KB limit). This allows prompts of any size.

        Args:
            prompt: Prompt to send to Claude

        Returns:
            Claude's output text.

        Raises:
            subprocess.TimeoutExpired: If Claude times out.
            FileNotFoundError: If Claude CLI is not installed.
        """
        # Use stdin (-) to avoid Windows command-line length limits
        # Use --system-prompt to ensure clean output without custom personalities
        # Use --no-session-persistence to avoid polluting session history
        result = subprocess.run(
            [
                "claude",
                "--print",
                "-p", "-",
                "--model", self.model,
                "--system-prompt", "You are a plan conversion assistant. Output only the requested file content in the exact format specified. No commentary.",
                "--no-session-persistence",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        return result.stdout

    def _parse_file_output(self, output: str) -> dict[str, str]:
        """Parse ---FILE: name--- blocks from Claude output.

        Args:
            output: Claude's raw output text

        Returns:
            Dictionary mapping filename to content.
        """
        files: dict[str, str] = {}
        pattern = r"---FILE:\s*(.+?)---\n(.*?)---END FILE---"
        for match in re.finditer(pattern, output, re.DOTALL):
            filename = match.group(1).strip()
            content = match.group(2).strip()
            files[filename] = content
        return files
