"""Tests for learnings parser."""

from pathlib import Path

from debussy.parsers.learnings import Learning, extract_learnings


class TestExtractLearnings:
    """Tests for extract_learnings function."""

    def test_extract_learnings_with_section(self, tmp_path: Path) -> None:
        """Test extracting learnings from a file with ## Learnings section."""
        notes = tmp_path / "notes.md"
        notes.write_text("""# Phase Notes

## Summary
Did some stuff.

## Learnings
- First learning about the project
- Second learning with details
- Third one

## Next Steps
Continue work.
""")
        learnings = extract_learnings(notes, "1")

        assert len(learnings) == 3
        assert learnings[0].content == "First learning about the project"
        assert learnings[0].phase_id == "1"
        assert learnings[1].content == "Second learning with details"
        assert learnings[2].content == "Third one"

    def test_extract_learnings_no_section(self, tmp_path: Path) -> None:
        """Test returns empty list when no ## Learnings section."""
        notes = tmp_path / "notes.md"
        notes.write_text("""# Phase Notes

## Summary
Did some stuff.

## Next Steps
Continue work.
""")
        learnings = extract_learnings(notes, "1")
        assert learnings == []

    def test_extract_learnings_empty_section(self, tmp_path: Path) -> None:
        """Test returns empty list when Learnings section is empty."""
        notes = tmp_path / "notes.md"
        notes.write_text("""# Phase Notes

## Learnings

## Next Steps
Continue work.
""")
        learnings = extract_learnings(notes, "1")
        assert learnings == []

    def test_extract_learnings_file_not_exists(self, tmp_path: Path) -> None:
        """Test returns empty list when file doesn't exist."""
        notes = tmp_path / "nonexistent.md"
        learnings = extract_learnings(notes, "1")
        assert learnings == []

    def test_extract_learnings_asterisk_bullets(self, tmp_path: Path) -> None:
        """Test extracting learnings with asterisk bullets."""
        notes = tmp_path / "notes.md"
        notes.write_text("""## Learnings
* Learning with asterisk
* Another asterisk learning
""")
        learnings = extract_learnings(notes, "2")

        assert len(learnings) == 2
        assert learnings[0].content == "Learning with asterisk"

    def test_extract_learnings_case_insensitive(self, tmp_path: Path) -> None:
        """Test section header is case insensitive."""
        notes = tmp_path / "notes.md"
        notes.write_text("""## LEARNINGS
- Uppercase header learning
""")
        learnings = extract_learnings(notes, "1")

        assert len(learnings) == 1
        assert learnings[0].content == "Uppercase header learning"

    def test_learning_dataclass(self) -> None:
        """Test Learning dataclass."""
        learning = Learning(
            content="Test learning",
            phase_id="1",
            source_file=Path("/test/notes.md"),
        )
        assert learning.content == "Test learning"
        assert learning.phase_id == "1"
        assert learning.source_file == Path("/test/notes.md")
