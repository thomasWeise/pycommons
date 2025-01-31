"""Test making distributions."""

from os.path import dirname
from shutil import copy2
from typing import Final

import pytest

from pycommons.dev.building.build_info import BuildInfo
from pycommons.dev.building.make_dist import make_dist
from pycommons.dev.building.make_documentation import make_documentation
from pycommons.dev.building.run_tests import run_tests
from pycommons.dev.building.static_analysis import static_analysis
from pycommons.io.path import Path, write_lines
from pycommons.io.temp import temp_dir

#: the paths to the files needed
__FILES_NEEDED_1: Final[tuple[str, ...]] = (
    "pyproject.toml", "setup.cfg", "setup.py", "LICENSE",
    "README.md", "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
    "tests/pycommons/ds/test_cache.py", "docs/source/conf.py",
)


def test_make_dist_1a() -> None:
    """Test making the distribution."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_1:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()
        td.resolve_inside("dist").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=td.resolve_inside("dist"))
        run_tests(bi)
        static_analysis(bi)
        make_documentation(bi)
        make_dist(bi)


def test_make_dist_1b() -> None:
    """Test making the distribution."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_1:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            if source.basename() == "setup.cfg":
                lines = list(map(
                    str.rstrip, source.read_all_str().split("\n")))
                idx = lines.index("[options.extras_require]")
                while (len(lines) > idx) and (str.__len__(lines[idx]) > 0):
                    del lines[idx]
                del lines[idx]
                with dest.open_for_write() as ddds:
                    write_lines(lines, ddds)
            else:
                copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()
        td.resolve_inside("dist").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=td.resolve_inside("dist"))
        run_tests(bi)
        static_analysis(bi)
        make_documentation(bi)
        make_dist(bi)


#: the paths to the files needed
__FILES_NEEDED_2: Final[tuple[str, ...]] = (
    "pyproject.toml", "setup.cfg",
    "README.md", "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
    "tests/pycommons/ds/test_cache.py", "docs/source/conf.py",
)


def test_make_dist_2() -> None:
    """Test making the distribution."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_2:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
        td.resolve_inside("docs/build").ensure_dir_exists()
        td.resolve_inside("dist").ensure_dir_exists()

        bi: BuildInfo = BuildInfo(
            base_dir=td,
            package_name="pycommons",
            tests_dir=td.resolve_inside("tests"),
            examples_dir=None,
            doc_source_dir=td.resolve_inside("docs/source"),
            doc_dest_dir=td.resolve_inside("docs/build"),
            dist_dir=td.resolve_inside("dist"))

        with pytest.raises(ValueError):
            make_dist(bi)


def test_make_dist_3() -> None:
    """Test making the distribution."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED_2:
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

        with pytest.raises(ValueError):
            make_dist(bi)
