"""Test the links in the README.md files."""

from pycommons.io.path import file_path
from pycommons.tests.links_in_md import check_links_in_md


def test_links_in_readme_md() -> None:
    """Test the links in the README.md file."""
    check_links_in_md(file_path(__file__).up(
        2).resolve_inside("README.md"))


def test_links_in_contributing_md() -> None:
    """Test the links in the CONTRIBUTING.md file."""
    check_links_in_md(file_path(__file__).up(
        2).resolve_inside("CONTRIBUTING.md"))
