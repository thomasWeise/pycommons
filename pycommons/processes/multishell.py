r"""
A tool for running multiple commands in parallel.

>>> from pycommons.processes.shell import STREAM_CAPTURE
>>> c1 = Command(("echo", "123"), stdout=STREAM_CAPTURE)
>>> c2 = Command(("echo", "abc"), stdout=STREAM_CAPTURE)

>>> multi_execute((c1, c2), True)
(('123\n', None), ('abc\n', None))

>>> multi_execute((c1, ), False)
(('123\n', None),)

>>> multi_execute((c1, c2, c2, c2), True)
(('123\n', None), ('abc\n', None), ('abc\n', None), ('abc\n', None))
"""

from threading import Thread
from typing import Any, Final, Iterable

from pycommons.io.console import logger
from pycommons.processes.shell import Command
from pycommons.types import type_error


def __exec(command: Command, idx: int,
           out: list[tuple[str | None, str | None]],
           log_call: bool) -> None:
    """
    Perform the actual execution of a command.

    :param command: the command to execute
    :param idx: the index of the command to execute
    :param out: the output list to receive the command output
    :param log_call: shall the call be logged?
    """
    out[idx] = command.execute(log_call=log_call)


def multi_execute(commands: Iterable[Command], log: bool = True) \
        -> tuple[tuple[str | None, str | None], ...]:
    r"""
    Execute multiple commands in parallel.

    :param commands: the iterable of the commands to execute
    :param log: shall the execution state be logged?
    :returns: the results of the commands

    >>> from pycommons.processes.shell import STREAM_CAPTURE
    >>> c1 = Command(("echo", "123"), stdout=STREAM_CAPTURE)
    >>> c2 = Command(("echo", "abc"), stdout=STREAM_CAPTURE)

    >>> multi_execute((), False)
    ()
    >>> multi_execute((), True)
    ()

    >>> multi_execute((c1, ), False)
    (('123\n', None),)
    >>> multi_execute((c1, ), True)
    (('123\n', None),)

    >>> multi_execute((c1, c2), False)
    (('123\n', None), ('abc\n', None))
    >>> multi_execute((c1, c2), True)
    (('123\n', None), ('abc\n', None))

    >>> multi_execute((c1, c2, c2, c2), True)
    (('123\n', None), ('abc\n', None), ('abc\n', None), ('abc\n', None))
    >>> multi_execute((c1, c2, c2, c2), False)
    (('123\n', None), ('abc\n', None), ('abc\n', None), ('abc\n', None))

    >>> try:
    ...     multi_execute(1)
    ... except TypeError as te:
    ...     print(te)
    commands should be an instance of typing.Iterable but is int, namely 1.

    >>> try:
    ...     multi_execute((c1, c2), 3)
    ... except TypeError as te:
    ...     print(te)
    log should be an instance of bool but is int, namely 3.

    >>> try:
    ...     multi_execute(("x", ))
    ... except TypeError as te:
    ...     print(str(te)[:20])
    commands[0] should b
    """
    if not isinstance(commands, Iterable):
        raise type_error(commands, "commands", Iterable)
    if not isinstance(log, bool):
        raise type_error(log, "log", bool)

    threads: Final[list[Thread]] = []
    out: list[tuple[str | None, str | None]] = []
    kwargs: Final[dict[str, Any]] = {"log_call": log, "out": out}
    command: Command | None = None
    for idx, command in enumerate(commands):
        if not isinstance(command, Command):
            raise type_error(command, f"commands[{idx}]", Command)
        kw = dict(kwargs)
        kw["command"] = command
        kw["idx"] = idx
        out.append((None, None))
        threads.append(Thread(target=__exec, kwargs=kw))

    llen: Final[int] = list.__len__(threads)
    if llen <= 0:
        if log:
            logger("No command to execute, quitting.")
        return ()
    if llen <= 1:
        if log:
            logger("Only one command, not using threads.")
        if command is None:
            raise ValueError("Huh?")
        return (command.execute(log_call=False), )

    if log:
        logger(f"Executing {llen} processes by using threads.")
    for thread in threads:
        thread.start()
    if log:
        logger(f"All {llen} processes have started.")
    for thread in threads:
        thread.join()
    if log:
        logger(f"All {llen} processes have completed.")
    return tuple(out)
