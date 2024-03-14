"""Perform the static code analysis."""

from argparse import ArgumentParser
from os import chdir, getcwd
from typing import Any, Callable, Final, Iterable

from pycommons.dev.building.build_info import (
    BuildInfo,
    parse_project_arguments,
)
from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path
from pycommons.processes.python import PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_FORWARD, Command
from pycommons.types import type_error


def __execute(arguments: Iterable[str], wd: Path, timeout: int,
              errors: Callable[[str], Any]) -> None:
    """
    Execute a command.

    :param arguments: the arguments
    :param wd: the working directory
    :param timeout: the timeout
    :param errors: the error collector
    """
    cmd: Final[Command] = Command(
        arguments, working_dir=wd, stdout=STREAM_FORWARD,
        stderr=STREAM_FORWARD, timeout=timeout)
    try:
        cmd.execute(True)
    except ValueError as ve:
        errors(f"{cmd} failed with {ve!r}.")


def __replace(orig: Iterable[str], replacement: Path) -> Iterable[str]:
    """
    Replace the `"."` with the given path.

    :param orig: the original sequence
    :param replacement: the replacement
    :return: the replaced sequence
    """
    return (replacement if f == "." else f for f in orig)


#: a list of analysis to be applied to the base directory
__BASE_ANALYSES: Final[tuple[tuple[str, ...], ...]] = (
    ("flake8", ".", "--ignore=,B008,B009,B010,DUO102,TRY003,TRY101,W503"),
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
    ("ruff", "--target-version", "py310", "--select",
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
    ("ruff", "--target-version", "py310", "--select",
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
    ("ruff", "--target-version", "py310", "--select",
     "A,ANN,B,C,C4,COM,D,DJ,DTZ,E,ERA,EXE,F,G,I,ICN,ISC,N,NPY,PIE,PLC,"
     "PLE,PLR,PLW,PT,PYI,Q,RET,RSE,RUF,S,SIM,T10,TID,TRY,UP,W,YTT",
     "--ignore=ANN001,ANN002,ANN003,ANN101,ANN204,ANN401,B008,B009,"
     "B010,C901,D203,D208,D212,D401,D407,D413,N801,PLR0911,PLR0912,"
     "PLR0913,PLR0915,PLR2004,PYI041,RUF100,TRY003,UP035", "--line-length",
     "79", "."),
)


def static_analysis(info: BuildInfo, timeout: int = 3600) -> None:
    """
    Perform the static code analysis for a Python project.

    :param info: the build information
    :param timeout: the timeout for every single step

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     static_analysis(BuildInfo(
    ...         Path(__file__).up(4), "pycommons", "tests", "examples"))
    >>> "Successfully completed" in s.getvalue()
    True

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

    >>> try:
    ...     with redirect_stdout(s):
    ...         static_analysis(BuildInfo(Path(__file__).up(4), "pycommons",
    ...             "tests", "examples"), None)
    ... except TypeError as te:
    ...     print(te)
    timeout should be an instance of int but is None.

    >>> try:
    ...     with redirect_stdout(s):
    ...         static_analysis(BuildInfo(Path(__file__).up(4), "pycommons",
    ...             "tests", "examples"), 1.2)
    ... except TypeError as te:
    ...     print(te)
    timeout should be an instance of int but is float, namely '1.2'.

    >>> try:
    ...     with redirect_stdout(s):
    ...         static_analysis(BuildInfo(Path(__file__).up(4), "pycommons",
    ...             "tests", "examples"), 0)
    ... except ValueError as ve:
    ...      print(ve)
    timeout=0 is invalid, must be in 1..1000000.
    """
    if not isinstance(info, BuildInfo):
        raise type_error(info, "info", BuildInfo)

    text: str = (f"static analysis for {info} with "
                 f"per-step timeout of {timeout}s")
    logger(f"Performing {text}.")

    current: Final[Path] = directory_path(getcwd())
    try:
        errors: list[str] = []
        for analysis, path in ((__BASE_ANALYSES, info.base_dir),
                               (__PACKAGE_ANALYSES, info.sources_dir),
                               (__TESTS_ANALYSES, info.tests_dir),
                               (__EXAMPLES_ANALYSES, info.examples_dir)):
            if path is None:
                continue
            for a in analysis:
                __execute(__replace(a, path), info.base_dir,
                          timeout, errors.append)
    finally:
        chdir(current)

    if list.__len__(errors) <= 0:
        logger(f"Successfully completed {text}.")
        return

    logger(f"The {text} encountered the following errors:")
    for error in errors:
        logger(error)

    raise ValueError(f"Failed to do {text}.")


# Run conversion if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Apply Static Code Analysis Tools",
        "This utility applies a big heap of static code analysis tools in "
        "a unified way as I use it throughout my projects.")
    static_analysis(parse_project_arguments(parser))
