# Debussy Convert Process

This document explains how `debussy convert` transforms freeform plans into Debussy's structured format.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEBUSSY CONVERT WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              INPUTS
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  Freeform Plan   │  │ MASTER_TEMPLATE  │  │  PHASE_GENERIC   │
    │  (user's plan)   │  │      .md         │  │      .md         │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUILD CONVERSION PROMPT                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  CONVERSION_PROMPT template filled with:                           │    │
│  │  • {source_content} = freeform plan text                          │    │
│  │  • {master_template} = MASTER_TEMPLATE.md content                 │    │
│  │  • {phase_template} = PHASE_GENERIC.md content                    │    │
│  │  • {previous_issues_section} = audit errors (if retry)            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLAUDE CLI CALL                                  │
│                                                                             │
│   subprocess.run(["claude", "--print", "-p", prompt, "--model", "haiku"])   │
│                                                                             │
│   • Spawns Claude CLI as subprocess (NOT a persistent instance)             │
│   • Uses --print flag for non-interactive output                           │
│   • Stateless: each call is independent                                    │
│   • Timeout: 120s default                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PARSE CLAUDE OUTPUT                                 │
│                                                                             │
│   Expected format:                                                          │
│   ┌──────────────────────────────────────────┐                             │
│   │ ---FILE: MASTER_PLAN.md---               │                             │
│   │ # Plan Title...                          │                             │
│   │ ---END FILE---                           │                             │
│   │                                          │                             │
│   │ ---FILE: phase-1.md---                   │                             │
│   │ # Phase 1...                             │                             │
│   │ ---END FILE---                           │                             │
│   └──────────────────────────────────────────┘                             │
│                                                                             │
│   Regex: r"---FILE:\s*(.+?)---\n(.*?)---END FILE---"                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WRITE FILES TO DISK                                │
│                                                                             │
│   output_dir/                                                               │
│   ├── MASTER_PLAN.md                                                        │
│   ├── phase-1.md                                                            │
│   ├── phase-2.md                                                            │
│   └── phase-3.md                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RUN AUDIT                                      │
│                                                                             │
│   auditor.audit(output_dir / "MASTER_PLAN.md")                             │
│                                                                             │
│   Checks:                                                                   │
│   • Master plan has ## Phases table                                        │
│   • Phase files exist and are parseable                                    │
│   • Each phase has ## Gates section                                        │
│   • Each phase has notes output path                                       │
│   • No circular dependencies                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
           ┌───────────────┐             ┌───────────────┐
           │ AUDIT PASSED  │             │ AUDIT FAILED  │
           └───────┬───────┘             └───────┬───────┘
                   │                             │
                   ▼                             ▼
           ┌───────────────┐             ┌───────────────────────┐
           │    SUCCESS    │             │  iteration < max?     │
           │               │             └───────────┬───────────┘
           │ Return:       │                   │           │
           │ • success=T   │                  YES          NO
           │ • files=[...] │                   │           │
           │ • audit_passed│                   ▼           ▼
           └───────────────┘             ┌───────────┐ ┌─────────┐
                                         │  RETRY    │ │  FAIL   │
                                         │           │ │         │
                                         │ Add audit │ │ Return: │
                                         │ issues to │ │ success │
                                         │ prompt    │ │ = False │
                                         └─────┬─────┘ └─────────┘
                                               │
                                               └──────► (back to BUILD PROMPT)
```

---

## Key Design Decisions

### Stateless Subprocess Model

The converter does **NOT** create a persistent Claude instance.

Each conversion attempt spawns a **NEW** subprocess:

```python
subprocess.run(["claude", "--print", "-p", prompt, "--model", "haiku"])
```

This means:
- No conversation history between iterations
- Each retry includes full context (templates + previous errors)
- Stateless design - can be parallelized easily
- Cost: one API call per iteration

### Audit-Driven Feedback Loop

The retry mechanism uses audit errors to guide Claude:

1. First attempt: Claude gets source + templates
2. If audit fails: errors are formatted and added to prompt
3. Next attempt: Claude sees what went wrong and can fix it

```python
# REMEDIATION_SECTION added to prompt on retry
"""
## IMPORTANT: Previous Attempt Failed Audit
The previous conversion attempt had these issues:
- [error] MISSING_GATES: Phase 1 has no gates defined
- [error] NO_NOTES_OUTPUT: Phase 2 has no notes output path

You MUST fix these issues in this attempt.
"""
```

---

## File Output Format

Claude must output files in this specific format for parsing:

```
---FILE: MASTER_PLAN.md---
# Feature Name - Master Plan

**Created:** 2024-01-15
...content...
---END FILE---

---FILE: phase-1.md---
# Phase 1: Setup

**Status:** Pending
...content...
---END FILE---
```

The parser uses regex to extract files:
```python
pattern = r"---FILE:\s*(.+?)---\n(.*?)---END FILE---"
```

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_iterations` | 3 | Maximum retry attempts |
| `model` | haiku | Claude model (haiku for cost efficiency) |
| `timeout` | 120s | Subprocess timeout per attempt |

---

## Related Files

- [plan_converter.py](../src/debussy/converters/plan_converter.py) - Main converter implementation
- [prompts.py](../src/debussy/converters/prompts.py) - Conversion prompt templates
- [CONVERT_TESTS.md](CONVERT_TESTS.md) - Test strategy documentation
- [MASTER_TEMPLATE.md](templates/plans/MASTER_TEMPLATE.md) - Master plan template
- [PHASE_GENERIC.md](templates/plans/PHASE_GENERIC.md) - Phase file template
