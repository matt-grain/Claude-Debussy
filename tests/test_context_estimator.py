"""Tests for the ContextEstimator module."""

from __future__ import annotations

from debussy.runners.context_estimator import (
    CHARS_TO_TOKENS_RATIO,
    DEFAULT_CONTEXT_LIMIT,
    DEFAULT_THRESHOLD_PERCENT,
    DEFAULT_TOOL_CALL_THRESHOLD,
    REASONING_OVERHEAD,
    ContextEstimate,
    ContextEstimator,
)


class TestContextEstimateDataclass:
    """Tests for ContextEstimate dataclass."""

    def test_default_values(self) -> None:
        """ContextEstimate initializes with zero values."""
        estimate = ContextEstimate()
        assert estimate.file_tokens == 0
        assert estimate.tool_output_tokens == 0
        assert estimate.prompt_tokens == 0
        assert estimate.tool_call_count == 0

    def test_total_estimated_with_zeros(self) -> None:
        """total_estimated returns 0 when all values are zero."""
        estimate = ContextEstimate()
        assert estimate.total_estimated == 0

    def test_total_estimated_calculation(self) -> None:
        """total_estimated applies reasoning overhead multiplier."""
        estimate = ContextEstimate(
            file_tokens=1000,
            tool_output_tokens=500,
            prompt_tokens=200,
        )
        # 1000 + 500 + 200 = 1700 base, 1700 * 1.3 = 2210 with overhead
        expected = int(1700 * REASONING_OVERHEAD)
        assert estimate.total_estimated == expected

    def test_total_estimated_ignores_tool_call_count(self) -> None:
        """total_estimated doesn't include tool_call_count in calculation."""
        estimate = ContextEstimate(
            file_tokens=100,
            tool_output_tokens=100,
            prompt_tokens=100,
            tool_call_count=999,
        )
        # tool_call_count should not affect total
        expected = int(300 * REASONING_OVERHEAD)
        assert estimate.total_estimated == expected

    def test_usage_percentage_zero(self) -> None:
        """usage_percentage returns 0 when total is zero."""
        estimate = ContextEstimate()
        assert estimate.usage_percentage == 0.0

    def test_usage_percentage_calculation(self) -> None:
        """usage_percentage calculates correctly relative to 200k limit."""
        # Create estimate that equals 100k tokens after overhead
        # 100k / 200k = 50%
        base_tokens = int(100_000 / REASONING_OVERHEAD)
        estimate = ContextEstimate(file_tokens=base_tokens)
        assert abs(estimate.usage_percentage - 50.0) < 0.1

    def test_usage_percentage_can_exceed_100(self) -> None:
        """usage_percentage can exceed 100% if context is overfull."""
        # Create estimate that equals 400k tokens after overhead
        # 400k / 200k = 200%
        base_tokens = int(400_000 / REASONING_OVERHEAD)
        estimate = ContextEstimate(file_tokens=base_tokens)
        assert estimate.usage_percentage > 100.0


class TestContextEstimatorInit:
    """Tests for ContextEstimator initialization."""

    def test_default_configuration(self) -> None:
        """ContextEstimator uses default values when not specified."""
        estimator = ContextEstimator()
        assert estimator.threshold_percent == DEFAULT_THRESHOLD_PERCENT
        assert estimator.context_limit == DEFAULT_CONTEXT_LIMIT
        assert estimator.tool_call_threshold == DEFAULT_TOOL_CALL_THRESHOLD

    def test_custom_configuration(self) -> None:
        """ContextEstimator accepts custom configuration."""
        estimator = ContextEstimator(
            threshold_percent=90,
            context_limit=100_000,
            tool_call_threshold=50,
        )
        assert estimator.threshold_percent == 90
        assert estimator.context_limit == 100_000
        assert estimator.tool_call_threshold == 50

    def test_initial_estimate_is_zero(self) -> None:
        """ContextEstimator starts with zero estimate."""
        estimator = ContextEstimator()
        estimate = estimator.get_estimate()
        assert estimate.file_tokens == 0
        assert estimate.tool_output_tokens == 0
        assert estimate.prompt_tokens == 0
        assert estimate.tool_call_count == 0


