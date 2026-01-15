"""Context usage estimator for Claude sessions.

Provides token counting and threshold detection without relying on
broken stream-json cumulative tokens. Uses observable signals:
- File content reads from Read tool
- Tool output sizes
- Prompt sizes
- Tool call count as fallback heuristic
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONTEXT_LIMIT = 200_000
CHARS_TO_TOKENS_RATIO = 4
REASONING_OVERHEAD = 1.3
DEFAULT_THRESHOLD_PERCENT = 80
DEFAULT_TOOL_CALL_THRESHOLD = 100


@dataclass
class ContextEstimate:
    """Container for estimated context usage at a point in time."""

    file_tokens: int = 0
    tool_output_tokens: int = 0
    prompt_tokens: int = 0
    tool_call_count: int = 0

    @property
    def total_estimated(self) -> int:
        """Total estimated tokens including reasoning overhead.

        Multiplies sum by REASONING_OVERHEAD (1.3) to account for Claude's
        internal token usage during tool formatting and chain-of-thought.
        """
        base = self.file_tokens + self.tool_output_tokens + self.prompt_tokens
        return int(base * REASONING_OVERHEAD)

    @property
    def usage_percentage(self) -> float:
        """Estimated context usage as percentage of 200k window (0-100+)."""
        return (self.total_estimated / DEFAULT_CONTEXT_LIMIT) * 100


class ContextEstimator:
    """Tracks estimated context usage during a Claude session.

    Monitors observable signals (file reads, tool outputs, prompts, tool calls)
    to estimate when context is approaching limits. Provides both primary
    (token-based) and fallback (tool-count) threshold detection.

    Configuration:
        threshold_percent: Percentage of context limit to trigger restart (default 80%)
        context_limit: Maximum context tokens (default 200k)
        tool_call_threshold: Tool call count for fallback heuristic (default 100)
    """

    def __init__(
        self,
        threshold_percent: int = DEFAULT_THRESHOLD_PERCENT,
        context_limit: int = DEFAULT_CONTEXT_LIMIT,
        tool_call_threshold: int = DEFAULT_TOOL_CALL_THRESHOLD,
    ) -> None:
        """Initialize the context estimator.

        Args:
            threshold_percent: Percentage of context to trigger restart (0-100)
            context_limit: Maximum context window size (tokens)
            tool_call_threshold: Tool call count for fallback heuristic
        """
        self.threshold_percent = threshold_percent
        self.context_limit = context_limit
        self.tool_call_threshold = tool_call_threshold

        self._estimate = ContextEstimate()

    def add_file_read(self, content: str) -> None:
        """Track tokens from a Read tool result.

        Args:
            content: The file content that was read
        """
        tokens = self._estimate_tokens(content)
        self._estimate.file_tokens += tokens
        logger.debug(f"Context: added file read ({tokens} tokens), total: {self._estimate.total_estimated}/{self.context_limit}")

    def add_tool_output(self, content: str) -> None:
        """Track tokens from tool output (non-Read tools).

        Args:
            content: The tool output/result content
        """
        tokens = self._estimate_tokens(content)
        self._estimate.tool_output_tokens += tokens
        self._estimate.tool_call_count += 1
        logger.debug(f"Context: added tool output ({tokens} tokens, call #{self._estimate.tool_call_count}), total: {self._estimate.total_estimated}/{self.context_limit}")

    def add_prompt(self, content: str) -> None:
        """Track tokens from an injected prompt.

        Args:
            content: The prompt text that was sent to Claude
        """
        tokens = self._estimate_tokens(content)
        self._estimate.prompt_tokens += tokens
        logger.debug(f"Context: added prompt ({tokens} tokens), total: {self._estimate.total_estimated}/{self.context_limit}")

    def should_restart(self) -> bool:
        """Check if context usage exceeds threshold (primary or fallback).

        Uses two checks:
        1. Primary: token percentage >= threshold_percent
        2. Fallback: tool call count >= tool_call_threshold

        Returns True if either check triggers.

        Returns:
            True if restart is recommended
        """
        # Primary check: token-based threshold
        usage_pct = self._estimate.usage_percentage
        if usage_pct >= self.threshold_percent:
            logger.warning(f"Context threshold exceeded: {usage_pct:.1f}% ({self._estimate.total_estimated}/{self.context_limit} tokens)")
            return True

        # Fallback check: tool call count
        if self._estimate.tool_call_count >= self.tool_call_threshold:
            logger.warning(f"Tool call fallback threshold exceeded: {self._estimate.tool_call_count} calls (threshold: {self.tool_call_threshold})")
            return True

        return False

    def get_estimate(self) -> ContextEstimate:
        """Get current context estimate.

        Returns:
            Current ContextEstimate snapshot
        """
        return ContextEstimate(
            file_tokens=self._estimate.file_tokens,
            tool_output_tokens=self._estimate.tool_output_tokens,
            prompt_tokens=self._estimate.prompt_tokens,
            tool_call_count=self._estimate.tool_call_count,
        )

    def reset(self) -> None:
        """Reset all counters to zero for fresh session.

        Call this when starting a new Claude session to clear previous
        context tracking.
        """
        self._estimate = ContextEstimate()
        logger.debug("Context estimator reset")

    @staticmethod
    def _estimate_tokens(content: str) -> int:
        """Estimate token count from string content.

        Uses simple character-to-token ratio (1 token ≈ 4 characters).
        Conservative estimate to avoid over-counting.

        Args:
            content: String content to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(content) // CHARS_TO_TOKENS_RATIO)
