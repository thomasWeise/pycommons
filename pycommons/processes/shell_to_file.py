r"""
A tool for invoking shell commands and piping their output to files.

To do this more or less safely and reliably, we create a script that
invokes the original command. The script is created as temporary file
and will be deleted after the command completes.

>>> from pycommons.io.temp import temp_dir
>>> cmd = Command(("echo", "123"))

>>> with temp_dir() as td:
...     so = td.resolve_inside("so.txt")
...     se = td.resolve_inside("se.txt")
...     to_files(cmd, so, se).execute()
...     print(f"so: {so.read_all_str()}")
(None, None)
so: 123
<BLANKLINE>

>>> with temp_dir() as td:
...     so = td.resolve_inside("so.txt")
...     to_files(cmd, so, so).execute()
...     print(f"so: {so.read_all_str()}")
(None, None)
so: 123
<BLANKLINE>

>>> try:
...     to_files("a", "a", "b")
... except TypeError as te:
...     print(str(te)[:10])
command sh

>>> try:
...     to_files(cmd, 1, "b")
... except TypeError as te:
...     print(te)
stdout should be an instance of any in {None, str} but is int, namely 1.

>>> try:
...     to_files(cmd, "a", 1)
... except TypeError as te:
...     print(te)
stderr should be an instance of any in {None, str} but is int, namely 1.

>>> try:
...     to_files(cmd, None, None)
... except ValueError as ve:
...     print(ve)
Either stdout or stderr must be specified.
"""

import platform
from dataclasses import dataclass
from os import chmod
from stat import S_IRUSR, S_IWUSR, S_IXUSR  # nosec
from subprocess import list2cmdline  # nosec
from typing import Final, Iterable, Mapping

from pycommons.io.console import logger
from pycommons.io.path import Path
from pycommons.io.temp import temp_file
from pycommons.processes.shell import STREAM_IGNORE, Command
from pycommons.types import type_error

#: the internal operating system
_WINDOWS: Final[bool] = platform.system() == "Windows"


@dataclass(frozen=True, init=False, order=False, eq=False)
class __FileCommand(Command):
    """The internal file shell command data class."""

    #: the file to receive the standard output
    stdout_file: Path | None
    #: the file to receive the standard error output
    stderr_file: Path | None

    def __init__(self, command: str | Iterable[str],
                 working_dir: str | None = None,
                 timeout: int | None = 3600,
                 stdout: str | None = None,
                 stderr: str | None = None,
                 env: Mapping[str, str] | Iterable[tuple[
                     str, str]] | None = None) -> None:
        """
        Initialize the file-based command object.

        :param command: the command
        :param working_dir: the working directory
        :param timeout: the timeout, if any
        :param stdout: the file to capture the stdout, or `None` if
            stdout should be ignored
        :param stderr: the file to capture the stderr, or `None` if
            stderr should be ignored
        :param env: the environment variables to use
        """
        super().__init__(command, working_dir, timeout, None,
                         STREAM_IGNORE, STREAM_IGNORE, env)
        sof: Final[Path | None] = None if stdout is None else Path(stdout)
        sef: Path | None = None if stderr is None else Path(stderr)
        if (sof is not None) and (sef is not None) and (sof == sef):
            sef = sof
        object.__setattr__(self, "stdout_file", sof)
        object.__setattr__(self, "stderr_file", sef)

    def __str__(self) -> str:
        """
        Get the string representation of this command.

        :return: the command's string representation

        >>> cmd = Command(("echo", "123"))
        >>> str(to_files(cmd, "/tmp/x", "/tmp/x"))[-22:]
        "stdout+stderr>'/tmp/x'"
        >>> str(to_files(cmd, "/tmp/x", None))[-15:]
        "stdout>'/tmp/x'"
        >>> str(to_files(cmd, None, "/tmp/x"))[-15:]
        "stderr>'/tmp/x'"
        """
        old: str = super().__str__()
        so: Final[Path | None] = self.stdout_file
        se: Final[Path | None] = self.stderr_file
        if so is se:
            return f"{old}, stdout+stderr>{so!r}"
        if so is not None:
            old = f"{old}, stdout>{so!r}"
        return old if se is None else f"{old}, stderr>{se!r}"

    def execute(self, log_call: bool = True) -> tuple[None, None]:
        """
        Execute the command.

        :param log_call: shall we log the call?
        :return: always `(None, None)`
        """
        text: Final[list[str]] = [str(list2cmdline(self.command))]
        with temp_file(directory=self.working_dir,
                       suffix=".bat" if _WINDOWS else ".sh") as temp:
            if log_call:
                logger(f"Using temp file {temp!r} as execution "
                       f"wrapper for {self}.")
            if not _WINDOWS:
                text.insert(0, "#!/bin/bash\n")
            sof: Final[Path | None] = self.stdout_file
            sef: Final[Path | None] = self.stderr_file
            if sof is not None:
                text.append(f' 1>"{sof}"')
            if sef is not None:
                text.append(" 2>&1" if sef is sof else f' 2>"{sef}"')
            temp.write_all_str("".join(text))
            if not _WINDOWS:
                chmod(temp, S_IRUSR | S_IWUSR | S_IXUSR)
            Command(command=temp,
                    working_dir=self.working_dir,
                    timeout=self.timeout,
                    stdin=None,
                    stderr=STREAM_IGNORE,
                    stdout=STREAM_IGNORE,
                    env=self.env).execute(log_call)
            if sof is not None:
                sof.enforce_file()
            if sef is not None:
                sef.enforce_file()
        return None, None


def to_files(command: Command, stdout: str | None,
             stderr: str | None) -> Command:
    """
    Take an existing command and forward its stdout and/or stderr to files.

    Currently, providing text as standard input is not supported.
    You can provide either different or the same file for the standard output
    and standard error. If the same file is provided, then both streams will
    be merged into that file.
    Either way, the files you provide will be created and overwritten during
    the command execution.
    Notice that whatever original settings for standard error and standard
    output you provided in the original
    :class:`~pycommons.processes.shell.Command` instance `command` will be
    ignored.

    :param command: the command
    :param stdout: the file to capture the stdout, or `None` if stdout
        should be ignored
    :param stderr: the file to capture the stderr, or `None` if stderr
        should be ignored
    :return: the new command
    """
    if not isinstance(command, Command):
        raise type_error(command, "command", Command)
    if command.stdin is not None:
        raise ValueError("Stdin is not supported for file commands.")
    if (stdout is not None) and (not isinstance(stdout, str)):
        raise type_error(stdout, "stdout", (str, None))
    if (stderr is not None) and (not isinstance(stderr, str)):
        raise type_error(stderr, "stderr", (str, None))
    if (stdout is None) and (stderr is None):
        raise ValueError("Either stdout or stderr must be specified.")
    return __FileCommand(command=command.command,
                         working_dir=command.working_dir,
                         timeout=command.timeout,
                         stdout=stdout,
                         stderr=stderr,
                         env=command.env)
