"""Run the pytest tests."""

from argparse import ArgumentParser
from itertools import chain
from typing import Final

from pycommons.dev.building.build_info import (
    BuildInfo,
    parse_project_arguments,
)
from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.io.path import Path, delete_path
from pycommons.types import type_error


def run_tests(info: BuildInfo) -> None:
    """
    Perform the unit testing of the project.

    This code cannot really be unit tested, as it would run the itself
    recursively.

    :param info: the build information

    >>> try:
    ...     run_tests(None)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi

    >>> try:
    ...     run_tests(1)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi
    """
    if not isinstance(info, BuildInfo):
        raise type_error(info, "info", BuildInfo)

    logger(
        f"Performing unit tests for {info}. First erasing old coverage data.")

    info.command(("coverage", "erase")).execute()
    coverage_file: Final[Path] = info.base_dir.resolve_inside(".coverage")
    if coverage_file.exists():
        delete_path(coverage_file)

    logger("Now running doctests.")
    ignores: Final[list] = []
    if info.doc_dest_dir is not None:
        ignores.append(f"--ignore={info.doc_dest_dir}")
    if info.doc_source_dir is not None:
        ignores.append(f"--ignore={info.doc_source_dir}")
    if info.dist_dir is not None:
        ignores.append(f"--ignore={info.dist_dir}")
    if info.tests_dir is not None:
        ignores.append(f"--ignore={info.tests_dir}")
    info.command(chain((
        "coverage", "run", "-a", f"--include={info.package_name}/*",
        "-m", "pytest", "--strict-config",
        "--doctest-modules"), ignores)).execute()

    if info.tests_dir is None:
        logger("No unit tests found.")
    else:
        logger("Now unit tests.")
        if info.examples_dir is not None:
            del ignores[-1]
        if info.examples_dir is not None:
            ignores.append(f"--ignore={info.examples_dir}")
        info.command(chain((
            "coverage", "run", "-a", f"--include={info.package_name}/*",
            "-m", "pytest", "--strict-config",
            info.tests_dir), ignores)).execute()

    logger(f"Finished doing unit tests for {info}.")


# Run conversion if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Run the unit tests for a Python Project.",
        "This utility runs the unit tests and computes the coverage data "
        "in a unified way.")
    run_tests(parse_project_arguments(parser))
