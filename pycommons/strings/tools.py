"""Routines for handling strings."""

from re import Match, subn
from re import compile as _compile
from typing import Callable, Final, Iterable, Pattern, cast

from pycommons.types import type_error

#: fast call to :meth:`str.__len__`
__LEN: Final[Callable[[str], int]] = cast(Callable[[str], int], str.__len__)


def replace_str(find: str, replace: str, src: str) -> str:
    """
    Perform a recursive replacement of strings.

    After applying this function, there will not be any occurence of `find`
    left in `src`. All of them will have been replaced by `replace`. If that
    produces new instances of `find`, these will be replaced as well
    *unless they do not make the string shorter*. In other words, the
    replacement is continued only if the new string becomes shorter.

    See :func:`replace_regex` for regular-expression based replacements.

    :param find: the string to find
    :param replace: the string with which it will be replaced
    :param src: the string in which we search
    :return: the string `src`, with all occurrences of find replaced by replace
    :raises TypeError: if any of the parameters are not strings

    >>> replace_str("a", "b", "abc")
    'bbc'
    >>> replace_str("aa", "a", "aaaaa")
    'a'
    >>> replace_str("aba", "a", "abaababa")
    'aa'
    >>> replace_str("aba", "aba", "abaababa")
    'abaababa'
    >>> replace_str("aa", "aa", "aaaaaaaa")
    'aaaaaaaa'
    >>> replace_str("a", "aa", "aaaaaaaa")
    'aaaaaaaaaaaaaaaa'
    >>> replace_str("a", "xx", "aaaaaaaa")
    'xxxxxxxxxxxxxxxx'

    >>> try:
    ...     replace_str(None, "a", "b")
    ... except TypeError as te:
    ...     print(te)
    replace() argument 1 must be str, not None

    >>> try:
    ...     replace_str(1, "a", "b")
    ... except TypeError as te:
    ...     print(te)
    replace() argument 1 must be str, not int

    >>> try:
    ...     replace_str("a", None, "b")
    ... except TypeError as te:
    ...     print(te)
    replace() argument 2 must be str, not None

    >>> try:
    ...     replace_str("x", 1, "b")
    ... except TypeError as te:
    ...     print(te)
    replace() argument 2 must be str, not int

    >>> try:
    ...     replace_str("a", "v", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     replace_str("x", "xy", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    """
    new_len: int = __LEN(src)
    while True:
        src = src.replace(find, replace)
        old_len: int = new_len
        new_len = __LEN(src)
        if new_len >= old_len:
            return src


