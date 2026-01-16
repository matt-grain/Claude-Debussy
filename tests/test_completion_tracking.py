"""Unit tests for feature completion tracking and re-run protection."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from debussy.core.models import IssueRef
from debussy.core.state import StateManager


@pytest.fixture
def state_manager(temp_db: Path) -> StateManager:
    """Create a state manager with a temporary database."""
    return StateManager(temp_db)


class TestCompletedFeaturesSchema:
    """Tests for the completed_features table schema."""

    def test_table_created_on_init(self, state_manager: StateManager) -> None:
        """Test that completed_features table is created on initialization."""
        # Query should succeed even if empty
        with state_manager._connection() as conn:
            rows = conn.execute("SELECT * FROM completed_features").fetchall()
        assert rows == []

    def test_migration_on_existing_db(self, temp_dir: Path) -> None:
        """Test that table is added to existing databases without it."""
        db_path = temp_dir / "test_migration.db"

        # Create a minimal database without the new table
        import sqlite3

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE runs (id TEXT PRIMARY KEY)")
        conn.close()

        # StateManager should add the completed_features table
        state = StateManager(db_path)

        # Verify table exists
        with state._connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_features'")
            assert cursor.fetchone() is not None


class TestRecordCompletion:
    """Tests for StateManager.record_completion()."""

    def test_record_completion_basic(self, state_manager: StateManager) -> None:
        """Test recording a basic completion."""
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
        ]
        feature_id = state_manager.record_completion(
            name="Test Feature",
            issues=issues,
            plan_path=Path("/tmp/plans/test-feature/MASTER_PLAN.md"),
        )

        assert feature_id > 0

    def test_record_completion_with_mixed_issues(self, state_manager: StateManager) -> None:
        """Test recording completion with both GitHub and Jira issues."""
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="jira", id="PROJ-123"),
            IssueRef(type="jira", id="PROJ-124"),
        ]
        feature_id = state_manager.record_completion(
            name="Mixed Feature",
            issues=issues,
            plan_path=Path("/tmp/plans/mixed/MASTER_PLAN.md"),
        )

        assert feature_id > 0

        # Verify stored correctly
        feature = state_manager.get_completion_details(feature_id)
        assert feature is not None
        assert feature.name == "Mixed Feature"
        assert len(feature.issues) == 3
        assert feature.issues[0].type == "github"
        assert feature.issues[1].type == "jira"

    def test_record_completion_stores_utc_timestamp(self, state_manager: StateManager) -> None:
        """Test that completion timestamp is stored in UTC."""
        issues = [IssueRef(type="github", id="10")]
        feature_id = state_manager.record_completion(
            name="UTC Test",
            issues=issues,
            plan_path=Path("/tmp/test.md"),
        )

        feature = state_manager.get_completion_details(feature_id)
        assert feature is not None
        # Timestamp should be recent (within last minute)
        now = datetime.now(UTC)
        delta = now - feature.completed_at.replace(tzinfo=UTC)
        assert delta.total_seconds() < 60


class TestFindCompletedFeatures:
    """Tests for StateManager.find_completed_features()."""

    def test_find_no_matches(self, state_manager: StateManager) -> None:
        """Test finding features when none exist."""
        search_issues = [IssueRef(type="github", id="999")]
        matches = state_manager.find_completed_features(search_issues)
        assert matches == []

    def test_find_exact_match(self, state_manager: StateManager) -> None:
        """Test finding a feature with exact issue match."""
        # Record a completion
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
        ]
        state_manager.record_completion(
            name="Exact Match Test",
            issues=issues,
            plan_path=Path("/tmp/test.md"),
        )

        # Search with same issues
        search_issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
        ]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 1
        assert matches[0].name == "Exact Match Test"

    def test_find_partial_match(self, state_manager: StateManager) -> None:
        """Test finding a feature with partial issue overlap."""
        # Record a completion
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
            IssueRef(type="github", id="12"),
        ]
        state_manager.record_completion(
            name="Partial Match Test",
            issues=issues,
            plan_path=Path("/tmp/test.md"),
        )

        # Search with only some matching issues
        search_issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="99"),  # New issue
        ]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 1
        assert matches[0].name == "Partial Match Test"

    def test_find_no_overlap(self, state_manager: StateManager) -> None:
        """Test no matches when issues don't overlap."""
        # Record a completion
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
        ]
        state_manager.record_completion(
            name="No Overlap Test",
            issues=issues,
            plan_path=Path("/tmp/test.md"),
        )

        # Search with different issues
        search_issues = [
            IssueRef(type="github", id="99"),
            IssueRef(type="github", id="100"),
        ]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 0

    def test_find_multiple_features(self, state_manager: StateManager) -> None:
        """Test finding multiple overlapping features."""
        # Record two completions that share an issue
        state_manager.record_completion(
            name="Feature A",
            issues=[
                IssueRef(type="github", id="10"),
                IssueRef(type="github", id="11"),
            ],
            plan_path=Path("/tmp/feature-a.md"),
        )
        state_manager.record_completion(
            name="Feature B",
            issues=[
                IssueRef(type="github", id="10"),
                IssueRef(type="github", id="12"),
            ],
            plan_path=Path("/tmp/feature-b.md"),
        )

        # Search with the shared issue
        search_issues = [IssueRef(type="github", id="10")]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 2
        names = {m.name for m in matches}
        assert "Feature A" in names
        assert "Feature B" in names

    def test_find_jira_issues(self, state_manager: StateManager) -> None:
        """Test finding features with Jira issue references."""
        # Record a completion with Jira issues
        issues = [
            IssueRef(type="jira", id="PROJ-123"),
            IssueRef(type="jira", id="PROJ-124"),
        ]
        state_manager.record_completion(
            name="Jira Feature",
            issues=issues,
            plan_path=Path("/tmp/jira.md"),
        )

        # Search with Jira issue
        search_issues = [IssueRef(type="jira", id="PROJ-123")]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 1
        assert matches[0].name == "Jira Feature"

    def test_find_cross_platform_no_match(self, state_manager: StateManager) -> None:
        """Test that GitHub and Jira issues with same number don't match."""
        # Record with GitHub issue #10
        state_manager.record_completion(
            name="GitHub Feature",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/gh.md"),
        )

        # Search with Jira issue "10"
        search_issues = [IssueRef(type="jira", id="10")]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 0

    def test_find_empty_search(self, state_manager: StateManager) -> None:
        """Test that empty search returns no matches."""
        # Record a completion
        state_manager.record_completion(
            name="Test",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/test.md"),
        )

        # Empty search
        matches = state_manager.find_completed_features([])
        assert matches == []


