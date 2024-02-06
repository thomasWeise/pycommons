"""Routines for handling strings."""

from re import MULTILINE, Match, subn
from re import compile as _compile
from typing import Callable, Final, Iterable, Pattern

from pycommons.types import type_error


def regex_sub(search: str | Pattern,
              replace: str | Callable[[Match], str],
              inside: str) -> str:
    r"""
    Replace all occurrences of 'search' in 'inside' with 'replace'.

    :param search: the regular expression to search, either a string or a
        pattern
    :param replace: the string to replace it with, or a function receiving
        a :class:`re.Match` instance and returning a replacement string
    :param inside: the string in which to search/replace
    :return: the new string after the recursive replacement
    :raises TypeError: if any of the parameters is not of the right type

    >>> regex_sub('[ \t]+\n', '\n', ' bla \nxyz\tabc\t\n')
    ' bla\nxyz\tabc\n'
    >>> regex_sub('[0-9]A', 'X', '23A7AA')
    '2XXA'
    >>> from re import compile as cpx
    >>> regex_sub(cpx('[0-9]A'), 'X', '23A7AA')
    '2XXA'
    >>> def __repl(a):
    ...     print(repr(a))
    ...     return "y"
    >>> regex_sub("a.b", __repl, "albaab")
    <re.Match object; span=(0, 3), match='alb'>
    <re.Match object; span=(3, 6), match='aab'>
    'yy'
    >>> def __repl(a):
    ...     print(repr(a))
    ...     ss = a.group()
    ...     print(ss)
    ...     return "axb"
    >>> regex_sub("aa.bb", __repl, "aaaaaxbbbbb")
    <re.Match object; span=(3, 8), match='aaxbb'>
    aaxbb
    <re.Match object; span=(2, 7), match='aaxbb'>
    aaxbb
    <re.Match object; span=(1, 6), match='aaxbb'>
    aaxbb
    <re.Match object; span=(0, 5), match='aaxbb'>
    aaxbb
    'axb'
    >>> regex_sub("aa.bb", "axb", "aaaaaxbbbbb")
    'axb'
    >>> regex_sub("aa.bb", "axb", "".join("a" * 100 + "y" + "b" * 100))
    'axb'
    >>> regex_sub("aa.bb", "axb", "".join("a" * 10000 + "y" + "b" * 10000))
    'axb'
    >>> try:
    ...    regex_sub(1, "1", "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub(None, "1", "2")
    ... except TypeError as te:
    ...    print(te)
    search should be an instance of any in {str, typing.Pattern} but is None.
    >>> try:
    ...    regex_sub("x", 2, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str or a callable but is int, namely '2'.
    >>> try:
    ...    regex_sub("x", None, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str or a callable but is None.
    >>> try:
    ...    regex_sub(1, 1, "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub("yy", "1", 3)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is int, namely '3'.
    >>> try:
    ...    regex_sub("adad", "1", None)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is None.
    >>> try:
    ...    regex_sub(1, "1", 3)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub(1, 3, 5)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...     regex_sub("abab|baab|bbab|aaab|aaaa|bbbb", "baba", "ababababab")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Too many replacements, pattern re.compile('abab|ba
    """
    if not isinstance(search, Pattern):
        if isinstance(search, str):
            search = _compile(search, flags=MULTILINE)
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


#: A regular expression matching all characters that are non-line breaking
#: white space.
REGEX_WHITESPACE: Final[Pattern] = _compile(
    "[\t\u000b\u000c\u0020\u00a0\u1680\u2000\u2001\u2002\u2003\u2004"
    "\u2005\u2006\u2007\u2008\u2009\u200A\u202f\u205f\u3000]")

#: A regular expression matching all characters that are non-line breaking
#: white space.
REGEX_NEWLINE: Final[Pattern] = _compile(
    "(?:\n\r|\r\n|[\n\r\u0085\u2028\u2029])")

#: A regular expression matching any white space or newline character.
REGEX_WHITESPACE_OR_NEWLINE: Final[Pattern] = \
    _compile(f"{REGEX_NEWLINE.pattern[:-2]}{REGEX_WHITESPACE.pattern[1:]})")


#: a pattern used to clean up training white space
__PATTERN_TRAILING_WHITESPACE: Final[Pattern] = \
    _compile(f"{REGEX_WHITESPACE.pattern}+{REGEX_NEWLINE.pattern}",
             flags=MULTILINE)


def normalize_trailing_spaces(text: str) -> str:
    r"""
    Normalize all trailing white space from in the lines in the given text.

    All white space trailing any line is removed.
    All white space including newline characters at the end of the text are
    replaced with a single newline character.
    If the text is empty, a single newline character is returned.

    :param text: the text
    :return: the text, minus all white space trailing any *line*
    :raises TypeError: if `text` is not an instance of `str`

    >>> normalize_trailing_spaces("a")
    'a\n'
    >>> normalize_trailing_spaces("a ")
    'a\n'
    >>> normalize_trailing_spaces("a \n\n \n ")
    'a\n'
    >>> normalize_trailing_spaces("")
    '\n'
    >>> normalize_trailing_spaces("  a \n\t\n\t \n \t\t\nb  \n\t \n\n")
    '  a\n\n\n\nb\n'
    >>> try:
    ...     normalize_trailing_spaces(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'
    >>> try:
    ...     normalize_trailing_spaces(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    """
    if str.__len__(text) == 0:
        return "\n"
    text = str.rstrip(regex_sub(__PATTERN_TRAILING_WHITESPACE, "\n", text))
    return text + "\n"


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
        current_len: int = str.__len__(current)
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