def replace_regex(search: str | Pattern,
                  replace: str | Callable[[Match], str],
                  inside: str) -> str:
    r"""
    Replace all occurrences of 'search' in 'inside' with 'replace'.

    This replacement procedure is done repetitively and recursively until
    no occurrence of `search` is found anymore. This, of course, may lead
    to an endless loop, so a `ValueError` is thrown if there are too many
    recursive replacements.

    :param search: the regular expression to search, either a string or a
        pattern
    :param replace: the string to replace it with, or a function receiving
        a :class:`re.Match` instance and returning a replacement string
    :param inside: the string in which to search/replace
    :return: the new string after the recursive replacement
    :raises TypeError: if any of the parameters is not of the right type
    :raises ValueError: if there are 100000 recursive replacements or more,
        indicating that there could be an endless loop

    >>> replace_regex('[ \t]+\n', '\n', ' bla \nxyz\tabc\t\n')
    ' bla\nxyz\tabc\n'
    >>> replace_regex('[0-9]A', 'X', '23A7AA')
    '2XXA'
    >>> from re import compile as cpx
    >>> replace_regex(cpx('[0-9]A'), 'X', '23A7AA')
    '2XXA'

    >>> def __repl(a):
    ...     print(repr(a))
    ...     return "y"
    >>> replace_regex("a.b", __repl, "albaab")
    <re.Match object; span=(0, 3), match='alb'>
    <re.Match object; span=(3, 6), match='aab'>
    'yy'

    >>> def __repl(a):
    ...     print(repr(a))
    ...     ss = a.group()
    ...     print(ss)
    ...     return "axb"
    >>> replace_regex("aa.bb", __repl, "aaaaaxbbbbb")
    <re.Match object; span=(3, 8), match='aaxbb'>
    aaxbb
    <re.Match object; span=(2, 7), match='aaxbb'>
    aaxbb
    <re.Match object; span=(1, 6), match='aaxbb'>
    aaxbb
    <re.Match object; span=(0, 5), match='aaxbb'>
    aaxbb
    'axb'

    >>> replace_regex("aa.bb", "axb", "aaaaaxbbbbb")
    'axb'
    >>> replace_regex("aa.bb", "axb", "".join("a" * 100 + "y" + "b" * 100))
    'axb'
    >>> replace_regex("aa.bb", "axb",
    ...               "".join("a" * 10000 + "y" + "b" * 10000))
    'axb'

    >>> try:
    ...    replace_regex(1, "1", "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}

    >>> try:
    ...    replace_regex(None, "1", "2")
    ... except TypeError as te:
    ...    print(te)
    search should be an instance of any in {str, typing.Pattern} but is None.

    >>> try:
    ...    replace_regex("x", 2, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str or a callable but is int, namely '2'.

    >>> try:
    ...    replace_regex("x", None, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str or a callable but is None.

    >>> try:
    ...    replace_regex(1, 1, "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}

    >>> try:
    ...    replace_regex("yy", "1", 3)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is int, namely '3'.

    >>> try:
    ...    replace_regex("adad", "1", None)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is None.

    >>> try:
    ...    replace_regex(1, "1", 3)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}

    >>> try:
    ...    replace_regex(1, 3, 5)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}

    >>> try:
    ...     replace_regex("abab|baab|bbab|aaab|aaaa|bbbb", "baba",
    ...                   "ababababab")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Too many replacements, pattern re.compile('abab|ba
    """
    if not isinstance(search, Pattern):
        if isinstance(search, str):
            search = _compile(search)
        else:
            raise type_error(search, "search", (str, Pattern))
    if not (isinstance(replace, str) or callable(replace)):
        raise type_error(replace, "replace", str, call=True)
    if not isinstance(inside, str):
        raise type_error(inside, "inside", str)
    for _ in range(100_000):
        text, n = subn(pattern=search, repl=replace, string=inside)
        if (n <= 0) or (text == inside):
            return text
        inside = text
    raise ValueError(
        f"Too many replacements, pattern {search!r} probably malformed for "
        f"text {inside!r} and replacement {replace!r}.")


def get_prefix_str(strings: str | Iterable[str]) -> str:
    r"""
    Compute the common prefix of an iterable of strings.

    :param strings: the iterable of strings
    :return: the common prefix
    :raises TypeError: if the input is not a string, iterable of string,
        or contains any non-string element (before the prefix is determined)
        Notice: If the prefix is determined as the empty string, then the
        search is stopped. If some non-`str` items follow later in `strings`,
        then these may not raise a `TypeError`

    >>> get_prefix_str(["abc", "acd"])
    'a'
    >>> get_prefix_str(["xyz", "gsdf"])
    ''
    >>> get_prefix_str([])
    ''
    >>> get_prefix_str(["abx"])
    'abx'
    >>> get_prefix_str(("abx", ))
    'abx'
    >>> get_prefix_str({"abx", })
    'abx'
    >>> get_prefix_str("abx")
    'abx'
    >>> get_prefix_str(("\\relative.path", "\\relative.figure",
    ...     "\\relative.code"))
    '\\relative.'
    >>> get_prefix_str({"\\relative.path", "\\relative.figure",
    ...     "\\relative.code"})
    '\\relative.'

    >>> try:
    ...     get_prefix_str(None)
    ... except TypeError as te:
    ...     print(te)
    strings should be an instance of any in {str, typing.Iterable} but is None.

    >>> try:
    ...     get_prefix_str(1)
    ... except TypeError as te:
    ...     print(str(te)[:60])
    strings should be an instance of any in {str, typing.Iterabl

    >>> try:
    ...     get_prefix_str(["abc", "acd", 2, "x"])
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     get_prefix_str(["abc", "acd", None, "x"])
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> get_prefix_str(["xyz", "gsdf", 5])
    ''
    """
    if isinstance(strings, str):
        return strings
    if not isinstance(strings, Iterable):
        raise type_error(strings, "strings", (str, Iterable))
    prefix: str | None = None
    prefix_len: int = -1
    for current in strings:  # iterate over all strings
        current_len: int = __LEN(current)
        if prefix is None:  # no prefix set yet
            prefix = current
            prefix_len = current_len
        else:  # we got a prefix
            for i in range(min(prefix_len, current_len)):
                if prefix[i] != current[i]:
                    prefix_len = i
                    break
        if prefix_len == 0:
            return ""
    return "" if prefix is None else prefix[0:prefix_len]
