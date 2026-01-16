"""Tests for the issue status fetcher."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from debussy.core.models import IssueStatus
from debussy.sync.status_fetcher import (
    DEFAULT_CACHE_TTL,
    CacheEntry,
    IssueStatusFetcher,
    StatusCache,
)


class TestStatusCache:
    """Tests for StatusCache."""

    def test_cache_key_creation(self) -> None:
        """Test cache key is unique per platform and issue."""
        cache = StatusCache()
        key1 = cache._make_key("github", "10")
        key2 = cache._make_key("jira", "10")
        key3 = cache._make_key("github", "20")

        assert key1 == "github:10"
        assert key2 == "jira:10"
        assert key3 == "github:20"
        assert key1 != key2
        assert key1 != key3

    def test_cache_set_and_get(self) -> None:
        """Test setting and getting cached values."""
        cache = StatusCache()
        status = IssueStatus(
            id="10",
            platform="github",
            state="open",
            labels=["bug"],
            milestone="v1.0",
        )

        cache.set(status)
        retrieved = cache.get("github", "10")

        assert retrieved is not None
        assert retrieved.id == "10"
        assert retrieved.platform == "github"
        assert retrieved.state == "open"

    def test_cache_miss_returns_none(self) -> None:
        """Test that cache miss returns None."""
        cache = StatusCache()
        result = cache.get("github", "999")
        assert result is None

    def test_cache_expiration(self) -> None:
        """Test that expired entries return None."""
        from datetime import datetime

        cache = StatusCache(ttl=timedelta(seconds=1))
        status = IssueStatus(id="10", platform="github", state="open")
        cache.set(status)

        # Manually expire the entry
        key = cache._make_key("github", "10")
        cache._cache[key] = CacheEntry(
            status=status,
            fetched_at=datetime.now() - timedelta(seconds=10),
        )

        result = cache.get("github", "10")
        assert result is None

    def test_cache_clear(self) -> None:
        """Test clearing the cache."""
        cache = StatusCache()
        cache.set(IssueStatus(id="10", platform="github", state="open"))
        cache.set(IssueStatus(id="20", platform="github", state="closed"))

        cache.clear()

        assert cache.get("github", "10") is None
        assert cache.get("github", "20") is None

    def test_cache_invalidate_single_entry(self) -> None:
        """Test invalidating a specific entry."""
        cache = StatusCache()
        cache.set(IssueStatus(id="10", platform="github", state="open"))
        cache.set(IssueStatus(id="20", platform="github", state="closed"))

        cache.invalidate("github", "10")

        assert cache.get("github", "10") is None
        assert cache.get("github", "20") is not None

    def test_default_cache_ttl(self) -> None:
        """Test default cache TTL is 5 minutes."""
        assert timedelta(minutes=5) == DEFAULT_CACHE_TTL

    def test_freshness_seconds(self) -> None:
        """Test freshness calculation."""
        cache = StatusCache()
        cache.set(IssueStatus(id="10", platform="github", state="open"))

        freshness = cache.freshness_seconds
        assert "github:10" in freshness
        assert freshness["github:10"] >= 0
        assert freshness["github:10"] < 1  # Should be very fresh


class TestIssueStatusFetcher:
    """Tests for IssueStatusFetcher."""

    @pytest.mark.asyncio
    async def test_fetcher_init_without_credentials(self) -> None:
        """Test fetcher can be created without credentials."""
        fetcher = IssueStatusFetcher()
        assert fetcher.github_repo is None
        assert fetcher.jira_url is None

    @pytest.mark.asyncio
    async def test_fetcher_github_client_initialization(self) -> None:
        """Test GitHub client initializes when repo is provided."""
        with patch("debussy.sync.status_fetcher.GitHubClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance

            fetcher = IssueStatusFetcher(
                github_repo="owner/repo",
                github_token="test-token",
            )

            async with fetcher:
                mock_client.assert_called_once()
                mock_instance.__aenter__.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetcher_skips_github_without_repo(self) -> None:
        """Test fetcher skips GitHub when no repo configured."""
        fetcher = IssueStatusFetcher()

        async with fetcher:
            result = await fetcher.fetch_github_status(["10", "11"])

        assert result == {}

    @pytest.mark.asyncio
    async def test_fetcher_uses_cache(self) -> None:
        """Test fetcher returns cached values when available."""
        with patch("debussy.sync.status_fetcher.GitHubClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance

            fetcher = IssueStatusFetcher(
                github_repo="owner/repo",
                github_token="test-token",
            )
            cached_status = IssueStatus(id="10", platform="github", state="open")
            fetcher._cache.set(cached_status)

            async with fetcher:
                result = await fetcher.fetch_github_status(["10"], use_cache=True)

            assert "10" in result
            assert result["10"].state == "open"
            # Should NOT have called get_issue since cache was used
            mock_instance.get_issue.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetcher_bypasses_cache_on_request(self) -> None:
        """Test fetcher fetches fresh when use_cache=False."""
        with patch("debussy.sync.status_fetcher.GitHubClient") as mock_client:
            mock_instance = AsyncMock()
            mock_gh_issue = MagicMock()
            mock_gh_issue.number = 10
            mock_gh_issue.state = "closed"
            mock_gh_issue.labels = []
            mock_gh_issue.milestone_title = None
            mock_instance.get_issue.return_value = mock_gh_issue
            mock_client.return_value = mock_instance

            fetcher = IssueStatusFetcher(
                github_repo="owner/repo",
                github_token="test-token",
            )
            # Pre-populate cache with different state
            fetcher._cache.set(IssueStatus(id="10", platform="github", state="open"))

            async with fetcher:
                result = await fetcher.fetch_github_status(["10"], use_cache=False)

            assert result["10"].state == "closed"  # Fresh value, not cached

    @pytest.mark.asyncio
    async def test_fetch_all_parallel(self) -> None:
        """Test fetch_all fetches from both platforms in parallel."""
        with (
            patch("debussy.sync.status_fetcher.GitHubClient") as mock_gh,
            patch("debussy.sync.status_fetcher.JiraClient") as mock_jira,
        ):
            mock_gh_instance = AsyncMock()
            mock_gh.return_value = mock_gh_instance
            mock_jira_instance = AsyncMock()
            mock_jira.return_value = mock_jira_instance

            fetcher = IssueStatusFetcher(
                github_repo="owner/repo",
                github_token="test-token",
                jira_url="https://test.atlassian.net",
                jira_email="test@test.com",
                jira_token="jira-token",
            )

            # Pre-populate cache
            fetcher._cache.set(IssueStatus(id="10", platform="github", state="open"))
            fetcher._cache.set(IssueStatus(id="PROJ-123", platform="jira", state="In Progress"))

            async with fetcher:
                result = await fetcher.fetch_all(
                    github_issues=["10"],
                    jira_issues=["PROJ-123"],
                    use_cache=True,
                )

            assert "GH-10" in result  # GitHub issues prefixed
            assert "PROJ-123" in result  # Jira keys unchanged

    @pytest.mark.asyncio
    async def test_clear_cache(self) -> None:
        """Test clearing the cache."""
        fetcher = IssueStatusFetcher()
        fetcher._cache.set(IssueStatus(id="10", platform="github", state="open"))

        fetcher.clear_cache()

        assert fetcher._cache.get("github", "10") is None

    @pytest.mark.asyncio
    async def test_fetcher_handles_api_error(self) -> None:
        """Test fetcher gracefully handles API errors."""
        from debussy.sync.github_client import GitHubNotFoundError

        with patch("debussy.sync.status_fetcher.GitHubClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get_issue.side_effect = GitHubNotFoundError("Not found")
            mock_client.return_value = mock_instance

            fetcher = IssueStatusFetcher(
                github_repo="owner/repo",
                github_token="test-token",
            )

            async with fetcher:
                result = await fetcher.fetch_github_status(["999"])

            # Should return empty dict, not raise
            assert result == {}