class TestContextEstimatorAddFileRead:
    """Tests for ContextEstimator.add_file_read() method."""

    def test_adds_tokens_from_file_content(self) -> None:
        """add_file_read() adds estimated tokens from file content."""
        estimator = ContextEstimator()
        content = "x" * 400  # 400 chars = 100 tokens (4:1 ratio)
        estimator.add_file_read(content)

        estimate = estimator.get_estimate()
        assert estimate.file_tokens == 100

    def test_accumulates_multiple_reads(self) -> None:
        """add_file_read() accumulates tokens from multiple reads."""
        estimator = ContextEstimator()
        estimator.add_file_read("x" * 400)  # 100 tokens
        estimator.add_file_read("y" * 800)  # 200 tokens

        estimate = estimator.get_estimate()
        assert estimate.file_tokens == 300

    def test_does_not_increment_tool_call_count(self) -> None:
        """add_file_read() does not increment tool call count."""
        estimator = ContextEstimator()
        estimator.add_file_read("content")

        estimate = estimator.get_estimate()
        assert estimate.tool_call_count == 0


class TestContextEstimatorAddToolOutput:
    """Tests for ContextEstimator.add_tool_output() method."""

    def test_adds_tokens_from_tool_output(self) -> None:
        """add_tool_output() adds estimated tokens from tool output."""
        estimator = ContextEstimator()
        content = "x" * 400  # 400 chars = 100 tokens
        estimator.add_tool_output(content)

        estimate = estimator.get_estimate()
        assert estimate.tool_output_tokens == 100

    def test_increments_tool_call_count(self) -> None:
        """add_tool_output() increments tool call count."""
        estimator = ContextEstimator()
        estimator.add_tool_output("output 1")
        estimator.add_tool_output("output 2")
        estimator.add_tool_output("output 3")

        estimate = estimator.get_estimate()
        assert estimate.tool_call_count == 3

    def test_accumulates_multiple_outputs(self) -> None:
        """add_tool_output() accumulates tokens from multiple outputs."""
        estimator = ContextEstimator()
        estimator.add_tool_output("x" * 400)  # 100 tokens
        estimator.add_tool_output("y" * 400)  # 100 tokens

        estimate = estimator.get_estimate()
        assert estimate.tool_output_tokens == 200


class TestContextEstimatorAddPrompt:
    """Tests for ContextEstimator.add_prompt() method."""

    def test_adds_tokens_from_prompt(self) -> None:
        """add_prompt() adds estimated tokens from prompt content."""
        estimator = ContextEstimator()
        prompt = "x" * 400  # 400 chars = 100 tokens
        estimator.add_prompt(prompt)

        estimate = estimator.get_estimate()
        assert estimate.prompt_tokens == 100

    def test_accumulates_multiple_prompts(self) -> None:
        """add_prompt() accumulates tokens from multiple prompts."""
        estimator = ContextEstimator()
        estimator.add_prompt("x" * 400)  # 100 tokens
        estimator.add_prompt("y" * 800)  # 200 tokens

        estimate = estimator.get_estimate()
        assert estimate.prompt_tokens == 300

    def test_does_not_increment_tool_call_count(self) -> None:
        """add_prompt() does not increment tool call count."""
        estimator = ContextEstimator()
        estimator.add_prompt("prompt content")

        estimate = estimator.get_estimate()
        assert estimate.tool_call_count == 0


