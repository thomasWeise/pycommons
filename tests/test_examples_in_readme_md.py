"""Test the examples in the README.md file."""

from pycommons.dev.tests.examples_in_md import check_examples_in_md
from pycommons.io.path import file_path


def test_examples_in_readme_md() -> None:
    """Test the examples in the README.md file."""
    check_examples_in_md(file_path(__file__).up(
        2).resolve_inside("README.md"))
