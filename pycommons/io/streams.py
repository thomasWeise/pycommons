"""
Streams for reading and writing of data.

When working with text files, we would usually open them as instances of
:class:`~io.TextIOBase`. However, we usually only need a tiny subset of what
these classes offer.
For example, when we open a text file for reading, usually, we just want to
iterate over its lines.
When opening a file for writing, usually, we just want to iteratively write
lines of text.
From this perspective, a text input stream is basically an interator of string
which returns the lines one-by-one.
A text output stream then basically is a function which accepts a string.
Whenever this function is called, it writes this string as line to the output.
This perspective has some intriguing effects: If a text file opened for
reading is indeed represented as iterator of strings, then the code processing
this iterator can as well accept other sources, such as lists,
*without needing any change*.
If a file opened for text output is indeed treated as `Callable[[str], Any]`,
then code writing to such a file can as well receive another such callable,
say, :func:`print`.
In other words, that works with this concept of text input and output will
become much more versatile and elegant.

However, there is one drawback: How can we close the streams once we are done
with them?
In this module, we try marry the :class:`typing.ContextManager` interface to
the iterator/`Callable` perspective.
In other words, it provides the above functionality in a way that uses
Python's magic of decorators, context managers, and generators to
automatically close the underlying text streams once the iterator or
`Callable` goes out of scope.
"""

from contextlib import contextmanager
from io import TextIOBase
from typing import (
    Any,
    Callable,
    Final,
    Generator,
    Iterable,
    Iterator,
    Protocol,
    TextIO,
    cast,
)

from pycommons.types import type_error


def __input_stream(get_str: Callable[[], str],
                   closer: Callable[[], Any]) -> Iterator[str]:
    r"""
    Turn a stream into an iterator of lines: the internal implementation.

    The function `get_str()` will be used to get the elements to iterate
    over. As soon as it returns the empty string, the iteration stops.
    Once the iteration stops, the `closer` method is called.

    See :func:`input_stream` for details.

    :param get_str: get the next string
    :param closer: to be invoked when the stream is finished
    :return: an iterator for the strings in the stream, which all will be
        piped through :meth:`str.rstrip`.

    >>> def _close():
    ...     print("closed.")
    >>> def _get(l: list[str]) -> Callable[[], str]:
    ...     __i: int = 0
    ...     def __get() -> str:
    ...         nonlocal __i
    ...         nonlocal  l
    ...         __i += 1
    ...         if __i > len(l):
    ...             return ""
    ...         return l[__i - 1]
    ...     return __get

    >>> for f in __input_stream(_get(["a", "b"]), _close):
    ...     print(f)
    a
    b
    closed.

    >>> for f in __input_stream(_get([" a ", "b\n "]), _close):
    ...     print(f)
     a
    b
    closed.

    >>> try:
    ...     for f in __input_stream(_get(["a", "b"]), _close):
    ...         print(f)
    ...         raise ValueError
    ... except ValueError as ve:
    ...     print(ve)
    a
    closed.
    <BLANKLINE>

    >>> for f in __input_stream(_get([]), _close):
    ...     print(f)
    closed.

    >>> for f in __input_stream(_get(["y", "e"]), _close):
    ...     print(f)
    ...     break
    y
    closed.

    >>> it = __input_stream(_get(["x", "y", "z"]), _close)
    >>> print(next(it))
    x
    >>> print(next(it))
    y
    >>> print("a")
    a
    >>> del it
    closed.
    >>> def k():
    ...     it = __input_stream(_get(["x", "y", "z"]), _close)
    ...     print(next(it))
    >>> k()
    x
    closed.
    """
    the_len: Final[Callable[[str], int]] = cast(
        Callable[[str], int], str.__len__)
    the_rstrip: Final[Callable[[str], str]] = cast(
        Callable[[str], str], str.rstrip)
    try:
        while True:
            s = get_str()
            if the_len(s) == 0:
                break
            yield the_rstrip(s)
    finally:
        closer()


