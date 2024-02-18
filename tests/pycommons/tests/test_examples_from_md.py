"""Test the type."""

from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.io.path import Path, file_path
from pycommons.tests.examples_in_md import check_examples_in_md


def test_examples_from_md() -> None:
    """Test the examples from markdown."""
    base: Final[Path] = file_path(__file__).up()

    try:
        check_examples_in_md(base.resolve_inside("md_no_examples_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("No example found in " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_no_examples_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("No example found in " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_no_end_mark_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("No end mark for start mark")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_no_end_mark_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("No end mark for start mark")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Empty fragment ")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Empty fragment ")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_3.md"))
    except ValueError as ve:
        assert str(ve).startswith("No end mark for start mark")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_4.md"))
    except ValueError as ve:
        assert str(ve).startswith("No end mark for start mark")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_5.md"))
    except ValueError as ve:
        assert str(ve).startswith("No end mark for start mark")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_6.md"))
    except ValueError as ve:
        assert str(ve).startswith("Did not find newline in stripped fragment")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_7.md"))
    except ValueError as ve:
        assert str(ve).startswith("Did not find newline in stripped fragment")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_8.md"))
    except ValueError as ve:
        assert str(ve).startswith("Did not find newline in stripped fragment")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_empty_9.md"))
    except ValueError as ve:
        assert str(ve).endswith("contains no text.")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_error_fragment_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Error when compiling")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_error_fragment_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Error when compiling")
    else:
        pytest.fail("There should be an error!")

    try:
        check_examples_in_md(base.resolve_inside("md_error_fragment_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Error when executing")
    else:
        pytest.fail("There should be an error!")
