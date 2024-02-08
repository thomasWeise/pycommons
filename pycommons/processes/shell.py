"""The tool for invoking shell commands."""

import subprocess  # nosec
from os import getcwd
from typing import Callable, Final, Iterable, Mapping

from pycommons.io.console import logger
from pycommons.io.path import Path
from pycommons.types import check_int_range, type_error


def exec_text_process(
        command: str | Iterable[str],
        timeout: int = 3600,
        cwd: str | None = None,
        wants_stdout: bool = False,
        stdin: str | None = None,
        log_call: bool = True,
        log_stdin: bool = False,
        log_stdout: bool = True,
        log_stderr: bool = True,
        exit_code_to_str: Mapping[int, str] | None = None,
        check_stderr: Callable[[str], str | None] | None = None) \
        -> str | None:
    r"""
    Execute a text-based command.

    The command is executed and its stdout and stderr and return code are
    captured. If the command had a non-zero exit code, an exception is thrown.
    The command itself, as well as the parameters are logged if `log_call` is
    `True`. If `wants_stdout` is `True`, the command's stdout is returned.
    Otherwise, `None` is returned.
    All spaces are stripped from all command strings and all command strings
    that become empty this way are discarded.

    :param command: the command to execute, either a single string or a
        sequence of strings. All white space will be stripped from the strings
        and all strings that then become empty are dropped.
    :param timeout: the timeout in seconds, must be less than 1000 hours and
        at least 1 second
    :param cwd: the directory to run inside, or `None` if not specified, in
        which case the program will be executed in the current work directory
        (see :func:`os.getcwd`)
    :param wants_stdout: if `True`, the text contents of stdout should be
        returned; otherwise, i.e., if `False`, `None` is returned
    :param exit_code_to_str: an optional map converting return codes that are
        different from `0` to strings
    :param check_stderr: provide an error message if any error is found in
        stderr, or `None` or the empty string otherwise
    :param stdin: optional data to be written to stdin, `None` to write
        nothing to the program's stdin
    :param log_call: should any log output be generated?
    :param log_stdin: should the data passed to stdin be logged?
    :param log_stdout: should the data read from stdout be logged?
    :param log_stderr: should the data read from stderr be logged?

    >>> exec_text_process(("echo", "123"), wants_stdout=True, log_call=False)
    '123\n'

    >>> exec_text_process(("echo", " ", "123"), wants_stdout=True,
    ...                   log_call=False)
    '123\n'

    >>> from contextlib import redirect_stdout
    >>> from io import StringIO
    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     exec_text_process(("echo", "123"), wants_stdout=False)
    >>> print(s.getvalue().strip().split("\n")[2:])
    ['Obtained return value 0.', '', 'stdout:', '123']

    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     exec_text_process("cat", stdin="tester",
    ...                       wants_stdout=False)
    >>> print(s.getvalue().strip().split("\n")[2:])
    ['Obtained return value 0.', '', 'stdout:', 'tester']

    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     exec_text_process("cat", stdin="tester",
    ...                       wants_stdout=False, log_stdin=True)
    >>> print(s.getvalue().strip().split("\n")[2:-3])
    ['Obtained return value 0.', '', 'stdin:', 'tester']

    >>> s = StringIO()
    >>> try:
    ...     with redirect_stdout(s):
    ...         exec_text_process(("ping", "blabla!"),
    ...                           wants_stdout=False,
    ...                           exit_code_to_str={2: "bla!"})
    ... except ValueError as ve:
    ...     ss = str(ve)
    ...     print(ss[:33] + " ... " + ss[-33:])
    Execution of 'ping' 'blabla!' in  ... return code 2 with meaning 'bla!'
    >>> print("\n".join(s.getvalue().strip().split("\n")[2:]))
    Obtained return value 2.
    Meaning of return value: 'bla!'
    <BLANKLINE>
    stderr:
    ping: blabla!: Name or service not known

    >>> s = StringIO()
    >>> try:
    ...     with redirect_stdout(s):
    ...         exec_text_process(("ping", "blabla!"),
    ...                           wants_stdout=False,
    ...                           exit_code_to_str={2: " "})
    ... except ValueError as ve:
    ...     ss = str(ve)
    ...     print(ss[:33] + " ... " + ss[-22:])
    Execution of 'ping' 'blabla!' in  ... led with return code 2
    >>> print("\n".join(s.getvalue().strip().split("\n")[2:]))
    Obtained return value 2.
    <BLANKLINE>
    stderr:
    ping: blabla!: Name or service not known

    >>> s = StringIO()
    >>> try:
    ...     with redirect_stdout(s):
    ...         exec_text_process(
    ...             ("ping", "blabla!"),
    ...             wants_stdout=False,
    ...             exit_code_to_str={2: "bla!"},
    ...             check_stderr=lambda i: "Oh" if "service" in i else "Ah")
    ... except ValueError as ve:
    ...     ss = str(ve)
    ...     print(ss[:33] + " ... " + ss[-33:])
    Execution of 'ping' 'blabla!' in  ... ning 'bla!' leading to error 'Oh'
    >>> print("\n".join(s.getvalue().strip().split("\n")[2:-3]))
    Obtained return value 2.
    Meaning of return value: 'bla!'
    <BLANKLINE>
    stderr:
    ping: blabla!: Name or service not known

    >>> s = StringIO()
    >>> try:
    ...     with redirect_stdout(s):
    ...         exec_text_process(
    ...             ("ping", "blabla!"),
    ...             wants_stdout=False,
    ...             exit_code_to_str={2: "bla!"},
    ...             check_stderr=lambda i: "" if "service" in i else "")
    ... except ValueError as ve:
    ...     ss = str(ve)
    ...     print(ss[:33] + " ... " + ss[-33:])
    Execution of 'ping' 'blabla!' in  ... return code 2 with meaning 'bla!'
    >>> print("\n".join(s.getvalue().strip().split("\n")[2:-3]))
    Obtained return value 2.
    Meaning of return value: 'bla!'

    >>> try:
    ...     exec_text_process(command=1)
    ... except TypeError as te:
    ...     print(te)
    command should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     exec_text_process(command=("echo", 1))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     exec_text_process(command="")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [] mapping to ''!

    >>> try:
    ...     exec_text_process(command=" ")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [] mapping to ''!

    >>> try:
    ...     exec_text_process(command=(" ", "   ", ))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid command [] mapping to ''!


    >>> try:
    ...     exec_text_process("ls", timeout=1.3)
    ... except TypeError as te:
    ...     print(te)
    timeout should be an instance of int but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", stdin=1.3)
    ... except TypeError as te:
    ...     print(te)
    stdin should be an instance of str but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", log_call=1.3)
    ... except TypeError as te:
    ...     print(te)
    log_call should be an instance of bool but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", log_stdin=1.3)
    ... except TypeError as te:
    ...     print(te)
    log_stdin should be an instance of bool but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", log_stdout=1.3)
    ... except TypeError as te:
    ...     print(te)
    log_stdout should be an instance of bool but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", log_stderr=1.3)
    ... except TypeError as te:
    ...     print(te)
    log_stderr should be an instance of bool but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", wants_stdout=1.3)
    ... except TypeError as te:
    ...     print(te)
    wants_stdout should be an instance of bool but is float, namely '1.3'.

    >>> try:
    ...     exec_text_process("ls", exit_code_to_str=1.3)
    ... except TypeError as te:
    ...     print(str(te)[:-28])
    exit_code_to_str should be an instance of any in {None, typing.Mapping}

    >>> try:
    ...     exec_text_process("ls", check_stderr=1.3)
    ... except TypeError as te:
    ...     print(str(te)[:-24])
    check_stderr should be an instance of any in {None} or a callable but
    """
    if isinstance(command, str):
        command = [command]
    if not isinstance(command, Iterable):
        raise type_error(command, "command", Iterable)
    check_int_range(timeout, "timeout", 1, 3600_000)
    if not isinstance(log_call, bool):
        raise type_error(log_call, "log_call", bool)
    if not isinstance(log_stdin, bool):
        raise type_error(log_stdin, "log_stdin", bool)
    if not isinstance(log_stdout, bool):
        raise type_error(log_stdout, "log_stdout", bool)
    if not isinstance(log_stderr, bool):
        raise type_error(log_stderr, "log_stderr", bool)
    if not isinstance(wants_stdout, bool):
        raise type_error(wants_stdout, "wants_stdout", bool)
    if (exit_code_to_str is not None) and (
            not isinstance(exit_code_to_str, Mapping)):
        raise type_error(exit_code_to_str, "exit_code_to_str", (
            Mapping, None))
    if (check_stderr is not None) and (not callable(check_stderr)):
        raise type_error(check_stderr, "check_stderr", (
            type(None), ), call=True)

    cmd = [s for s in map(str.strip, command) if str.__len__(s) > 0]
    execstr: str = " ".join(map(repr, cmd))
    if (list.__len__(cmd) <= 0) or (str.__len__(execstr) <= 0):
        raise ValueError(f"Invalid command {cmd!r} mapping to {execstr!r}!")

    wd = Path.directory(getcwd() if cwd is None else cwd)
    execstr = f"{execstr} in {wd!r}"

    arguments: Final[dict[str, str | list[str] | bool | int]] = {
        "args": cmd,
        "check": False,
        "text": True,
        "timeout": timeout,
        "capture_output": True,
        "cwd": wd,
    }

    if stdin is not None:
        if not isinstance(stdin, str):
            raise type_error(stdin, "stdin", str)
        arguments["input"] = stdin

    if log_call:
        logger(f"Now invoking {execstr}.")
    # noqa # nosemgrep # pylint: disable=W1510 # type: ignore
    ret: Final[subprocess.CompletedProcess] = \
        subprocess.run(**arguments)  # type: ignore # nosec # noqa
    returncode: Final[int] = ret.returncode

    logging: list[str] | None = [
        f"Finished executing {execstr}.",
        f"Obtained return value {returncode}."] if log_call else None

    meaning: str | None = None
    if (returncode != 0) and exit_code_to_str:
        meaning = exit_code_to_str.get(returncode, None)
        if meaning is not None:
            meaning = str.strip(meaning)
            if str.__len__(meaning) > 0:
                if logging is not None:
                    logging.append(f"Meaning of return value: {meaning!r}")
            else:
                meaning = None

    if log_stdin and (stdin is not None) and (logging is not None):
        logging.append(f"\nstdin:\n{stdin}")

    stdout = ret.stdout
    if ((stdout is not None) and (str.__len__(stdout) > 0)
            and log_stdout and (logging is not None)):
        logging.append(f"\nstdout:\n{stdout}")

    stderr = ret.stderr
    del ret
    error_msg: str | None = None
    if stderr is not None:
        if str.__len__(stderr) > 0:
            if log_stderr and (logging is not None):
                logging.append(f"\nstderr:\n{stderr}")
            if callable(check_stderr):
                error_msg = check_stderr(stderr)
                if error_msg is not None:
                    error_msg = str.strip(error_msg)
                    if str.__len__(error_msg) <= 0:
                        error_msg = None
                    elif logging is not None:
                        logging.append(f"\nerror message: {execstr!r}")
        del stderr
    if logging is not None:
        logger("\n".join(logging))
        del logging

    if (returncode != 0) or (error_msg is not None):
        execstr = (f"Execution of {execstr} failed with "
                   f"return code {returncode}")
        if meaning is not None:
            execstr = f"{execstr} with meaning {meaning!r}"
        if error_msg is not None:
            execstr = f"{execstr} leading to error {error_msg!r}"
        raise ValueError(execstr)

    return stdout if wants_stdout else None
