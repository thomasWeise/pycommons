"""The `logger` routine for writing a log string to stdout."""
import datetime
from contextlib import AbstractContextManager, nullcontext
from typing import Callable, Final

from pycommons.processes.caller import is_doc_test

#: the "now" function
__DTN: Final[Callable[[], datetime.datetime]] = datetime.datetime.now


def logger(message: str, note: str = "",
           lock: AbstractContextManager = nullcontext(),
           do_print: bool = not is_doc_test()) -> None:
    """
    Write a message to the console log.

    The line starts with the current date and time, includes the note, and
    then the message string after an ": ".
    This function can use a `lock` context to prevent multiple processes or
    threads to write to the console at the same time.

    :param message: the message
    :param note: a note to put between the time and the message
    :param lock: the lock to prevent multiple threads to write log
        output at the same time
    :param do_print: really print the output, by default `False` if this
        method is called from a "doctest", `True` otherwise

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> sio = StringIO()
    >>> dt1 = datetime.datetime.now()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", do_print=True)
    >>> line = sio.getvalue().strip()
    >>> print(line[26:])
    : hello world!
    >>> dt2 = datetime.datetime.now()
    >>> dtx = datetime.datetime.strptime(line[:26], "%Y-%m-%d %H:%M:%S.%f")
    >>> dt1 <= dtx <= dt2
    True

    >>> sio = StringIO()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", "note", do_print=True)
    >>> line = sio.getvalue().strip()
    >>> print(line[26:])
    note: hello world!

    >>> from contextlib import AbstractContextManager
    >>> class T:
    ...     def __enter__(self):
    ...         print("x")
    ...     def __exit__(self, exc_type, exc_val, exc_tb):
    ...         print("y")

    >>> sio = StringIO()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", "", T(), do_print=True)
    >>> sio.seek(0)
    0
    >>> lines = sio.readlines()
    >>> print(lines[0].rstrip())
    x
    >>> print(lines[1][26:].rstrip())
    : hello world!
    >>> print(lines[2].rstrip())
    y

    >>> sio = StringIO()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", "note", T(), do_print=True)
    >>> sio.seek(0)
    0
    >>> lines = sio.readlines()
    >>> print(lines[0].rstrip())
    x
    >>> print(lines[1][26:].rstrip())
    note: hello world!
    >>> print(lines[2].rstrip())
    y

    >>> logger("hello world")  # not printed in doctests
    >>> logger("hello world", do_print=False)  # not printed anyway
    """
    if do_print:
        text: Final[str] = f"{__DTN()}{note}: {message}"
        with lock:
            print(text, flush=True)  # noqa