def input_stream(get_str: Callable[[], str],
                 closer: Callable[[], Any]) -> Iterator[str]:
    r"""
    Turn an input stream into an iterator of lines.

    The function `get_str()` will be used to get the elements to iterate
    over. As soon as it returns the empty string, the iteration stops.
    Once the iteration stops, the `closer` method is called.
    All strings from `get_str` will be piped through :meth:`str.rstrip`,
    meaning that trailing spaces or newlines will all be removed.

    :param get_str: get the next string
    :param closer: to be invoked when the stream is finished
    :return: an iterator for the strings in the stream, which all will be
        piped through :meth:`str.rstrip`.

    >>> def _close():
    ...     print("closed.")
    >>> def _get(l: list[str]) -> Callable[[], str]:
    ...     __i: int = 0
    ...     def __get() -> str:
    ...         nonlocal __i
    ...         nonlocal  l
    ...         __i += 1
    ...         if __i > len(l):
    ...             return ""
    ...         return l[__i - 1]
    ...     return __get

    >>> for f in input_stream(_get(["a", "b"]), _close):
    ...     print(f)
    a
    b
    closed.

    >>> def _is():
    ...     iss = input_stream(_get(["a", "b "]), _close)
    ...     print(next(iss))
    >>> _is()
    a
    closed.

    >>> for f in input_stream(_get([" a ", "b\n "]), _close):
    ...     print(f)
     a
    b
    closed.

    >>> try:
    ...     for f in input_stream(_get(["a", "b"]), _close):
    ...         print(f)
    ...         raise ValueError("hehehe")
    ... except ValueError as ve:
    ...     print(ve)
    a
    closed.
    hehehe

    >>> for f in input_stream(_get([]), _close):
    ...     print(f)
    closed.

    >>> print(list(input_stream(_get(["a", "x"]), _close)))
    closed.
    ['a', 'x']

    >>> print(list(input_stream(_get(["a  ", " x\n\n "]), _close)))
    closed.
    ['a', ' x']

    >>> for f in input_stream(_get(["y", "e"]), _close):
    ...     print(f)
    ...     break
    y
    closed.

    >>> it = input_stream(_get(["x", "y", "z"]), _close)
    >>> print(next(it))
    x
    >>> print(next(it))
    y
    >>> print("a")
    a
    >>> del it
    closed.
    >>> def k():
    ...     it = input_stream(_get(["x", "y", "z"]), _close)
    ...     print(next(it))
    >>> k()
    x
    closed.

    >>> try:
    ...     next(input_stream(None, _close))
    ... except TypeError as te:
    ...     print(te)
    closed.
    get_str should be a callable but is None.

    >>> try:
    ...     input_stream(1, _close)
    ... except TypeError as te:
    ...     print(te)
    closed.
    get_str should be a callable but is int, namely '1'.

    >>> try:
    ...     input_stream(_get(["12"]), None)
    ... except TypeError as te:
    ...     print(te)
    closer should be a callable but is None.

    >>> try:
    ...     input_stream(_get(["12"]), 1)
    ... except TypeError as te:
    ...     print(te)
    closer should be a callable but is int, namely '1'.

    >>> try:
    ...     for sss in input_stream(_get(["12", 5]), _close):
    ...         print(sss)
    ... except TypeError as te:
    ...     print(te)
    12
    closed.
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> def _get2(l: list[str]) -> Callable[[], str]:
    ...     __i: int = 0
    ...     def __get() -> str:
    ...         nonlocal __i
    ...         nonlocal  l
    ...         __i += 1
    ...         if __i > len(l):
    ...             raise ValueError("Crash!")
    ...         return l[__i - 1]
    ...     return __get
    >>> try:
    ...     print(list(input_stream(_get2(["12", "x"]), _close)))
    ... except ValueError as ve:
    ...     print(ve)
    closed.
    Crash!
    """
    if not callable(closer):
        raise type_error(closer, "closer", call=True)
    if not callable(get_str):
        closer()
        raise type_error(get_str, "get_str", call=True)
    return __input_stream(get_str, closer)


