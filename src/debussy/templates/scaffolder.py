"""Scaffold new plans from templates."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


class PlanScaffolder:
    """Scaffold new plans from templates."""

    def __init__(self, templates_dir: Path):
        """Initialize scaffolder with templates directory.

        Args:
            templates_dir: Path to the templates directory
        """
        self.templates_dir = templates_dir

    def scaffold(
        self,
        feature_name: str,
        output_dir: Path,
        num_phases: int = 3,
        template_type: str = "generic",
    ) -> list[Path]:
        """Generate plan files from templates.

        Args:
            feature_name: Name of the feature (used in filenames and content)
            output_dir: Directory to write generated files
            num_phases: Number of phase files to generate
            template_type: "generic", "backend", or "frontend"

        Returns:
            List of created file paths.

        Raises:
            ValueError: If template_type is invalid or templates not found.
            FileNotFoundError: If template files don't exist.
        """
        if num_phases < 1:
            msg = f"Number of phases must be at least 1, got {num_phases}"
            raise ValueError(msg)

        if template_type not in ["generic", "backend", "frontend"]:
            msg = f"Unknown template type: {template_type}"
            raise ValueError(msg)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate variables for substitution
        date_str = datetime.now().strftime("%Y-%m-%d")
        feature_slug = self._slugify(feature_name)

        created_files: list[Path] = []

        # 1. Generate master plan
        master_path = output_dir / "MASTER_PLAN.md"
        master_content = self._generate_master_plan(
            feature_name=feature_name,
            feature_slug=feature_slug,
            num_phases=num_phases,
            date=date_str,
        )
        master_path.write_text(master_content, encoding="utf-8")
        created_files.append(master_path)

        # 2. Generate phase files
        for phase_num in range(1, num_phases + 1):
            phase_path = output_dir / f"{feature_slug}-phase-{phase_num}.md"
            phase_content = self._generate_phase(
                feature_name=feature_name,
                feature_slug=feature_slug,
                phase_num=phase_num,
                total_phases=num_phases,
                template_type=template_type,
            )
            phase_path.write_text(phase_content, encoding="utf-8")
            created_files.append(phase_path)

        return created_files

    def _load_template(self, name: str) -> str:
        """Load template content from file.

        Args:
            name: Template filename (e.g., "MASTER_TEMPLATE.md" or "PHASE_GENERIC.md")

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

    def _substitute(self, template_str: str, variables: dict[str, str]) -> str:
        """Replace {placeholders} in template with values.

        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variable names to values

        Returns:
            String with all placeholders replaced
        """
        result = template_str
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def _slugify(self, text: str) -> str:
        """Convert text to filename-safe slug.

        Args:
            text: Text to convert

        Returns:
            Slugified version (e.g., "User Auth" -> "user-auth")
        """
        # Convert to lowercase, replace spaces with hyphens
        slug = text.lower().strip()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r"[\s_]+", "-", slug)
        # Remove non-alphanumeric characters (except hyphens)
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")

    def _generate_master_plan(
        self,
        feature_name: str,
        feature_slug: str,
        num_phases: int,
        date: str,
    ) -> str:
        """Generate master plan content from template.

        Args:
            feature_name: Human-readable feature name
            feature_slug: Filename-safe slug
            num_phases: Number of phases
            date: Date string (YYYY-MM-DD)

        Returns:
            Generated master plan content
        """
        template = self._load_template("MASTER_TEMPLATE.md")

        # Build phase table rows dynamically
        phase_rows = []
        for i in range(1, num_phases + 1):
            phase_title = f"Phase {i}"
            row = f"| {i} | [{phase_title}]({feature_slug}-phase-{i}.md) | {{Brief focus}} | Low | Pending |"
            phase_rows.append(row)

        phase_table = "\n".join(phase_rows)

        variables = {
            "feature": feature_name,
            "date": date,
            "feature_slug": feature_slug,
            "phase_1_title": "Phase 1",
            "phase_2_title": "Phase 2" if num_phases >= 2 else "",
            "phase_3_title": "Phase 3" if num_phases >= 3 else "",
        }

        content = self._substitute(template, variables)

        # Replace the phase table section dynamically
        # Find the phases table and replace with generated rows
        content = re.sub(
            r"\| Phase \| Title.*?\n\|.*?\n(\|.*?\n)+",
            f"| Phase | Title | Focus | Risk | Status |\n|-------|-------|-------|------|--------|\n{phase_table}\n",
            content,
            flags=re.MULTILINE,
        )

        return content

    def _generate_phase(
        self,
        feature_name: str,
        feature_slug: str,
        phase_num: int,
        total_phases: int,  # noqa: ARG002
        template_type: str,
    ) -> str:
        """Generate phase file content from template.

        Args:
            feature_name: Human-readable feature name
            feature_slug: Filename-safe slug
            phase_num: This phase number (1-indexed)
            total_phases: Total number of phases (reserved for future use)
            template_type: "generic", "backend", or "frontend"

        Returns:
            Generated phase content
        """
        # Select template based on type
        template_map = {
            "generic": "PHASE_GENERIC.md",
            "backend": "PHASE_BACKEND.md",
            "frontend": "PHASE_FRONTEND.md",
        }
        template = self._load_template(template_map[template_type])

        # Determine previous phase
        if phase_num == 1:
            prev_phase_link = "N/A"
            prev_notes_path = "N/A"
        else:
            prev_num = phase_num - 1
            prev_phase_link = f"[Phase {prev_num}]({feature_slug}-phase-{prev_num}.md)"
            prev_notes_path = f"notes/NOTES_{feature_slug}_phase_{prev_num}.md"

        # Notes output for this phase
        notes_output_path = f"notes/NOTES_{feature_slug}_phase_{phase_num}.md"

        variables = {
            "feature": feature_name,
            "feature_slug": feature_slug,
            "phase_num": str(phase_num),
            "phase_title": f"Phase {phase_num}",
            "prev_phase_link": prev_phase_link,
            "prev_notes_path": prev_notes_path,
            "notes_output_path": notes_output_path,
        }

        return self._substitute(template, variables)
