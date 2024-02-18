"""Test the type."""

from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.io.path import Path, file_path
from pycommons.tests.links_in_md import check_links_in_md


def test_links_from_md() -> None:
    """Test the links  from markdown."""
    base: Final[Path] = file_path(__file__).up()

    check_links_in_md(base.resolve_inside("md_with_links_1.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_1.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_2.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_3.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_4.md"))
    check_links_in_md(base.resolve_inside("md_with_incomplete_links_5.md"))

    try:
        check_links_in_md(base.resolve_inside("md_no_examples_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_no_examples_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_3.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Multi-line code start without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_4.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Multi-line code start without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_5.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Multi-line code start without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_6.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_7.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_8.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_empty_9.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "File " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_error_fragment_1.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_error_fragment_2.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_no_end_mark_1.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Multi-line code start without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_no_end_mark_2.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Multi-line code start without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_1.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "No closing gap for [...](...) link in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_2.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Invalid [...](...) link in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_3.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Invalid image sequence in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_4.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "No closing gap for image sequence in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_5.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_link_errors_6.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Found no links in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_error_header_1.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Headline without space after # in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")

    try:
        check_links_in_md(base.resolve_inside("md_with_error_header_2.md"))
    except ValueError as ve:
        assert str(ve).startswith(
            "Headline without end in file " + repr(base)[:-1])
    else:
        pytest.fail("There should be an error!")