def as_input_stream(stream: TextIOBase | TextIO) -> Iterator[str]:
    r"""
    Turn an input stream into an `Iterator` and close it after the iteration.

    All the lines from the text input source are made available via the
    returned :class:`typing.Iterator` object. Before being returned, they are
    piped through :meth:`str.rstrip`, meaning that trailing newlines and
    spaces are all removed.
    You do not have to manage the scope of the stream via its
    :class:`typing.ContextManager` interface anymore. Instead, it will
    automatically be closed once it leaves the current scope.

    :param stream: the text
    :return: an iterator of strings read from `stream` that closes the stream
        once done iterating or leaving the scope.

    >>> from tempfile import mkstemp
    >>> from os import remove as osremovex
    >>> from os import close as osclosex
    >>> h, p = mkstemp(text=True)
    >>> osclosex(h)
    >>> with open(p, "wt") as sta:
    ...     sta.writelines(["123\n", "456\n"])
    >>> with open(p, "rt") as rt:
    ...     while True:
    ...         rl = rt.readline()
    ...         if rl == "":
    ...             break
    ...         print(rl.rstrip())
    123
    456
    >>> tstr = open(p, "rt")
    >>> tstr.closed
    False
    >>> for s in as_input_stream(tstr):
    ...     print(s.rstrip())
    123
    456
    >>> tstr.closed
    True
    >>> stre = open(p, "rt")
    >>> for s in as_input_stream(stre):
    ...     print(s.rstrip())
    123
    456
    >>> stre.closed
    True
    >>> stre = open(p, "rt")
    >>> for s in as_input_stream(stre):
    ...     print(s.rstrip())
    ...     break
    123
    >>> stre.closed
    True
    >>> stre = open(p, "rt")
    >>> print(list(as_input_stream(stre)))
    ['123', '456']
    >>> stre.closed
    True
    >>> osremovex(p)

    >>> try:
    ...     as_input_stream(None)
    ... except TypeError as te:
    ...     print(te)
    stream should be an instance of io.TextIOBase but is None.

    >>> try:
    ...     as_input_stream(1)
    ... except TypeError as te:
    ...     print(te)
    stream should be an instance of io.TextIOBase but is int, namely '1'.
    """
    if not isinstance(stream, TextIOBase):
        raise type_error(stream, "stream", TextIOBase)
    return input_stream(stream.readline, stream.close)


class StrCallCtxMgr(Protocol):
    """
    A callable context manager.

    In order to allow MyPy to properly handle the return values of
    :func:`~output_stream` and :func:`~as_output_stream`, this token protocol
    unites the interfaces :class:`typing.Callable` and
    :class:`contextlib.AbstractContextManager`.
    """

    def __call__(self, text: str) -> None:
        """
        Invoke the actual consumer.

        :param text: the text to be passed in
        """

    def __enter__(self) -> Callable[[str], None]:
        """
        Enter the context.

        :return: itself
        """

    def __exit__(self, _, __, ___) -> bool:
        """
        Exit the context.

        :param _: the exception type
        :param __: the exception value
        :param ___: the whatever
        :return: `True` if the exception should be re-raised, if any, `False`
            otherwise
        """


