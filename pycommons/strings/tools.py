"""Routines for handling strings."""

from re import MULTILINE, Match, subn
from re import compile as _compile
from typing import Callable, Final, Iterable, Pattern

from pycommons.types import type_error


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
    new_len: int = str.__len__(src)
    while True:
        src = src.replace(find, replace)
        old_len: int = new_len
        new_len = str.__len__(src)
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


def normalize_trailing_space(text: str) -> str:
    r"""
    Normalize all trailing white space from in the lines in the given text.

    All white space trailing any line is removed.
    All white space including newline characters at the end of the text are
    replaced with a single newline character.
    If the text is empty, a single newline character is returned.

    :param text: the text
    :return: the text, minus all white space trailing any *line*
    :raises TypeError: if `text` is not an instance of `str`

    >>> normalize_trailing_space("a")
    'a\n'
    >>> normalize_trailing_space("a ")
    'a\n'
    >>> normalize_trailing_space("a \n\n \n ")
    'a\n'
    >>> normalize_trailing_space("")
    '\n'
    >>> normalize_trailing_space("  a \n\t\n\t \n \t\t\nb  \n\t \n\n")
    '  a\n\n\n\nb\n'
    >>> try:
    ...     normalize_trailing_space(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'
    >>> try:
    ...     normalize_trailing_space(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    """
    if str.__len__(text) == 0:
        return "\n"
    text = str.rstrip(replace_regex(
        __PATTERN_TRAILING_WHITESPACE, "\n", text))
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


def split_str(text: str, sep: str = "\n") -> Iterable[str]:
    r"""
    Convert a string to an iterable of strings by splitting it.

    All the lines in `text` are rstripped, meaning that all trailing white
    space is removed from them. Leading white space is not removed.

    :param text: the original text string
    :param sep: the separator, by default the newline character
    :return: the lines
    :raises TypeError: if `text` or `sep` are not strings
    :raises ValueError: if `sep` is the empty string

    >>> list(split_str("x"))
    ['x']
    >>> list(split_str("x\ny"))
    ['x', 'y']
    >>> list(split_str("x  \ny  "))
    ['x', 'y']
    >>> list(split_str(" x  \ny  "))
    [' x', 'y']
    >>> list(split_str("\n123\n  456\n789 \n 10\n\n"))
    ['', '123', '  456', '789', ' 10', '', '']
    >>> list(split_str(""))
    ['']

    >>> list(split_str("x", "a"))
    ['x']
    >>> list(split_str("xay", "a"))
    ['x', 'y']
    >>> list(split_str("x  ay  ", "a"))
    ['x', 'y']
    >>> list(split_str(" x  ay  ", "a"))
    [' x', 'y']
    >>> list(split_str("a123a  456a789 a 10aa", "a"))
    ['', '123', '  456', '789', ' 10', '', '']
    >>> list(split_str(""))
    ['']

    >>> try:
    ...     split_str(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    >>> try:
    ...     split_str(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     split_str("xax", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    >>> try:
    ...     split_str("xax", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'
    >>> try:
    ...     split_str("xax", "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid separator string '' for text 'xax'.
    """
    if str.__len__(text) <= 0:
        return ("", )
    if str.__len__(sep) <= 0:
        raise ValueError(
            f"Invalid separator string {sep!r} for text {text!r}.")
    return map(str.rstrip, text.split(sep))


def join_str(lines: Iterable[str],
             trailing_sep: bool = True,
             sep: str = "\n") -> str:
    r"""
    Convert an iterable of strings to a single string joined by a separator.

    All the strings in `lines` are right-stripped of trailing white space.
    They are then concatenated with the separator `sep`, which, by default, is
    the newline character `'\n'`.
    The result is again right-stripped of trailing white space.
    If `trailing_sep` is `True`, then, finally `sep` is appended.

    :param lines: the lines
    :param trailing_sep: should there be a separator appended at the end?
    :param sep: the separator string to be used, by default the newline
        character.
    :return: the single string
    :raises TypeError: if either `lines`, `sep`, or `trailing_sep` are of the
        wrong type or if `lines` contains any non-string

    >>> join_str(["a", "b", "", "c", ""])
    'a\nb\n\nc\n'
    >>> join_str(["a", "b", "", "c"])
    'a\nb\n\nc\n'
    >>> join_str(["a", "b", "", "c"], sep="")
    'abc'

    >>> join_str(["a", "b", "", "c", ""], trailing_sep=True)
    'a\nb\n\nc\n'
    >>> join_str(["a", "b", "", "c"], trailing_sep=True)
    'a\nb\n\nc\n'
    >>> join_str(("a", "b", "", "c"), trailing_sep=False)
    'a\nb\n\nc'
    >>> join_str(["a", "b", "", "c", ""], trailing_sep=False)
    'a\nb\n\nc'
    >>> join_str(("a  ", "b", " ", "c ", ""), trailing_sep=False)
    'a\nb\n\nc'

    >>> join_str(["a", "b", "", "c", ""], sep="y", trailing_sep=True)
    'aybyycy'
    >>> join_str(["a", "b", "", "c"], sep="y", trailing_sep=True)
    'aybyycy'
    >>> join_str(("a", "b", "", "c"), sep="y", trailing_sep=False)
    'aybyyc'
    >>> join_str(["a", "b", "", "c", ""], sep="y", trailing_sep=False)
    'aybyyc'
    >>> join_str(("a  ", "b", " ", "c ", ""), sep="y", trailing_sep=False)
    'aybyyc'

    >>> try:
    ...     join_str(None)
    ... except TypeError as te:
    ...     print(te)
    lines should be an instance of typing.Iterable but is None.
    >>> try:
    ...     join_str(1)
    ... except TypeError as te:
    ...     print(te)
    lines should be an instance of typing.Iterable but is int, namely '1'.
    >>> try:
    ...     join_str(["x", "y"], sep=None)
    ... except TypeError as te:
    ...     print(te)
    sep should be an instance of str but is None.
    >>> try:
    ...     join_str(["x", "y"], sep=1)
    ... except TypeError as te:
    ...     print(te)
    sep should be an instance of str but is int, namely '1'.
    >>> try:
    ...     join_str(("", "123", True))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'bool' object
    >>> try:
    ...     join_str(("", "123", "x"), 1)
    ... except TypeError as te:
    ...     print(te)
    trailing_sep should be an instance of bool but is int, namely '1'.
    """
    if not isinstance(lines, Iterable):
        raise type_error(lines, "lines", Iterable)
    if not isinstance(trailing_sep, bool):
        raise type_error(trailing_sep, "trailing_sep", bool)
    if not isinstance(sep, str):
        raise type_error(sep, "sep", str)
    use: Final[list[str]] = [str.rstrip(ll) for ll in lines]
    for i in range(list.__len__(use) - 1, -1, -1):
        if str.__len__(use[i]) <= 0:
            del use[i]
            continue
        break
    if trailing_sep:
        use.append("")
    return sep.join(use)