class TestContextEstimatorShouldRestart:
    """Tests for ContextEstimator.should_restart() threshold detection."""

    def test_returns_false_when_below_threshold(self) -> None:
        """should_restart() returns False when usage is below threshold."""
        estimator = ContextEstimator(threshold_percent=80)
        # Add content that puts us at ~50% usage
        # 50% of 200k = 100k tokens, divide by 1.3 overhead = ~77k base tokens
        # 77k tokens * 4 chars = 308k chars
        estimator.add_file_read("x" * 100_000)  # ~25k tokens

        assert not estimator.should_restart()

    def test_returns_true_at_threshold(self) -> None:
        """should_restart() returns True when usage reaches threshold."""
        estimator = ContextEstimator(threshold_percent=80, context_limit=200_000)
        # Need to reach 80% of 200k = 160k tokens after overhead
        # 160k / 1.3 = ~123k base tokens
        # 123k tokens * 4 chars = ~492k chars
        estimator.add_file_read("x" * 500_000)

        assert estimator.should_restart()

    def test_returns_true_above_threshold(self) -> None:
        """should_restart() returns True when usage exceeds threshold."""
        estimator = ContextEstimator(threshold_percent=80)
        # Add lots of content to exceed threshold
        estimator.add_file_read("x" * 1_000_000)

        assert estimator.should_restart()

    def test_fallback_triggers_on_tool_count(self) -> None:
        """should_restart() triggers on tool call count even with low tokens."""
        estimator = ContextEstimator(tool_call_threshold=100)

        # Add 100 tool outputs with minimal content
        for _ in range(100):
            estimator.add_tool_output("x")

        assert estimator.should_restart()

    def test_fallback_does_not_trigger_below_count(self) -> None:
        """should_restart() doesn't trigger on tool count below threshold."""
        estimator = ContextEstimator(tool_call_threshold=100)

        # Add 99 tool outputs
        for _ in range(99):
            estimator.add_tool_output("x")

        assert not estimator.should_restart()

    def test_primary_check_takes_precedence(self) -> None:
        """should_restart() triggers on token threshold regardless of tool count."""
        estimator = ContextEstimator(threshold_percent=80, tool_call_threshold=1000)
        # High tool call threshold, but exceed token threshold
        estimator.add_file_read("x" * 1_000_000)

        assert estimator.should_restart()


class TestContextEstimatorReset:
    """Tests for ContextEstimator.reset() method."""

    def test_reset_clears_all_counters(self) -> None:
        """reset() clears all token counters to zero."""
        estimator = ContextEstimator()
        estimator.add_file_read("x" * 1000)
        estimator.add_tool_output("y" * 1000)
        estimator.add_prompt("z" * 1000)

        estimator.reset()
        estimate = estimator.get_estimate()

        assert estimate.file_tokens == 0
        assert estimate.tool_output_tokens == 0
        assert estimate.prompt_tokens == 0
        assert estimate.tool_call_count == 0

    def test_reset_allows_fresh_tracking(self) -> None:
        """reset() allows fresh tracking after reset."""
        estimator = ContextEstimator()
        estimator.add_file_read("x" * 400)
        estimator.reset()
        estimator.add_file_read("y" * 800)

        estimate = estimator.get_estimate()
        assert estimate.file_tokens == 200  # Only second read

    def test_reset_resets_should_restart_state(self) -> None:
        """reset() resets state so should_restart() returns False."""
        estimator = ContextEstimator(threshold_percent=80)
        # Exceed threshold
        estimator.add_file_read("x" * 1_000_000)
        assert estimator.should_restart()

        # Reset and verify threshold is no longer exceeded
        estimator.reset()
        assert not estimator.should_restart()


class TestContextEstimatorGetEstimate:
    """Tests for ContextEstimator.get_estimate() method."""

    def test_returns_copy_of_estimate(self) -> None:
        """get_estimate() returns a copy, not the internal reference."""
        estimator = ContextEstimator()
        estimator.add_file_read("x" * 400)

        estimate1 = estimator.get_estimate()
        estimator.add_file_read("y" * 400)
        estimate2 = estimator.get_estimate()

        # First estimate should not have been modified
        assert estimate1.file_tokens == 100
        assert estimate2.file_tokens == 200