@contextmanager
def __output_stream(write: Callable[[str], Any], close: Callable[[], Any],
                    suffix: str | None) \
        -> Generator[Callable[[str], None], None, None]:
    r"""
    Convert a function pair to a context-managed output stream.

    See :func:`output_stream` for details.

    :param write: the write function
    :param close: the close function
    :param suffix: the suffix to append to each rstrip-ped line
    :return: the context manager

    >>> from tempfile import mkstemp
    >>> from os import remove as osremovex
    >>> from os import close as osclosex
    >>> h, p = mkstemp(text=True)
    >>> osclosex(h)
    >>> wt = open(p, "wt")
    >>> with __output_stream(wt.write, wt.close, "\n") as cons:
    ...     cons("1")
    ...     cons("2  ")
    >>> wt.closed
    True
    >>> for s in as_input_stream(open(p, "rt")):
    ...     print(s)
    1
    2
    >>> wt = open(p, "wt")
    >>> with __output_stream(wt.write, wt.close, None) as cons:
    ...     cons("1")
    ...     cons("2  ")
    >>> wt.closed
    True
    >>> for s in as_input_stream(open(p, "rt")):
    ...     print(s)
    12
    >>> wt = open(p, "wt")
    >>> try:
    ...     with __output_stream(wt.write, wt.close, None) as cons:
    ...         cons("1")
    ...         cons(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'NoneType' object
    >>> wt.closed
    True
    >>> wt = open(p, "wt")
    >>> try:
    ...     with __output_stream(wt.write, wt.close, None) as cons:
    ...         cons("1")
    ...         cons(int)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'type' object
    >>> wt.closed
    True
    >>> osremovex(p)
    """
    if suffix is None:
        def __write_1(s: str, __write: Callable[[str], Any] = write,
                      __rstrip: Callable[[str], str] = cast(
                          Callable[[str], str], str.rstrip)) -> None:
            __write(__rstrip(s))
        __writer = cast(Callable[[str], None], __write_1)
    else:
        def __write_2(s: str, __write: Callable[[str], Any] = write,
                      __rstrip: Callable[[str], str] = cast(
                          Callable[[str], str], str.rstrip),
                      __s=suffix) -> None:
            __write(__rstrip(s))
            __write(__s)
        __writer = cast(Callable[[str], None], __write_2)

    try:
        yield __writer
    finally:
        close()


def output_stream(write: Callable[[str], Any],
                  close: Callable[[], Any],
                  suffix: str | None = "\n") -> StrCallCtxMgr:
    """
    Convert a function pair to a context-managed output stream.

    The result of this function is a `Callable` which receives a single
    string argument. This argument is passed to :meth:`str.rstrip` and
    the result of this is handed to `write`. After each time this is
    done, the `suffix` is also passed to a call to `write`, unless it is
    `None`.

    `suffix` can be a newline character to end lines when writing text to a
    text IO object. It could also be `None` if we just want to pipe the raw
    strings to `write` and do not need additional invocations of `write` to
    add end-of-line markers.

    Once the scope of the returned :class:`typing.Callable` ends, `close` is
    invoked.

    :param write: the write function
    :param close: the close function
    :param suffix: the suffix to be appended to each rstrip-ped line
    :return: the context manager

    >>> from tempfile import mkstemp
    >>> from os import remove as osremovex
    >>> from os import close as osclosex
    >>> h, p = mkstemp(text=True)
    >>> osclosex(h)
    >>> wt = open(p, "wt")
    >>> callable(output_stream(wt.write, wt.close))
    True
    >>> with output_stream(wt.write, wt.close) as cons:
    ...     cons("1")
    ...     cons("2  ")
    >>> for s in as_input_stream(open(p, "rt")):
    ...     print(s)
    1
    2
    >>> osremovex(p)
    >>> def __c():
    ...     print("closed")
    >>> with output_stream(print, __c) as cons:
    ...     cons("1")
    ...     cons("2")
    1
    <BLANKLINE>
    <BLANKLINE>
    2
    <BLANKLINE>
    <BLANKLINE>
    closed
    >>> def __c():
    ...     print("closed")
    >>> with output_stream(print, __c, None) as cons:
    ...     cons("1")
    ...     cons("2")
    1
    2
    closed
    >>> def __c():
    ...     print("closed")
    >>> with output_stream(print, __c, "a") as cons:
    ...     cons("1")
    ...     cons("2")
    1
    a
    2
    a
    closed
    >>> try:
    ...     with output_stream(print, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    close should be a callable but is int, namely '1'.
    >>> try:
    ...     with output_stream(2, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    close should be a callable but is int, namely '1'.
    >>> try:
    ...     with output_stream(2, __c) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    closed
    write should be a callable but is int, namely '2'.
    >>> try:
    ...     with output_stream(print, __c, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    closed
    suffix should be an instance of any in {None, str} but is int, namely '1'.
    >>> try:
    ...     with output_stream(None, __c, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    closed
    write should be a callable but is None.
    >>> try:
    ...     with output_stream(None, None, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    close should be a callable but is None.
    >>> try:
    ...     with output_stream(print, None, 1) as cons:
    ...         cons("1")
    ... except TypeError as te:
    ...     print(te)
    close should be a callable but is None.
    """
    if not callable(close):
        raise type_error(close, "close", call=True)
    if not callable(write):
        close()
        raise type_error(write, "write", call=True)
    if (suffix is not None) and (not isinstance(suffix, str)):
        close()
        raise type_error(suffix, "suffix", (str, None))
    return cast(StrCallCtxMgr, __output_stream(write, close, suffix))


