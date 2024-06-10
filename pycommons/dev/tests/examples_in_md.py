"""Test all the `Python` example code in a markdown file."""
from os import getcwd
from typing import Final

from pycommons.dev.tests.compile_and_run import compile_and_run
from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path, file_path


def check_examples_in_md(file: str) -> None:
    """
    Test all the example Python codes in a markdown file.

    :param file: the file
    :raises TypeError: if `file` is not a string
    :raises ValueError: if `file` is empty or otherwise invalid

    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     check_examples_in_md(file_path(file_path(__file__).up(
    ...         4).resolve_inside("README.md")))

    >>> try:
    ...     check_examples_in_md(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     check_examples_in_md(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     check_examples_in_md("")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not be empty.

    >>> try:
    ...     check_examples_in_md("/")
    ... except ValueError as ve:
    ...     print(ve)
    Path '/' does not identify a file.
    """
    # First, we load the README.md file as a single string
    readme: Final[Path] = file_path(file)
    logger(f"Executing all examples from file {readme!r}.")
    text: Final[str] = readme.read_all_str()
    logger(f"Read {str.__len__(text)} characters from {readme!r}.")

    i2: int = -1
    # All examples start and end with ``` after a newline.
    mark1: Final[str] = "\n```"
    mark2: Final[str] = "python"  # python code starts with ```python

    wd: Final[str] = directory_path(getcwd())  # current working directory
    logger(f"Current working directory is {wd!r}.")
    example_cnt: int = 0

    while True:
        # First, find the starting mark.
        i2 += 1
        i1 = text.find(mark1, i2)
        if i1 <= i2:
            break  # no starting mark anymore: done
        i1 += len(mark1)
        i2 = text.find(mark1, i1)
        if i2 <= i1:
            raise ValueError(f"No end mark for start mark {mark1!r} "
                             f"at character {i1}?")

        orig_fragment: str = text[i1:i2]  # get the fragment
        fragment: str = str.strip(orig_fragment)
        if str.__len__(fragment) <= 0:
            raise ValueError(f"Empty fragment {orig_fragment!r} from "
                             f"{i1} to {i2}?")
        i2 += str.__len__(mark1)
        if fragment.startswith(mark2):  # it is a python fragment
            i3 = fragment.find("\n")
            if i3 < str.__len__(mark2):
                raise ValueError("Did not find newline in stripped "
                                 f"fragment {orig_fragment!r}?")
            compile_and_run(fragment[i3 + 1:], f"{readme}:{i1}:{i2}")
            example_cnt += 1

    if example_cnt <= 0:
        raise ValueError(f"No example found in {readme!r}.")
    logger(
        f"Successfully executed all {example_cnt} examples from {readme!r}.")
