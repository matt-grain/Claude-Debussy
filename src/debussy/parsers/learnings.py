"""Parser for extracting learnings from phase notes files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Learning:
    """A single learning extracted from notes."""

    content: str
    phase_id: str
    source_file: Path


def extract_learnings(notes_path: Path, phase_id: str) -> list[Learning]:
    """Extract learnings from a notes file.

    Looks for a ## Learnings section and extracts each bullet point as a learning.

    Args:
        notes_path: Path to the notes markdown file
        phase_id: The phase ID for tagging

    Returns:
        List of Learning objects extracted from the file
    """
    if not notes_path.exists():
        return []

    content = notes_path.read_text(encoding="utf-8")

    # Find the ## Learnings section
    # Match "## Learnings" followed by content until next ## heading or end of file
    pattern = r"##\s*Learnings\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if not match:
        return []

    learnings_section = match.group(1).strip()
    if not learnings_section:
        return []

    learnings: list[Learning] = []

    # Extract bullet points (- or *)
    for raw_line in learnings_section.split("\n"):
        line = raw_line.strip()
        if line.startswith(("-", "*")):
            # Remove the bullet and clean up
            learning_text = line[1:].strip()
            if learning_text:
                learnings.append(
                    Learning(
                        content=learning_text,
                        phase_id=phase_id,
                        source_file=notes_path,
                    )
                )

    return learnings
