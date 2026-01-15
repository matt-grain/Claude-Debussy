"""Prompts for Claude-powered plan conversion."""

from __future__ import annotations

CONVERSION_PROMPT = """
You are converting a freeform implementation plan into Debussy's structured format.

## Source Plan
{source_content}

## Target Structure
You must create these files:
1. MASTER_PLAN.md - Master plan with phases table
2. phase-1.md, phase-2.md, etc. - One file per phase

## Master Plan Template (MUST FOLLOW EXACTLY)
{master_template}

## Phase Template (MUST FOLLOW EXACTLY)
{phase_template}

## Critical Requirements
1. The phases table MUST use this exact format:
   | Phase | Title | Focus | Risk | Status |
   |-------|-------|-------|------|--------|
   | 1 | [Phase Title](phase-1.md) | Brief focus | Low/Medium/High | Pending |

2. Each phase file MUST have:
   - ## Gates section with validation commands (e.g., `command: uv run ruff check .`)
   - ## Process Wrapper section with checkbox items
   - ## Tasks section with checkbox items
   - A notes output path in Process Wrapper (e.g., Write `notes/NOTES_feature_phase_1.md`)

3. If the source plan doesn't specify validation commands, infer reasonable ones:
   - Python projects: ruff, pyright, pytest
   - JavaScript/TypeScript: eslint, tsc, jest/vitest
   - General: tests, build

4. Preserve ALL content from the source plan. Do not remove any tasks or details.

5. Phase filenames should match the format: phase-N.md (e.g., phase-1.md, phase-2.md)

{previous_issues_section}

## Output Format
Output each file in this format:

---FILE: MASTER_PLAN.md---
[content]
---END FILE---

---FILE: phase-1.md---
[content]
---END FILE---

Generate the structured plan files now.
"""

REMEDIATION_SECTION = """
## IMPORTANT: Previous Attempt Failed Audit
The previous conversion attempt had these issues:
{issues}

You MUST fix these issues in this attempt. Pay special attention to:
- Ensuring all phase files referenced in the master plan exist
- Adding proper ## Gates section with validation commands
- Including notes output path in Process Wrapper
"""

# Questions for interactive mode
INTERACTIVE_QUESTIONS = {
    "phases": {
        "question": "How many phases should this plan have?",
        "options": ["2 phases", "3 phases", "4 phases", "5+ phases"],
    },
    "gates": {
        "question": "What validation tools should we use?",
        "options": ["Python (ruff, pyright, pytest)", "JavaScript (eslint, tsc)", "Custom"],
        "multi_select": True,
    },
    "notes": {
        "question": "Should phases write handoff notes?",
        "options": ["Yes (recommended)", "No"],
    },
}
