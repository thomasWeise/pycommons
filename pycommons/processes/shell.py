"""The tool for invoking shell commands."""

import subprocess  # nosec
from dataclasses import dataclass
from os import getcwd
from typing import Callable, Final, Iterable

from pycommons.io.console import logger
from pycommons.io.path import UTF8, Path, directory_path
from pycommons.types import check_int_range, type_error

#: ignore the given stream
STREAM_IGNORE: Final[int] = 0
#: forward given stream to the same stream of this process
STREAM_FORWARD: Final[int] = 1
#: capture the given stream
STREAM_CAPTURE: Final[int] = 2


#: the stream mode to string converter
_SM: Final[Callable[[int], str]] = {
    STREAM_IGNORE: " ignored",
    STREAM_FORWARD: " forwarded",
    STREAM_CAPTURE: " captured",
}.get


@dataclass(frozen=True, init=False, order=False, eq=False)
class Command:
    """
    A class that represents a command that can be executed.

    >>> c = Command("test")
    >>> c.command
    ('test',)
    >>> c.working_dir.is_dir()
    True
    >>> c.timeout
    3600

    >>> d = Command(("test", "b"))
    >>> d.command
    ('test', 'b')
    >>> d.working_dir == c.working_dir
    True
    >>> d.timeout == c.timeout
    True

    >>> e = Command(("", "test", " b", " "))
    >>> e.command == d.command
    True
    >>> e.working_dir == c.working_dir
    True
    >>> e.timeout == c.timeout
    True

    >>> try:
    ...     Command(1)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    command should be an instance of any in {str, typi

    >>> try:
    ...     Command([1])
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     Command(["x", 1])
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     Command([])
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [].

    >>> try:
    ...     Command([""])
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [''].

    >>> try:
    ...     Command("")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [''].

    >>> Command("x", working_dir=Path(__file__).up(1)).command
    ('x',)

    >>> try:
    ...     Command("x", working_dir=1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     Command("x", working_dir=Path(__file__))
    ... except ValueError as ve:
    ...     print(str(ve)[-30:])
    does not identify a directory.

    >>> Command("x", timeout=23).timeout
    23

    >>> try:
    ...     Command("x", timeout=1.2)
    ... except TypeError as te:
    ...     print(te)
    timeout should be an instance of int but is float, namely '1.2'.

    >>> try:
    ...     Command("x", timeout=None)
    ... except TypeError as te:
    ...     print(te)
    timeout should be an instance of int but is None.

    >>> try:
    ...     Command("x", timeout=0)
    ... except ValueError as ve:
    ...     print(ve)
    timeout=0 is invalid, must be in 1..1000000.

    >>> try:
    ...     Command("x", timeout=1_000_001)
    ... except ValueError as ve:
    ...     print(ve)
    timeout=1000001 is invalid, must be in 1..1000000.

    >>> try:
    ...     Command("x", stdin=1_000_001)
    ... except TypeError as te:
    ...     print(str(te)[:49])
    stdin should be an instance of any in {None, str}
    """

    #: the command line.
    command: tuple[str, ...]
    #: the working directory
    working_dir: Path
    #: the timeout in seconds, after which the process will be terminated
    timeout: int
    #: the data to be written to stdin
    stdin: str | None
    #: how to handle the standard output stream
    stdout: int
    #: how to handle the standard error stream
    stderr: int

    def __init__(self, command: str | Iterable[str],
                 working_dir: str | None = None,
                 timeout: int | None = 3600,
                 stdin: str | None = None,
                 stdout: int = STREAM_IGNORE,
                 stderr: int = STREAM_IGNORE) -> None:
        """
        Create the command.

        :param command: the command string or iterable
        :param working_dir: the working directory
        :param timeout: the timeout
        :param stdin: a string to be written to stdin, or `None`
        :param stdout: how to handle the standard output stream
        :param stderr: how to handle the standard error stream
        """
        if isinstance(command, str):
            command = [command]
        elif not isinstance(command, Iterable):
            raise type_error(command, "command", (str, Iterable))
        object.__setattr__(self, "command", tuple(
            s for s in map(str.strip, command) if str.__len__(s) > 0))
        if tuple.__len__(self.command) <= 0:
            raise ValueError(f"Invalid command {command!r}.")

        object.__setattr__(self, "working_dir", directory_path(
            getcwd() if working_dir is None else working_dir))

        object.__setattr__(self, "timeout", check_int_range(
            timeout, "timeout", 1, 1_000_000))

        if (stdin is not None) and (not isinstance(stdin, str)):
            raise type_error(stdin, "stdin", (str, None))
        object.__setattr__(self, "stdin", stdin)

        object.__setattr__(self, "stdout", check_int_range(
            stdout, "stdout", 0, 2))
        object.__setattr__(self, "stderr", check_int_range(
            stderr, "stderr", 0, 2))

    def __str__(self) -> str:
        """
        Get the string representation of this command.

        :return: A string representing this command

        >>> str(Command("a"))[-50:]
        ' with no stdin, stdout ignored, and stderr ignored'
        >>> str(Command("x"))[:11]
        "('x',) in '"
        >>> "with 3 chars of stdin" in str(Command("x", stdin="123"))
        True
        """
        si: str = "no" if self.stdin is None \
            else f"{str.__len__(self.stdin)} chars of"
        return (f"{self.command!r} in {self.working_dir!r} for {self.timeout}"
                f"s with {si} stdin, stdout{_SM(self.stdout)}, and "
                f"stderr{_SM(self.stderr)}")

    def execute(self, log_call: bool = True) -> tuple[str | None, str | None]:
        r"""
        Execute the given process.

        :param log_call: should the call be logged?
        :return: a tuple with the standard output and standard error, which
            are only not `None` if they were supposed to be captured
        :raises TypeError: if any argument has the wrong type
        :raises ValueError: if execution of the process failed

        >>> Command(("echo", "123"), stdout=STREAM_CAPTURE).execute(False)
        ('123\n', None)

        >>> Command(("echo", "", "123"), stdout=STREAM_CAPTURE).execute(False)
        ('123\n', None)

        >>> from contextlib import redirect_stdout
        >>> with redirect_stdout(None):
        ...     s = Command(("echo", "123"), stdout=STREAM_CAPTURE).execute()
        >>> print(s)
        ('123\n', None)

        >>> Command("cat", stdin="test", stdout=STREAM_CAPTURE).execute(False)
        ('test', None)

        >>> Command("cat", stdin="test").execute(False)
        (None, None)

        >>> try:
        ...     with redirect_stdout(None):
        ...         Command(("ping", "blabla!")).execute(True)
        ... except ValueError as ve:
        ...     ss = str(ve)
        ...     print(ss[:20] + " ... " + ss[-22:])
        ('ping', 'blabla!')  ...  yields return code 2.

        >>> try:
        ...     with redirect_stdout(None):
        ...         Command(("ping", "www.example.com", "-i 20"),
        ...                 timeout=1).execute(True)
        ... except ValueError as ve:
        ...     print("timed out after" in str(ve))
        True

        >>> try:
        ...     Command("x").execute(None)
        ... except TypeError as te:
        ...     print(te)
        log_call should be an instance of bool but is None.

        >>> try:
        ...     Command("x").execute(1)
        ... except TypeError as te:
        ...     print(te)
        log_call should be an instance of bool but is int, namely '1'.

        >>> with redirect_stdout(None):
        ...     r = Command(("echo", "1"), stderr=STREAM_CAPTURE).execute(
        ...             True)
        >>> r
        (None, '')
        """
        if not isinstance(log_call, bool):
            raise type_error(log_call, "log_call", bool)
        message: Final[str] = str(self)
        if log_call:
            logger(f"Now invoking {message}.")

        arguments: Final[dict[str, str | Iterable[str] | bool | int]] = {
            "args": self.command,
            "check": False,
            "text": True,
            "timeout": self.timeout,
            "cwd": self.working_dir,
            "errors": "strict",
            "encoding": UTF8,
        }

        if self.stdin is not None:
            arguments["input"] = self.stdin

        arguments["stdout"] = 1 if self.stdout == STREAM_FORWARD else (
            subprocess.PIPE if self.stdout == STREAM_CAPTURE
            else subprocess.DEVNULL)
        arguments["stderr"] = 2 if self.stderr == STREAM_FORWARD else (
            subprocess.PIPE if self.stderr == STREAM_CAPTURE
            else subprocess.DEVNULL)

        try:
            # noqa # nosemgrep # pylint: disable=W1510 # type: ignore
            ret: Final[subprocess.CompletedProcess] = \
                subprocess.run(**arguments)  # type: ignore # nosec # noqa
        except (TimeoutError, subprocess.TimeoutExpired) as toe:
            if log_call:
                logger(f"Failed executing {self} with timeout {toe}.")
            raise ValueError(f"{message} timed out: {toe}.") from toe

        returncode: Final[int] = ret.returncode
        if returncode != 0:
            if log_call:
                logger(f"Failed executing {self}: got return"
                       f" code {returncode}.")
            raise ValueError(f"{message} yields return code {returncode}.")

        stdout: str | None = None
        if self.stdout == STREAM_CAPTURE:
            stdout = ret.stdout
            if not isinstance(stdout, str):
                raise type_error(stdout, f"stdout of {self}", stdout)

        stderr: str | None = None
        if self.stderr == STREAM_CAPTURE:
            stderr = ret.stderr
            if not isinstance(stderr, str):
                raise type_error(stderr, f"stderr of {self}", stderr)

        if log_call:
            capture: str = ""
            if stdout is not None:
                capture = f", captured {str.__len__(stdout)} chars of stdout"
            if stderr is not None:
                capture = f"{capture} and " if str.__len__(capture) > 0 \
                    else ", captured "
                capture = f"{capture}{str.__len__(stderr)} chars of stderr"
            logger(f"Finished executing {self} with return code 0{capture}.")

        return stdout, stderr
