"""Test the examples in the README.md file."""

from pycommons.io.path import file_path
from pycommons.tests.examples_from_md import check_examples_from_md


def test_examples_in_readme_md() -> None:
    """Test the examples in the README.md file."""
    check_examples_from_md(file_path(__file__).up(
        2).resolve_inside("README.md"))
