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

    with pytest.raises(
            TypeError, match="descriptor '__len__' requires a 'str'.*"):
        setup_doc(None, prj_base, 2023, None, None, None, None)

    with (pytest.raises(
            TypeError, match="descriptor '__len__' requires a 'str'.*"),
            temp_dir() as td):
        setup_doc(td, None, 2023, None, None, None, None)

    with (pytest.raises(
            ValueError, match="copyright_start_year=-1 is invalid, must.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, -1, None, None, None, None)

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

    with (pytest.raises(
            ValueError, match=f"copyright_start_year={current_year + 1}.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, current_year + 1, None, None, None, None)

    with (pytest.raises(
            TypeError, match="dependencies should be an instance of.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, 2023, 1, None, None, None)

    with (pytest.raises(
            TypeError, match="descriptor 'strip' for 'str' objects doe.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, 2023, (1, ), None, None, None)

    with (pytest.raises(
            TypeError, match="descriptor 'strip' for 'str' objects doe.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, 2023, (
            "pycommons", ("x", 1)), None, None, None)

    with (pytest.raises(
            TypeError, match="descriptor 'strip' for 'str' objects doe.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, 2023, (
            "pycommons", (1, "x")), None, None, None)

    with (pytest.raises(
            ValueError, match="'yyyx-b' is not among the known.*"),
            temp_dir() as td):
        setup_doc(td, prj_base, 2023, ("yyyx-b", ), None, None, None)
