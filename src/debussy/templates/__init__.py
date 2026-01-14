"""Template management for debussy init."""

from __future__ import annotations

from pathlib import Path

# Templates are in docs/templates, relative to project root
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "templates"

__all__ = ["TEMPLATES_DIR"]
