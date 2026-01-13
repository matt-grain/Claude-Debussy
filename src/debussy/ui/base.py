"""Base types and utilities for UI components."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class UIState(str, Enum):
    """Current state of the UI."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_INPUT = "waiting_input"


class UserAction(str, Enum):
    """Actions that can be triggered by user input."""

    NONE = "none"
    STATUS = "status"
    PAUSE = "pause"
    RESUME = "resume"
    TOGGLE_VERBOSE = "verbose"
    SKIP = "skip"
    QUIT = "quit"


@dataclass
class UIContext:
    """Current context for the UI display."""

    plan_name: str = ""
    current_phase: str = ""
    phase_title: str = ""
    total_phases: int = 0
    phase_index: int = 0
    state: UIState = UIState.IDLE
    start_time: float = field(default_factory=time.time)
    verbose: bool = True
    last_action: UserAction = UserAction.NONE
    # Token usage tracking (cumulative across all phases)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    # Current session tracking (resets per phase)
    session_input_tokens: int = 0
    session_output_tokens: int = 0
    context_window: int = 200_000  # Default Claude context window
    current_context_tokens: int = 0  # Current session's context usage


# Status display configuration
STATUS_MAP: dict[UIState, tuple[str, str]] = {
    UIState.IDLE: ("Idle", "dim"),
    UIState.RUNNING: ("Running", "green"),
    UIState.PAUSED: ("Paused", "yellow"),
    UIState.WAITING_INPUT: ("Waiting", "cyan"),
}


def format_duration(seconds: float) -> str:
    """Format duration in HH:MM:SS format."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
