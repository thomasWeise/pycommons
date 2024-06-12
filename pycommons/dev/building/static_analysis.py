"""Perform the static code analysis."""

from argparse import ArgumentParser
from os import chdir, getcwd
from typing import Any, Callable, Final, Iterable

from pycommons.dev.building.build_info import (
    BuildInfo,
    parse_project_arguments,
    replace_in_cmd,
)
from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path
from pycommons.processes.python import PYTHON_INTERPRETER
from pycommons.processes.shell import Command
from pycommons.types import type_error


def __exec(arguments: Iterable[str],
           info: BuildInfo,
           errors: Callable[[str], Any]) -> None:
    """
    Execute a command.

    :param arguments: the arguments
    :param info: the build info
    :param errors: the error collector
    """
    cmd: Final[Command] = info.command(arguments)
    try:
        cmd.execute(True)
    except ValueError as ve:
        errors(f"{cmd} failed with {ve!r}.")


#: a list of analysis to be applied to the base directory
__BASE_ANALYSES: Final[tuple[tuple[str, ...], ...]] = (
    ("flake8", ".", "--ignore=B008,B009,B010,DUO102,TRY003,TRY101,W503"),
    (PYTHON_INTERPRETER, "-m", "pyflakes", "."),
    ("pyroma", "."),
    ("semgrep", ".", "--error", "--strict", "--use-git-ignore",
     "--skip-unknown-extensions", "--optimizations", "all", "--config=auto"),
    ("pydocstyle", ".", "--convention=pep257"),
    ("vulture", ".", "--min-confidence", "61"),
    ("dodgy", "."),
)

#: a list of analysis to be applied to the package directory
__PACKAGE_ANALYSES: Final[tuple[tuple[str, ...], ...]] = (
    ("pylint", ".", "--disable=C0103,C0302,C0325,R0801,R0901,R0902,R0903,"
                    "R0911,R0912,R0913,R0914,R0915,R1702,R1728,W0212,"
                    "W0238,W0703"),
    ("mypy", ".", "--no-strict-optional", "--check-untyped-defs"),
    ("bandit", "-r", ".", "-s", "B311"),
    ("tryceratops", ".", "-i", "TRY003", "-i", "TRY101"),
    ("unimport", "."),
    ("pycodestyle", "."),
    ("ruff", "check", "--target-version", "py310", "--select",
     "A,ANN,B,C,C4,COM,D,DJ,DTZ,E,ERA,EXE,F,G,I,ICN,INP,ISC,N,NPY,PIE,PLC,"
     "PLE,PLR,PLW,PT,PYI,Q,RET,RSE,RUF,S,SIM,T,T10,T20,TID,TRY,UP,W,YTT",
     "--ignore=ANN001,ANN002,ANN003,ANN101,ANN204,ANN401,B008,B009,B010,"
     "C901,D203,D208,D212,D401,D407,D413,N801,PLR0911,PLR0912,PLR0913,"
     "PLR0915,PLR2004,PYI041,RUF100,TRY003,UP035", "--line-length", "79",
     "."),
)

#: a list of analysis to be applied to the test directory
__TESTS_ANALYSES: Final[tuple[tuple[str, ...], ...]] = (
    ("bandit", "-r", ".", "-s", "B311,B101"),
    ("tryceratops", ".", "-i", "TRY003", "-i", "TRY101"),
    ("unimport", "."),
    ("pycodestyle", "."),
    ("ruff", "check", "--target-version", "py310", "--select",
     "A,ANN,B,C,C4,COM,D,DJ,DTZ,E,ERA,EXE,F,G,I,ICN,ISC,N,NPY,PIE,PLC,PLE,"
     "PLR,PLW,PYI,Q,RET,RSE,RUF,T,SIM,T10,T20,TID,TRY,UP,W,YTT",
     "--ignore=ANN001,ANN002,ANN003,ANN101,ANN204,ANN401,B008,B009,B010,"
     "C901,D203,D208,D212,D401,D407,D413,N801,PLR0911,PLR0912,PLR0913,"
     "PLR0915,PLR2004,PYI041,RUF100,TRY003,UP035", "--line-length", "79",
     "."),
)

#: a list of analysis to be applied to the examples directory
__EXAMPLES_ANALYSES: Final[tuple[tuple[str, ...], ...]] = (
    ("bandit", "-r", ".", "-s", "B311"),
    ("tryceratops", ".", "-i", "TRY003", "-i", "TRY101"),
    ("unimport", "."),
    ("pycodestyle", "--ignore=E731,W503", "."),
    ("ruff", "check", "--target-version", "py310", "--select",
     "A,ANN,B,C,C4,COM,D,DJ,DTZ,E,ERA,EXE,F,G,I,ICN,ISC,N,NPY,PIE,PLC,"
     "PLE,PLR,PLW,PT,PYI,Q,RET,RSE,RUF,S,SIM,T10,TID,TRY,UP,W,YTT",
     "--ignore=ANN001,ANN002,ANN003,ANN101,ANN204,ANN401,B008,B009,"
     "B010,C901,D203,D208,D212,D401,D407,D413,N801,PLR0911,PLR0912,"
     "PLR0913,PLR0915,PLR2004,PYI041,RUF100,TRY003,UP035", "--line-length",
     "79", "."),
)

#: a list of analysis to be applied to the examples directory
__DOC_SOURCE: Final[tuple[tuple[str, ...], ...]] = __EXAMPLES_ANALYSES


def static_analysis(info: BuildInfo) -> None:
    """
    Perform the static code analysis for a Python project.

    :param info: the build information

    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     static_analysis(BuildInfo(
    ...         Path(__file__).up(4), "pycommons", "tests",
    ...             "examples", "docs/source"))

    >>> try:
    ...     static_analysis(None)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi

    >>> try:
    ...     static_analysis(1)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi
    """
    if not isinstance(info, BuildInfo):
        raise type_error(info, "info", BuildInfo)

    text: Final[str] = f"static analysis for {info}"
    logger(f"Performing {text}.")

    current: Final[Path] = directory_path(getcwd())
    try:
        errors: list[str] = []
        for analysis, path in ((__BASE_ANALYSES, info.base_dir),
                               (__PACKAGE_ANALYSES, info.sources_dir),
                               (__TESTS_ANALYSES, info.tests_dir),
                               (__EXAMPLES_ANALYSES, info.examples_dir),
                               (__DOC_SOURCE, info.doc_source_dir)):
            if path is None:
                continue
            for a in analysis:
                __exec(replace_in_cmd(a, path), info, errors.append)
    finally:
        chdir(current)

    if list.__len__(errors) <= 0:
        logger(f"Successfully completed {text}.")
        return

    logger(f"The {text} encountered the following errors:")
    for error in errors:
        logger(error)

    raise ValueError(f"Failed to do {text}: {'; '.join(errors)}.")


# Run static analysis program if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Apply Static Code Analysis Tools",
        "This utility applies a big heap of static code analysis tools in "
        "a unified way as I use it throughout my projects.")
    static_analysis(parse_project_arguments(parser))
