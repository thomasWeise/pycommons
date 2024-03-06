"""Test the documentation info module."""

from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.doc.doc_info import parse_readme_md, parse_version_py
from pycommons.io.path import Path, file_path


def test_parse_readme_md() -> None:
    """Test parsing of readme.md files."""
    base: Final[Path] = file_path(__file__).up()

    try:
        parse_readme_md(base.resolve_inside("md_2_titles.md"))
    except ValueError as ve:
        assert str(ve).startswith("Already have title")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_1.md"))
    except ValueError as ve:
        assert str(ve).startswith("Got '## x. blubb' and finding index 1")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_2.md"))
    except ValueError as ve:
        assert str(ve).startswith("Got '## blubb' after having index.")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_2nd_level_heading_3.md"))
    except ValueError as ve:
        assert str(ve).startswith("Found index 1 in line '## 1. blubb'")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_readme_md(base.resolve_inside(
            "md_error_no_title.md"))
    except ValueError as ve:
        assert str(ve).startswith("No title in '")
    else:
        pytest.fail("There should be an error!")


def test_parse_version() -> None:
    """Test parsing of version.py files."""
    base: Final[Path] = file_path(__file__).up()

    try:
        parse_version_py(base.resolve_inside(
            "version_error_1.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Incorrect string limits for")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_2.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Strange version string")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_2.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Strange version string")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_3.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Version defined as")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_4.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Undelimited string in")
    else:
        pytest.fail("There should be an error!")

    try:
        parse_version_py(base.resolve_inside(
            "version_error_5.txt"))
    except ValueError as ve:
        assert str(ve).startswith("Did not find version attr")
    else:
        pytest.fail("There should be an error!")
