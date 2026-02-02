"""The `logger` routine for writing a log string to stdout."""
import datetime
from typing import Callable, Final

from pycommons.processes.caller import is_doc_test

#: the "now" function
__DTN: Final[Callable[[], datetime.datetime]] = datetime.datetime.now


def logger(message: str, note: str = "",
           do_print: bool = not is_doc_test()) -> None:
    """
    Write a message to the console log.

    The line starts with the current date and time, includes the note, and
    then the message string after an ": ".
    This function can use a `lock` context to prevent multiple processes or
    threads to write to the console at the same time.

    :param message: the message
    :param note: a note to put between the time and the message
    :param do_print: really print the output, by default `False` if this
        method is called from a "doctest", `True` otherwise

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> sio = StringIO()
    >>> dt1 = datetime.datetime.now()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", do_print=True)
    >>> line = sio.getvalue().strip()
    >>> print(line[line.index(" ", line.index(" ") + 1) + 1:])
    hello world!
    >>> dt2 = datetime.datetime.now()
    >>> dtx = datetime.datetime.strptime(line[:26], "%Y-%m-%d %H:%M:%S.%f")
    >>> dt1 <= dtx <= dt2
    True

    >>> sio = StringIO()
    >>> with redirect_stdout(sio):
    ...     logger("hello world!", "note", do_print=True)
    >>> line = sio.getvalue().strip()
    >>> print(line[line.index("n"):])
    note: hello world!

    >>> logger("hello world")  # not printed in doctests
    >>> logger("hello world", do_print=False)  # not printed anyway
    """
    if do_print:
        text: Final[str] = f"{__DTN()}{note}: {message}"
        print(text, flush=True)  # noqa