def as_output_stream(stream: TextIOBase | TextIO) -> StrCallCtxMgr:
    """
    Turn a stream into an output consumer for single lines.

    You still have to manage the scope of the stream via its
    :class:`typing.ContextManager` interface, but you can now treat it like a
    single :class:`typing.Callable` receiving the strings to be written to the
    output. Each string will be piped through :meth:`str.rstrip` before being
    written and after each string, a newline character is written.

    :param stream: the input stream
    :return: the consumer for writing strings.

    >>> from tempfile import mkstemp
    >>> from os import remove as osremovex
    >>> from os import close as osclosex
    >>> h, p = mkstemp(text=True)
    >>> osclosex(h)
    >>> with as_output_stream(open(p, "wt")) as cons:
    ...     cons("1")
    ...     cons("2  ")
    >>> for s in as_input_stream(open(p, "rt")):
    ...     print(s)
    1
    2
    >>> osremovex(p)
    >>> try:
    ...     with as_output_stream(None):
    ...         pass
    ... except TypeError as te:
    ...     print(te)
    stream should be an instance of io.TextIOBase but is None.
    """
    if not isinstance(stream, TextIOBase):
        raise type_error(stream, "stream", TextIOBase)
    return output_stream(stream.write, stream.close)


def write_all(text: str | Iterable[str],
              collector: Callable[[str], Any]) -> None:
    """
    Write all the strings to the given collector.

    This function writes all the contents of `text` to the given `collector`.
    It checks the types of `text` and `collector`. Type checking for the
    contents of `text` is done via :meth:`str.rstrip`, which is applied to
    every single line in `text` (assuming that no element in `text` contains
    a newline character).

    :param text: the text source
    :param collector: the collector

    >>> write_all("a", print)
    a
    >>> write_all(["a", "b"], print)
    a
    b
    >>> write_all(["a ", " b"], print)
    a
     b
    >>> try:
    ...     write_all(1, print)
    ... except TypeError as te:
    ...     print(te)
    text should be an instance of any in {str, typing.Iterable} \
but is int, namely '1'.
    >>> try:
    ...     write_all(1, 2)
    ... except TypeError as te:
    ...     print(te)
    text should be an instance of any in {str, typing.Iterable} \
but is int, namely '1'.
    >>> try:
    ...     write_all("a", 2)
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is int, namely '2'.
    >>> try:
    ...     write_all(["a", "b"], 2)
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is int, namely '2'.
    >>> try:
    ...     write_all(["a", "b", 1, "3"], print)
    ... except TypeError as te:
    ...     print(te)
    a
    b
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'int' object
    >>> try:
    ...     write_all(["a", "b", 1, "3"], 4)
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is int, namely '4'.
    """
    if isinstance(text, str):
        text = (text, )
    elif not isinstance(text, Iterable):
        raise type_error(text, "text", (Iterable, str))
    if not callable(collector):
        raise type_error(collector, "collector", call=True)

    the_rstrip: Final[Callable[[str], str]] = cast(
        Callable[[str], str], str.rstrip)
    for st in text:
        collector(the_rstrip(st))
