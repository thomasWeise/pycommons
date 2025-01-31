"""Test running the static analysis."""

from os.path import dirname
from shutil import copy2
from typing import Final

import pytest

from pycommons.dev.building.build_info import BuildInfo
from pycommons.dev.building.static_analysis import static_analysis
from pycommons.io.path import UTF8, Path
from pycommons.io.temp import temp_dir

#: the paths to the files needed
__FILES_NEEDED: Final[tuple[str, ...]] = (
    "pyproject.toml", "setup.cfg", "setup.py",
    "README.md", "pycommons/version.py", "pycommons/__init__.py",
    "pycommons/ds/__init__.py", "pycommons/ds/cache.py",
    "tests/pycommons/ds/test_cache.py",
)


def test_static_analysis_1() -> None:
    """Test running the static analysis."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED:
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
        static_analysis(bi)


def test_static_analysis_2() -> None:
    """Test running the static analysis."""
    root_dir: Final[Path] = Path(__file__).up(5)

    with temp_dir() as td:
        for file in __FILES_NEEDED:
            source: Path = root_dir.resolve_inside(file)
            source.enforce_file()
            dest: Path = td.resolve_inside(file)
            Path(dirname(dest)).ensure_dir_exists()
            copy2(source, dest)
            dest.enforce_file()
            if dest.basename() == "cache.py":
                with open(dest, "a", encoding=UTF8) as dst:
                    dst.write("\n\n1 = 5")

        bi: BuildInfo = BuildInfo(base_dir=td,
                                  package_name="pycommons",
                                  tests_dir=td.resolve_inside("tests"),
                                  examples_dir=None,
                                  doc_source_dir=None,
                                  doc_dest_dir=None,
                                  dist_dir=None)
        with pytest.raises(ValueError):
            static_analysis(bi)
