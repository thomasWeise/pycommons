"""Test the documentation setup module."""

from datetime import UTC, datetime
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.dev.doc.setup_doc import setup_doc
from pycommons.io.path import Path, file_path
from pycommons.io.temp import temp_dir


def test_setup_doc() -> None:
    """Test documentation setup."""
    src_base: Final[Path] = file_path(__file__).up()
    prj_base: Final[Path] = src_base.up(4)

    with temp_dir() as td:
        setup_doc(td, prj_base, 2023, None, None, None, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    try:
        setup_doc(None, prj_base, 2023, None, None, None, None)
    except TypeError as te:
        assert str(te).startswith("descriptor '__len__' requires a 'str'")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, None, 2023, None, None, None, None)
    except TypeError as te:
        assert str(te).startswith("descriptor '__len__' requires a 'str'")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, -1, None, None, None, None)
    except ValueError as ve:
        assert str(ve).startswith("copyright_start_year=-1 is invalid, must")
    else:
        pytest.fail("There should be an error!")

    current_year: Final[int] = datetime.now(UTC).year

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year, None, None, None, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year - 3, None, None, None, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year, None, None, None, "./static")
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year, [], None, None, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year, None, {
            "https://example.com": "http://example.org"}, None, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    with temp_dir() as td:
        setup_doc(td, prj_base, current_year, None, {
            "https://example.com": "http://example.org"}, {
            "https://example.com/1.txt": "./1.txt"}, None)
        td.resolve_inside("README.md").enforce_file()
        td.resolve_inside("index.rst").enforce_file()

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, current_year + 1, None, None, None, None)
    except ValueError as ve:
        assert str(ve).startswith(f"copyright_start_year={current_year + 1}")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, 2023, 1, None, None, None)
    except TypeError as te:
        assert str(te).startswith("dependencies should be an instance of")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, 2023, (1, ), None, None, None)
    except TypeError as te:
        assert str(te).startswith("descriptor 'strip' for 'str' objects doe")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, 2023, (
                "pycommons", ("x", 1)), None, None, None)
    except TypeError as te:
        assert str(te).startswith("descriptor 'strip' for 'str' objects doe")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, 2023, (
                "pycommons", (1, "x")), None, None, None)
    except TypeError as te:
        assert str(te).startswith("descriptor 'strip' for 'str' objects doe")
    else:
        pytest.fail("There should be an error!")

    try:
        with temp_dir() as td:
            setup_doc(td, prj_base, 2023, ("yyyx-b", ), None, None, None)
    except ValueError as ve:
        assert str(ve).startswith("'yyyx-b' is not among the known")
    else:
        pytest.fail("There should be an error!")
