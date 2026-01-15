"""Resource loader using importlib.resources for packaged files."""

from importlib import resources
from pathlib import Path


def get_resource_text(subpackage: str, filename: str) -> str:
    """Load a resource file as text from the debussy.resources package.

    Args:
        subpackage: The subpackage name (agents, skills, commands)
        filename: The resource filename (e.g., debussy.md)

    Returns:
        The file contents as a string

    Raises:
        FileNotFoundError: If the resource doesn't exist
    """
    package = f"debussy.resources.{subpackage}"
    ref = resources.files(package).joinpath(filename)
    return ref.read_text(encoding="utf-8")


def copy_resource_to(subpackage: str, filename: str, dest: Path) -> None:
    """Copy a resource file to a destination path.

    Args:
        subpackage: The subpackage name (agents, skills, commands)
        filename: The resource filename
        dest: Destination path to write to
    """
    content = get_resource_text(subpackage, filename)
    dest.write_text(content, encoding="utf-8")
