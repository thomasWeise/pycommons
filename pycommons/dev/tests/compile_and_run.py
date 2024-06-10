"""Compile and run some Python code for testing purposes."""

from os import chdir, getcwd
from typing import Final

from pycommons.io.console import logger
from pycommons.io.path import directory_path
from pycommons.io.temp import temp_dir


def compile_and_run(code: str, source: str) -> None:
    """
    Compile and run some code for testing purposes.

    This method first checks the types of its parameters.
    It then performs some  superficial sanity checks on `code`.
    Then, it changes the working directory to a temporary folder which is
    deleted after all work is done.
    It then compiles and, if that was successful, executes the code fragment.
    Then working directory is changed back to the original directory and the
    temporary directory is deleted.

    :param code: the code to be compiled and run
    :param source: the source of the code
    :raises TypeError: if `code` or `source` are not strings
    :raises ValueError: if any parameter has an invalid value
        or if the code execution fails

    >>> wd = getcwd()
    >>> try:
    ...     compile_and_run(None, "bla")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run(1, "bla")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("x=5", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("x=5", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run(None, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("x=5", "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid source: ''.

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("x=5", " ")
    ... except ValueError as ve:
    ...     print(ve)
    Source cannot be only white space, but ' ' is.

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("", "x")
    ... except ValueError as ve:
    ...     print(ve)
    Code '' from 'x' is empty?

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run(" ", "x")
    ... except ValueError as ve:
    ...     print(ve)
    Code ' ' from 'x' consists of only white space!

    >>> wd == getcwd()
    True

    >>> try:
    ...     compile_and_run("ä ", "x")
    ... except ValueError as ve:
    ...     print(ve)
    Code 'ä ' from 'x' contains non-ASCII characters.

    >>> wd == getcwd()
    True

    >>> from contextlib import redirect_stdout
    >>> try:
    ...     with redirect_stdout(None):
    ...         compile_and_run("<>-sdf/%'!234", "src")
    ... except ValueError as ve:
    ...     print(ve)
    Error when compiling 'src'.

    >>> wd == getcwd()
    True

    >>> try:
    ...     with redirect_stdout(None):
    ...         compile_and_run("1/0", "src")
    ... except ValueError as ve:
    ...     print(ve)
    Error when executing 'src'.

    >>> wd == getcwd()
    True

    >>> with redirect_stdout(None):
    ...     compile_and_run("print(1)", "src")

    >>> wd == getcwd()
    True
    """
    if str.__len__(source) <= 0:
        raise ValueError(f"Invalid source: {source!r}.")
    use_source: Final[str] = str.strip(source)
    if str.__len__(use_source) <= 0:
        raise ValueError(
            f"Source cannot be only white space, but {source!r} is.")

    if str.__len__(code) <= 0:
        raise ValueError(f"Code {code!r} from {source!r} is empty?")
    use_code: Final[str] = str.rstrip(code)
    code_len: Final[int] = str.__len__(use_code)
    if code_len <= 0:
        raise ValueError(
            f"Code {code!r} from {source!r} consists of only white space!")

    if not str.isascii(use_code):
        raise ValueError(
            f"Code {code!r} from {source!r} contains non-ASCII characters.")

    working_dir: Final[str] = directory_path(getcwd())
    logger(f"Original working directory is {working_dir!r}.")

    with temp_dir() as td:
        logger(f"Changing working directory to temp dir {td!r} to "
               f"process source {use_source!r}.")
        try:
            chdir(td)
            try:
                compiled = compile(  # noqa # nosec
                    use_code, filename=use_source,  # noqa # nosec
                    mode="exec", dont_inherit=True)  # noqa # nosec
            except BaseException as be:  # noqa: B036
                raise ValueError(
                    f"Error when compiling {use_source!r}.") from be
            logger(f"Successfully compiled, now executing {use_source!r}.")
            try:
                exec(compiled, {})  # pylint: disable = W0122 # noqa # nosec
            except BaseException as be:  # noqa: B036
                raise ValueError(
                    f"Error when executing {use_source!r}.") from be
        finally:
            chdir(working_dir)
            logger(f"Changed working directory back to {working_dir!r}")
    logger(f"Successfully finished executing code from {use_source!r}.")