class TestGetCompletionDetails:
    """Tests for StateManager.get_completion_details()."""

    def test_get_existing_feature(self, state_manager: StateManager) -> None:
        """Test getting details of an existing feature."""
        issues = [
            IssueRef(type="github", id="10"),
            IssueRef(type="github", id="11"),
        ]
        feature_id = state_manager.record_completion(
            name="Detail Test",
            issues=issues,
            plan_path=Path("/tmp/plans/detail/MASTER_PLAN.md"),
        )

        feature = state_manager.get_completion_details(feature_id)

        assert feature is not None
        assert feature.id == feature_id
        assert feature.name == "Detail Test"
        assert len(feature.issues) == 2
        assert feature.plan_path == Path("/tmp/plans/detail/MASTER_PLAN.md")

    def test_get_nonexistent_feature(self, state_manager: StateManager) -> None:
        """Test getting details of a nonexistent feature."""
        feature = state_manager.get_completion_details(99999)
        assert feature is None


class TestValidateIssuesJson:
    """Tests for StateManager.validate_issues_json()."""

    def test_valid_json(self, state_manager: StateManager) -> None:
        """Test validation of valid issues JSON."""
        valid_json = '[{"type": "github", "id": "10"}, {"type": "jira", "id": "PROJ-123"}]'
        assert state_manager.validate_issues_json(valid_json) is True

    def test_empty_array(self, state_manager: StateManager) -> None:
        """Test validation of empty array."""
        assert state_manager.validate_issues_json("[]") is True

    def test_invalid_json(self, state_manager: StateManager) -> None:
        """Test validation of malformed JSON."""
        assert state_manager.validate_issues_json("not json") is False

    def test_not_array(self, state_manager: StateManager) -> None:
        """Test validation of non-array JSON."""
        assert state_manager.validate_issues_json('{"type": "github"}') is False

    def test_missing_type(self, state_manager: StateManager) -> None:
        """Test validation fails when type is missing."""
        assert state_manager.validate_issues_json('[{"id": "10"}]') is False

    def test_missing_id(self, state_manager: StateManager) -> None:
        """Test validation fails when id is missing."""
        assert state_manager.validate_issues_json('[{"type": "github"}]') is False

    def test_invalid_type(self, state_manager: StateManager) -> None:
        """Test validation fails with invalid issue type."""
        assert state_manager.validate_issues_json('[{"type": "gitlab", "id": "10"}]') is False


class TestCorruptedDataHandling:
    """Tests for graceful handling of corrupted data."""

    def test_corrupted_json_skipped_in_find(self, state_manager: StateManager) -> None:
        """Test that corrupted JSON entries are skipped during find."""
        # Insert corrupted data directly
        with state_manager._connection() as conn:
            conn.execute(
                """
                INSERT INTO completed_features (name, completed_at, issues_json, plan_path)
                VALUES (?, ?, ?, ?)
                """,
                ("Corrupted", datetime.now(UTC).isoformat(), "not valid json", "/tmp/bad.md"),
            )

        # Also insert valid data
        state_manager.record_completion(
            name="Valid",
            issues=[IssueRef(type="github", id="10")],
            plan_path=Path("/tmp/valid.md"),
        )

        # Search should find only the valid entry
        search_issues = [IssueRef(type="github", id="10")]
        matches = state_manager.find_completed_features(search_issues)

        assert len(matches) == 1
        assert matches[0].name == "Valid"

    def test_corrupted_json_returns_none_in_get(self, state_manager: StateManager) -> None:
        """Test that corrupted JSON returns None in get_completion_details."""
        # Insert corrupted data directly
        with state_manager._connection() as conn:
            conn.execute(
                """
                INSERT INTO completed_features (name, completed_at, issues_json, plan_path)
                VALUES (?, ?, ?, ?)
                """,
                ("Corrupted", datetime.now(UTC).isoformat(), "not valid json", "/tmp/bad.md"),
            )
            row = conn.execute("SELECT id FROM completed_features WHERE name = 'Corrupted'").fetchone()
            bad_id = row["id"]

        # Get should return None for corrupted entry
        feature = state_manager.get_completion_details(bad_id)
        assert feature is None