class TestContextEstimatorEstimateTokens:
    """Tests for ContextEstimator._estimate_tokens() static method."""

    def test_uses_chars_to_tokens_ratio(self) -> None:
        """_estimate_tokens() uses 4:1 char to token ratio."""
        # 400 chars / 4 = 100 tokens
        result = ContextEstimator._estimate_tokens("x" * 400)
        assert result == 100

    def test_returns_minimum_of_one(self) -> None:
        """_estimate_tokens() returns minimum of 1 token."""
        result = ContextEstimator._estimate_tokens("")
        assert result == 1

        result = ContextEstimator._estimate_tokens("x")
        assert result == 1

        result = ContextEstimator._estimate_tokens("xx")
        assert result == 1

    def test_truncates_to_integer(self) -> None:
        """_estimate_tokens() truncates fractional tokens."""
        # 5 chars / 4 = 1.25 -> 1 token
        result = ContextEstimator._estimate_tokens("xxxxx")
        assert result == 1

        # 7 chars / 4 = 1.75 -> 1 token
        result = ContextEstimator._estimate_tokens("xxxxxxx")
        assert result == 1


class TestContextEstimatorConstants:
    """Tests for module constants."""

    def test_default_context_limit(self) -> None:
        """DEFAULT_CONTEXT_LIMIT is 200k for Claude's context window."""
        assert DEFAULT_CONTEXT_LIMIT == 200_000

    def test_chars_to_tokens_ratio(self) -> None:
        """CHARS_TO_TOKENS_RATIO is 4 (conservative estimate)."""
        assert CHARS_TO_TOKENS_RATIO == 4

    def test_reasoning_overhead(self) -> None:
        """REASONING_OVERHEAD is 1.3 (30% overhead)."""
        assert REASONING_OVERHEAD == 1.3

    def test_default_threshold_percent(self) -> None:
        """DEFAULT_THRESHOLD_PERCENT is 80%."""
        assert DEFAULT_THRESHOLD_PERCENT == 80

    def test_default_tool_call_threshold(self) -> None:
        """DEFAULT_TOOL_CALL_THRESHOLD is 100 calls."""
        assert DEFAULT_TOOL_CALL_THRESHOLD == 100


class TestContextEstimatorIntegration:
    """Integration tests for ContextEstimator."""

    def test_realistic_session_tracking(self) -> None:
        """Simulate realistic session with mixed operations."""
        estimator = ContextEstimator()

        # Initial prompt
        estimator.add_prompt("Implement feature X with tests" * 100)

        # Read some files
        estimator.add_file_read("def function():\n    pass\n" * 100)
        estimator.add_file_read("class MyClass:\n    def method(self):\n        pass\n" * 50)

        # Tool outputs (grep, glob results)
        estimator.add_tool_output("src/main.py:10: match\nsrc/test.py:20: match\n")
        estimator.add_tool_output("/path/to/file1.py\n/path/to/file2.py\n")

        estimate = estimator.get_estimate()

        # Verify all categories are tracked
        assert estimate.prompt_tokens > 0
        assert estimate.file_tokens > 0
        assert estimate.tool_output_tokens > 0
        assert estimate.tool_call_count == 2
        assert estimate.total_estimated > 0
        assert estimate.usage_percentage > 0

    def test_threshold_detection_with_mixed_inputs(self) -> None:
        """Verify threshold detection with mixed input types."""
        estimator = ContextEstimator(threshold_percent=50)

        # Add content from various sources to reach ~50% of 200k
        # 50% of 200k = 100k tokens after overhead
        # 100k / 1.3 = ~77k base tokens = ~308k chars
        estimator.add_prompt("x" * 100_000)
        estimator.add_file_read("y" * 100_000)
        estimator.add_tool_output("z" * 110_000)

        assert estimator.should_restart()
