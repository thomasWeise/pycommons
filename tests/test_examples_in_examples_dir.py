"""Test the examples that ship with our package."""

from pycommons.dev.tests.examples_in_dir import check_examples_in_dir
from pycommons.io.path import file_path


def test_examples_in_examples_dir() -> None:
    """Test the examples that ship with our package."""
    check_examples_in_dir(file_path(__file__).up(2).resolve_inside(
        "examples"))
