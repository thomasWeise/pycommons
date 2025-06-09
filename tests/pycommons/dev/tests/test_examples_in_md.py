"""Test the type."""
from re import compile as re_compile
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.tests.examples_in_md import check_examples_in_md
from pycommons.io.path import Path, file_path


def test_examples_from_md() -> None:
    """Test the examples from markdown."""
    base: Final[Path] = file_path(__file__).up()

    with pytest.raises(
            ValueError, match=re_compile(
                f"No example found in {repr(base)[:-1]}.*")):
        check_examples_in_md(base.resolve_inside("md_no_examples_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"No example found in {repr(base)[:-1]}.*")):
        check_examples_in_md(base.resolve_inside("md_no_examples_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"No end mark for start mark.*")):
        check_examples_in_md(base.resolve_inside("md_no_end_mark_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"No end mark for start mark.*")):
        check_examples_in_md(base.resolve_inside("md_no_end_mark_2.md"))

    with pytest.raises(ValueError, match=re_compile(r"Empty fragment .*")):
        check_examples_in_md(base.resolve_inside("md_empty_1.md"))

    with pytest.raises(ValueError, match=re_compile(r"Empty fragment .*")):
        check_examples_in_md(base.resolve_inside("md_empty_2.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"No end mark for start mark.*")):
        check_examples_in_md(base.resolve_inside("md_empty_3.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"No end mark for start mark.*")):
        check_examples_in_md(base.resolve_inside("md_empty_4.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"No end mark for start mark.*")):
        check_examples_in_md(base.resolve_inside("md_empty_5.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Did not find newline in stripped fragment.*")):
        check_examples_in_md(base.resolve_inside("md_empty_6.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Did not find newline in stripped fragment.*")):
        check_examples_in_md(base.resolve_inside("md_empty_7.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Did not find newline in stripped fragment.*")):
        check_examples_in_md(base.resolve_inside("md_empty_8.md"))

    with pytest.raises(ValueError, match=re_compile(r".*contains no text.")):
        check_examples_in_md(base.resolve_inside("md_empty_9.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"Error when compiling.*")):
        check_examples_in_md(base.resolve_inside("md_error_fragment_1.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"Error when compiling.*")):
        check_examples_in_md(base.resolve_inside("md_error_fragment_1.md"))

    with pytest.raises(ValueError, match=re_compile(
            r"Error when executing.*")):
        check_examples_in_md(base.resolve_inside("md_error_fragment_2.md"))
