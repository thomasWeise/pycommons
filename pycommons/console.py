"""The `logger` routine for writing a log string to stdout."""
import datetime
from contextlib import AbstractContextManager, nullcontext
from typing import Callable, Final

#: the "now" function
__DTN: Final[Callable[[], datetime.datetime]] = datetime.datetime.now


def logger(message: str, note: str = "",
           lock: AbstractContextManager = nullcontext()) -> None:
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
    """
    text: Final[str] = f"{__DTN()}{note}: {message}"
    with lock:
        print(text, flush=True)  # noqa
