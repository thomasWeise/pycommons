"""Test making the documentation."""

from os.path import dirname
from shutil import copy2
from typing import Final

import pytest

from pycommons.dev.building.build_info import BuildInfo
from pycommons.dev.building.make_documentation import make_documentation
from pycommons.dev.building.run_tests import run_tests
from pycommons.io.path import Path
from pycommons.io.temp import temp_dir

#: the paths to the files needed
__FILES_NEEDED: Final[tuple[str, ...]] = (
    "pyproject.toml", "setup.cfg", "setup.py",
    "README.md", "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
    "tests/pycommons/ds/test_cache.py", "docs/source/conf.py",
)


def test_make_documentation_1() -> None:
    """Test making the documentation."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=None)
        make_documentation(bi)

        bi = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=None,
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=None)
        with pytest.raises(ValueError):
            make_documentation(bi)

        bi = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=None,
            dist_dir=None)
        with pytest.raises(ValueError):
            make_documentation(bi)

        tex: Path = td.resolve_inside("y")
        tex.ensure_file_exists()
        bi = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=tex,
            dist_dir=None)
        with pytest.raises(ValueError):
            make_documentation(bi)


def test_make_documentation_2() -> None:
    """Test making the documentation."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=None)
        run_tests(bi)
        make_documentation(bi)


def test_make_documentation_3() -> None:
    """Test making the documentation."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=None)
        run_tests(bi)
        cv = td.resolve_inside(".coverage")
        cv.write_all_str("wsT+fiesefjwrefswfk")
        make_documentation(bi)
