"""Issue status fetching with caching for GitHub and Jira.

This module provides status fetching from external issue trackers with
a TTL-based caching layer to reduce API calls.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from debussy.core.models import IssueStatus
from debussy.sync.github_client import (
    GitHubClient,
    GitHubClientError,
    GitHubNotFoundError,
)
from debussy.sync.jira_client import (
    JiraClient,
    JiraClientError,
    JiraNotFoundError,
)

logger = logging.getLogger(__name__)

# Default cache TTL: 5 minutes
DEFAULT_CACHE_TTL = timedelta(minutes=5)


@dataclass
class CacheEntry:
    """A cached issue status with timestamp."""

    status: IssueStatus
    fetched_at: datetime


@dataclass
class StatusCache:
    """TTL-based cache for issue statuses."""

    ttl: timedelta = DEFAULT_CACHE_TTL
    _cache: dict[str, CacheEntry] = field(default_factory=dict)

    def _make_key(self, platform: str, issue_id: str) -> str:
        """Create a unique cache key."""
        return f"{platform}:{issue_id}"

    def get(self, platform: str, issue_id: str) -> IssueStatus | None:
        """Get a cached status if not expired."""
        key = self._make_key(platform, issue_id)
        entry = self._cache.get(key)

        if entry is None:
            return None

        # Check if expired
        if datetime.now() - entry.fetched_at > self.ttl:
            del self._cache[key]
            return None

        return entry.status

    def set(self, status: IssueStatus) -> None:
        """Cache an issue status."""
        key = self._make_key(status.platform, status.id)
        self._cache[key] = CacheEntry(status=status, fetched_at=datetime.now())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def invalidate(self, platform: str, issue_id: str) -> None:
        """Invalidate a specific cache entry."""
        key = self._make_key(platform, issue_id)
        self._cache.pop(key, None)

    @property
    def freshness_seconds(self) -> dict[str, float]:
        """Get freshness of cached entries in seconds."""
        now = datetime.now()
        return {key: (now - entry.fetched_at).total_seconds() for key, entry in self._cache.items()}


class IssueStatusFetcher:
    """Fetches current issue status from GitHub and Jira APIs with caching.

    This class provides a unified interface for fetching issue status from
    both platforms with automatic caching to reduce API calls.

    Usage:
        async with IssueStatusFetcher(github_repo="owner/repo") as fetcher:
            status = await fetcher.fetch_github_status(["10", "11"])
    """

    def __init__(
        self,
        github_repo: str | None = None,
        github_token: str | None = None,
        jira_url: str | None = None,
        jira_email: str | None = None,
        jira_token: str | None = None,
        cache_ttl: timedelta = DEFAULT_CACHE_TTL,
    ) -> None:
        """Initialize the status fetcher.

        Args:
            github_repo: Repository in 'owner/repo' format.
            github_token: GitHub token (or uses GITHUB_TOKEN env var).
            jira_url: Jira instance URL (e.g., https://company.atlassian.net).
            jira_email: Jira user email (or uses JIRA_EMAIL env var).
            jira_token: Jira API token (or uses JIRA_API_TOKEN env var).
            cache_ttl: Time-to-live for cached statuses.
        """
        self.github_repo = github_repo
        self._github_token = github_token
        self.jira_url = jira_url
        self._jira_email = jira_email
        self._jira_token = jira_token
        self._cache = StatusCache(ttl=cache_ttl)
        self._github_client: GitHubClient | None = None
        self._jira_client: JiraClient | None = None

    async def __aenter__(self) -> IssueStatusFetcher:
        """Enter async context manager."""
        # Initialize clients lazily - only if credentials are available
        if self.github_repo:
            try:
                self._github_client = GitHubClient(
                    repo=self.github_repo,
                    token=self._github_token,
                )
                await self._github_client.__aenter__()
            except GitHubClientError as e:
                logger.warning(f"GitHub client initialization failed: {e}")
                self._github_client = None

        if self.jira_url:
            try:
                self._jira_client = JiraClient(
                    base_url=self.jira_url,
                    email=self._jira_email,
                    token=self._jira_token,
                )
                await self._jira_client.__aenter__()
            except JiraClientError as e:
                logger.warning(f"Jira client initialization failed: {e}")
                self._jira_client = None

        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit async context manager."""
        if self._github_client:
            await self._github_client.__aexit__(exc_type, exc_val, exc_tb)
            self._github_client = None
        if self._jira_client:
            await self._jira_client.__aexit__(exc_type, exc_val, exc_tb)
            self._jira_client = None

    @property
    def cache(self) -> StatusCache:
        """Get the status cache."""
        return self._cache

    def clear_cache(self) -> None:
        """Clear the status cache."""
        self._cache.clear()

    # =========================================================================
    # GitHub Status Fetching
    # =========================================================================

    async def fetch_github_status(
        self,
        issue_ids: list[str],
        use_cache: bool = True,
    ) -> dict[str, IssueStatus]:
        """Fetch current status for GitHub issues.

        Args:
            issue_ids: List of issue numbers as strings.
            use_cache: Whether to use cached results if available.

        Returns:
            Dict mapping issue ID to IssueStatus.
        """
        if not self._github_client:
            logger.warning("GitHub client not initialized, skipping GitHub status fetch")
            return {}

        results: dict[str, IssueStatus] = {}
        to_fetch: list[str] = []

        # Check cache first
        for issue_id in issue_ids:
            if use_cache:
                cached = self._cache.get("github", issue_id)
                if cached:
                    results[issue_id] = cached
                    continue
            to_fetch.append(issue_id)

        # Fetch uncached issues
        if to_fetch:
            fetch_tasks = [self._fetch_single_github_issue(issue_id) for issue_id in to_fetch]
            fetched = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            for issue_id, result in zip(to_fetch, fetched, strict=True):
                if isinstance(result, BaseException):
                    logger.warning(f"Failed to fetch GitHub issue #{issue_id}: {result}")
                    continue
                if result is not None:
                    results[issue_id] = result
                    self._cache.set(result)

        return results

    async def _fetch_single_github_issue(self, issue_id: str) -> IssueStatus | None:
        """Fetch status for a single GitHub issue."""
        if not self._github_client:
            return None

        try:
            issue = await self._github_client.get_issue(int(issue_id))
            return IssueStatus(
                id=str(issue.number),
                platform="github",
                state=issue.state,
                labels=issue.labels,
                milestone=issue.milestone_title,
                last_updated=None,  # GitHub API doesn't include updated_at in basic response
            )
        except GitHubNotFoundError:
            logger.warning(f"GitHub issue #{issue_id} not found")
            return None
        except GitHubClientError as e:
            logger.warning(f"Failed to fetch GitHub issue #{issue_id}: {e}")
            raise

    # =========================================================================
    # Jira Status Fetching
    # =========================================================================

    async def fetch_jira_status(
        self,
        issue_ids: list[str],
        use_cache: bool = True,
    ) -> dict[str, IssueStatus]:
        """Fetch current status for Jira issues.

        Args:
            issue_ids: List of Jira issue keys (e.g., ['PROJ-123', 'PROJ-124']).
            use_cache: Whether to use cached results if available.

        Returns:
            Dict mapping issue key to IssueStatus.
        """
        if not self._jira_client:
            logger.warning("Jira client not initialized, skipping Jira status fetch")
            return {}

        results: dict[str, IssueStatus] = {}
        to_fetch: list[str] = []

        # Check cache first
        for issue_id in issue_ids:
            if use_cache:
                cached = self._cache.get("jira", issue_id)
                if cached:
                    results[issue_id] = cached
                    continue
            to_fetch.append(issue_id)

        # Fetch uncached issues
        if to_fetch:
            fetch_tasks = [self._fetch_single_jira_issue(issue_id) for issue_id in to_fetch]
            fetched = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            for issue_id, result in zip(to_fetch, fetched, strict=True):
                if isinstance(result, BaseException):
                    logger.warning(f"Failed to fetch Jira issue {issue_id}: {result}")
                    continue
                if result is not None:
                    results[issue_id] = result
                    self._cache.set(result)

        return results

    async def _fetch_single_jira_issue(self, issue_id: str) -> IssueStatus | None:
        """Fetch status for a single Jira issue."""
        if not self._jira_client:
            return None

        try:
            issue = await self._jira_client.get_issue(issue_id)
            return IssueStatus(
                id=issue.key,
                platform="jira",
                state=issue.status,
                labels=[],  # Jira labels require separate API call, skip for now
                milestone=None,  # Jira uses versions/fix versions, skip for now
                last_updated=None,
            )
        except JiraNotFoundError:
            logger.warning(f"Jira issue {issue_id} not found")
            return None
        except JiraClientError as e:
            logger.warning(f"Failed to fetch Jira issue {issue_id}: {e}")
            raise

    # =========================================================================
    # Multi-Platform Fetch
    # =========================================================================

    async def fetch_all(
        self,
        github_issues: list[str] | None = None,
        jira_issues: list[str] | None = None,
        use_cache: bool = True,
    ) -> dict[str, IssueStatus]:
        """Fetch status for issues from both platforms.

        Args:
            github_issues: List of GitHub issue numbers as strings.
            jira_issues: List of Jira issue keys.
            use_cache: Whether to use cached results.

        Returns:
            Dict mapping prefixed issue IDs to IssueStatus.
            Keys are prefixed with platform: 'GH-10' or 'PROJ-123'.
        """
        results: dict[str, IssueStatus] = {}

        # Fetch in parallel
        tasks = []
        if github_issues:
            tasks.append(self.fetch_github_status(github_issues, use_cache=use_cache))
        if jira_issues:
            tasks.append(self.fetch_jira_status(jira_issues, use_cache=use_cache))

        if not tasks:
            return results

        fetched = await asyncio.gather(*tasks)

        idx = 0
        if github_issues:
            for issue_id, status in fetched[idx].items():
                results[f"GH-{issue_id}"] = status
            idx += 1
        if jira_issues:
            for issue_id, status in fetched[idx].items():
                results[issue_id] = status  # Jira keys are already unique

        return results
