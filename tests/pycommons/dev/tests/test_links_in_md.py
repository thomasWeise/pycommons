"""Test the type."""

from re import compile as re_compile
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.tests.links_in_md import check_links_in_md
from pycommons.io.path import Path, file_path


def test_links_from_md() -> None:
    """Test the links  from markdown."""
    base: Final[Path] = file_path(__file__).up()

    check_links_in_md(base.resolve_inside("md_with_links_1.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_1.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_2.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_3.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_4.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_5.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_no_examples_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_no_examples_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Multi-line code start without "
                f"end in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_3.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Multi-line code start without "
                f"end in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_4.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Multi-line code start without "
                f"end in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_5.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_6.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_7.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_8.md"))

    with pytest.raises(ValueError, match=re_compile(
            f"File {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_empty_9.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_error_fragment_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_error_fragment_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Multi-line code start without "
                f"end in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_no_end_mark_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Multi-line code start without "
                f"end in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_no_end_mark_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"No closing gap for \[...\]\(...\) link "
                f"in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Invalid \[...\]\(...\) "
                f"link in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_2.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Invalid image sequence in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_3.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"No closing gap for image sequence"
                f" in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_4.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_5.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                f"Found no links in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_link_errors_6.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Headline without space after"
                f" # in file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_error_header_1.md"))

    with pytest.raises(
            ValueError, match=re_compile(
                r"Headline without end in "
                f"file {repr(base)[:-1]}.*")):
        check_links_in_md(base.resolve_inside("md_with_error_header_2.md"))
