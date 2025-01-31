"""Test running tests."""

from os.path import dirname
from shutil import copy2
from typing import Final

import pytest

from pycommons.dev.building.build_info import BuildInfo
from pycommons.dev.building.run_tests import run_tests
from pycommons.io.path import UTF8, Path
from pycommons.io.temp import temp_dir

#: the paths to the files needed
__FILES_NEEDED_1: Final[tuple[str, ...]] = (
    "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
    "tests/pycommons/ds/test_cache.py",
)


def test_run_tests_1a() -> None:
    """Test running tests."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_1:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()

        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=td.resolve_inside("tests"),
                                  examples_dir=None,
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        run_tests(bi)


def test_run_tests_1b() -> None:
    """Test running tests."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_1:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
            if dest.basename() == "test_cache.py":
                with open(dest, "a", encoding=UTF8) as dst:
                    dst.write("\n\n")
                    dst.write("def test_fail():\n")
                    dst.write("    raise ValueError('Bla!')\n")

        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=td.resolve_inside("tests"),
                                  examples_dir=None,
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        with pytest.raises(ValueError):
            run_tests(bi)


#: the paths to the files needed
__FILES_NEEDED_2: Final[tuple[str, ...]] = (
    "examples/cache.py", "pycommons/version.py",
    "pycommons/__init__.py", "pycommons/ds/__init__.py",
    "pycommons/ds/cache.py", "tests/pycommons/ds/test_cache.py",
)


def test_run_tests_2() -> None:
    """Test running tests."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_2:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()

        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=td.resolve_inside("tests"),
                                  examples_dir=td.resolve_inside("examples"),
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        run_tests(bi)


#: the paths to the files needed
__FILES_NEEDED_3: Final[tuple[str, ...]] = (
    "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
)


def test_run_tests_3() -> None:
    """Test running tests."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_3:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()

        tests = td.resolve_inside("tests")
        tests.ensure_dir_exists()
        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=tests,
                                  examples_dir=None,
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        with pytest.raises(ValueError):
            run_tests(bi)


def test_run_tests_4() -> None:
    """Test running tests."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_3:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside(".coverage").ensure_file_exists()
        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=None,
                                  examples_dir=None,
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        run_tests(bi)
