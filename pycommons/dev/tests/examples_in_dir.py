"""Test all the example code in a directory."""
from random import randint
from typing import Final

from pycommons.dev.tests.compile_and_run import compile_and_run
from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path
from pycommons.types import type_error


def check_examples_in_dir(directory: str, recurse: bool = True) -> int:
    """
    Test all the examples in a directory.

    :param directory: the directory
    :param recurse: should we recurse into sub-directories (if any)?
    :returns: the total number of examples executed
    :raises TypeError: if `directory` is not a string or `recurse` is not a
        Boolean
    :raises ValueError: if executing the examples fails or if no examples were
        found

    >>> try:
    ...     check_examples_in_dir(None, True)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     check_examples_in_dir(1, True)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     check_examples_in_dir("x", None)
    ... except TypeError as te:
    ...     print(te)
    recurse should be an instance of bool but is None.

    >>> try:
    ...     check_examples_in_dir("y", 1)
    ... except TypeError as te:
    ...     print(te)
    recurse should be an instance of bool but is int, namely '1'.

    >>> from pycommons.io.temp import temp_dir
    >>> from contextlib import redirect_stdout
    >>> with temp_dir() as td, redirect_stdout(None) as rd:
    ...     try:
    ...         check_examples_in_dir(td, True)
    ...     except ValueError as ve:
    ...         s = str(ve)
    >>> print(s[:30])
    No examples found in directory

    >>> with temp_dir() as td, redirect_stdout(None) as rd:
    ...     pystring = "print('hello world!')"
    ...     td.resolve_inside("1.py").write_all_str(pystring)
    ...     td.resolve_inside("2.py").write_all_str(pystring)
    ...     tdx = td.resolve_inside("second")
    ...     tdx.ensure_dir_exists()
    ...     tdx.resolve_inside("1.py").write_all_str(pystring)
    ...     tdx.resolve_inside("2.py").write_all_str(pystring)
    ...     r1 = check_examples_in_dir(td, True)
    ...     r2 = check_examples_in_dir(td, False)
    >>> print(r1)
    4
    >>> print(r2)
    2

    >>> with temp_dir() as td, redirect_stdout(None) as rd:
    ...     pystring = "print('hello world!')"
    ...     td.resolve_inside("1.py").write_all_str(pystring)
    ...     pyerrstring = "1 / 0"
    ...     td.resolve_inside("2.py").write_all_str(pyerrstring)
    ...     tdx = td.resolve_inside("second")
    ...     res = ""
    ...     try:
    ...         check_examples_in_dir(td, True)
    ...     except ValueError as ve:
    ...         res = str(ve)
    >>> print(res[:20])
    Error when executing
    """
    # First, we resolve the directories
    if not isinstance(recurse, bool):
        raise type_error(recurse, "recurse", bool)
    examples_dir: Final[Path] = directory_path(directory)
    logger(f"Executing all examples in directory {examples_dir!r}.")

    files: Final[list[str]] = list(examples_dir.list_dir())
    count: int = list.__len__(files)
    total: int = 0
    logger(f"Got {count} potential files.")

    while count > 0:
        choice: int = randint(0, count - 1)  # noqa: S311
        current: Path = examples_dir.resolve_inside(files[choice])
        del files[choice]
        count -= 1

        if current.is_file():
            if current.endswith(".py"):  # if it is a python file
                chars: str = current.read_all_str()
                logger(f"Read {str.__len__(chars)} from file {files!r}.")
                compile_and_run(chars, current)
                total += 1
        elif recurse and current.is_dir() and (
                "pycache" not in current.lower()):
            total += check_examples_in_dir(current, True)

    if total <= 0:
        raise ValueError(f"No examples found in directory {directory!r}!")
    logger(f"Finished executing {total} examples in directory {directory!r}.")
    return total
