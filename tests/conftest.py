"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_master_plan(fixtures_dir: Path) -> Path:
    """Return the path to the sample master plan."""
    return fixtures_dir / "sample_master.md"


@pytest.fixture
def sample_phase(fixtures_dir: Path) -> Path:
    """Return the path to the sample phase file."""
    return fixtures_dir / "sample_phase.md"


@pytest.fixture
def sample_phase2(fixtures_dir: Path) -> Path:
    """Return the path to the sample phase 2 file."""
    return fixtures_dir / "sample_phase2.md"


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir: Path) -> Path:
    """Return the path for a temporary test database."""
    return temp_dir / "test_state.db"


@pytest.fixture
def temp_master_plan(temp_dir: Path) -> Path:
    """Create a temporary master plan for testing."""
    plan_content = """\
# Test Plan - Master

**Created:** 2026-01-12
**Status:** Draft

---

## Overview

Test plan for unit tests.

## Phases

| Phase | Title | Focus | Risk | Status |
|-------|-------|-------|------|--------|
| 1 | [Phase One](phase1.md) | Setup | Low | Pending |
| 2 | [Phase Two](phase2.md) | Logic | Medium | Pending |
"""
    plan_path = temp_dir / "test-master.md"
    plan_path.write_text(plan_content)

    # Create phase files
    phase1_content = """\
# Test Phase 1

**Status:** Pending
**Master Plan:** [test-master.md](test-master.md)
**Depends On:** N/A

---

## Process Wrapper (MANDATORY)
- [ ] **AGENT:test-agent** - do something
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_1.md`

## Gates
- echo: must pass

---

## Tasks

### 1. Task Group
- [ ] 1.1: First task
- [ ] 1.2: Second task
"""
    (temp_dir / "phase1.md").write_text(phase1_content)

    phase2_content = """\
# Test Phase 2

**Status:** Pending
**Master Plan:** [test-master.md](test-master.md)
**Depends On:** [Phase 1](phase1.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_phase_1.md`
- [ ] **[IMPLEMENTATION]**
- [ ] Write notes to: `notes/NOTES_phase_2.md`

## Gates
- ruff: 0 errors

---

## Tasks

### 1. Implementation
- [ ] 1.1: Implement feature
"""
    (temp_dir / "phase2.md").write_text(phase2_content)

    return plan_path
