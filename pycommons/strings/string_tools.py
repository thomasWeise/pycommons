"""Routines for handling strings."""

from re import Match, subn
from re import compile as _compile
from typing import Any, Callable, Final, Generator, Iterable, Pattern, cast

from pycommons.types import type_error

#: fast call to :meth:`str.__len__`
__LEN: Final[Callable[[str], int]] = cast("Callable[[str], int]", str.__len__)


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
    :returns: the string `src`, with all occurrences of find replaced by
        replace
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
    :returns: the new string after the recursive replacement
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
    replace should be an instance of str or a callable but is int, namely 2.

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
    inside should be an instance of str but is int, namely 3.

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
    :returns: the common prefix
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


def split_str(source: str, split_by: str) -> Generator[str, None, None]:
    """
    Split a string by the given other string.

    The goal is to provide a less memory intense variant of the method
    :meth:`str.split`. This routine should iteratively divide a given string
    based on a splitting character or string. This function may be useful if
    we are dealing with a very big `source` string and want to iteratively
    split it into smaller strings. Instead of creating a list with many small
    strings, what :meth:`str.split` does, it creates these strings
    iteratively

    :param source: the source string
    :param split_by: the split string
    :returns: each split element

    >>> list(split_str("", ""))
    ['']

    >>> list(split_str("", "x"))
    ['']

    >>> list(split_str("a", ""))
    ['a']

    >>> list(split_str("abc", ""))
    ['a', 'b', 'c']

    >>> list(split_str("a;b;c", ";"))
    ['a', 'b', 'c']

    >>> list(split_str("a;b;c;", ";"))
    ['a', 'b', 'c', '']

    >>> list(split_str(";a;b;;c;", ";"))
    ['', 'a', 'b', '', 'c', '']

    >>> list(split_str("a;aaa;aba;aa;aca;a", "a;a"))
    ['', 'a', 'b', '', 'c', '']
    """
    src_len: Final[int] = str.__len__(source)
    if src_len <= 0:  # handle empty input strings
        yield ""  # the source is empty, so the split is empty, too
        return  # quit after returning the empty string

    split_len: Final[int] = str.__len__(split_by)
    if split_len <= 0:  # handle empty split patterns
        yield from source  # if the split is empty, we return each character
        return  # and quit

    start: int = 0  # now we work for non-empty split patterns
    finder: Final[Callable[[str, int], int]] = source.find  # fast call
    while start < src_len:
        end = finder(split_by, start)
        if end < 0:
            yield source[start:] if start > 0 else source
            return  # pattern not found anymore, so we quit
        yield source[start:end]
        start = end + split_len
    yield ""  # pattern found at the end of the string


def escape(text: str, escapes: Iterable[str]) -> tuple[str, Any]:
    """
    Escapes a set of substrings inside a string in a reversible manner.

    A set of character sequences (`escapes`) are to be removed from
    `text` and to be replaced with characters that do not occur inside
    `text`. Escaping is a bijection. Since all escaped sequences are replaced
    with characters that are new to the string, there cannot be any issue with
    recursively occuring patterns or ambigiuties.

    Replacement is performed iteratively from beginning to end. The first
    sequence from `escapes` that is discovered is replaced and then the
    process continues. If two sequences start at the same place, then the
    longer one is replaced first.

    The same `text` with the same set of escapes will always produce the same
    output, regardless of the order of the escapes.

    The function returns a tuple containing the escaped string as well as the
    setup used for the escaping (as the second element). This second element
    must *only* be used by the function :func:`unescape`, which is the reverse
    operator of :func:`escape`. You must not make any assumption about its
    nature.

    :param text: the text
    :param escapes: the substrings to escape
    :return: a tuple of an escaped version of the string, together with
        the escape information.
        The second part of the tuple must not be accessed.

    >>> s, v = escape("12345", ("12", "X", "5"))
    >>> print(s)
    "34!
    >>> print(v)
    [('12', '"'), ('5', '!')]

    >>> unescape(s, v)
    '12345'

    >>> s, v = escape('"123!45', ("12", "X", "5", "!", '"'))
    >>> print(s)
    $&3#4%
    >>> print(v)
    [('!', '#'), ('"', '$'), ('12', '&'), ('5', '%')]

    >>> unescape(s, v)
    '"123!45'

    >>> s, v = escape('"123!45', ("X", "5", "12", "!", '"'))
    >>> print(s)
    $&3#4%
    >>> print(v)
    [('!', '#'), ('"', '$'), ('12', '&'), ('5', '%')]

    >>> unescape(s, v)
    '"123!45'

    >>> s, v = escape('111111112222233321111212121',
    ...     ("1", "11", "2", "222", "1", "32", "321", "21", "33"))
    >>> print(s)
    ####'""&(#!$$$
    >>> print(v)
    [('1', '!'), ('11', '#'), ('2', '"'), ('21', '$'), ('222', "'"), \
('321', '('), ('33', '&')]

    >>> unescape(s, v)
    '111111112222233321111212121'

    >>> s, v = escape('111&111112222233321111212X121',
    ...     ("1", "11", "2", "222", "1", "32", "321", "21", "33"))
    >>> print(s)
    #!&##!(""')#!$"X!$
    >>> print(v)
    [('1', '!'), ('11', '#'), ('2', '"'), ('21', '$'), ('222', '('), \
('321', ')'), ('33', "'")]

    >>> unescape(s, v)
    '111&111112222233321111212X121'

    >>> s, v = escape('221', ("22", "21"))
    >>> print(s)
    "1
    >>> print(v)
    [('22', '"')]

    >>> s, v = escape('22221', ("2222", "2221", "22", "21"))
    >>> print(s)
    $1
    >>> print(v)
    [('2222', '$')]

    >>> unescape(s, v)
    '22221'

    >>> s, v = escape('222212222122221', ("2222", "2221", "22", "21"))
    >>> print(s)
    $1$1$1
    >>> print(v)
    [('2222', '$')]

    >>> unescape(s, v)
    '222212222122221'

    >>> s, v = escape('222212222122221', ("2222", "2221", "22", "21", '"1'))
    >>> print(s)
    %1%1%1
    >>> print(v)
    [('2222', '%')]

    >>> unescape(s, v)
    '222212222122221'

    >>> try:
    ...     escape(1, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     escape("x", 5)
    ... except TypeError as te:
    ...     print(te)
    'int' object is not iterable

    >>> try:
    ...     escape("x", (5, ))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> s, v = escape("", ("12", ))
    >>> s == ""
    True
    >>> v is None
    True

    >>> s, v = escape("12", [])
    >>> s == "12"
    True
    >>> v is None
    True

    >>> s, v = escape("12", ["3", "4", "5"])
    >>> s == "12"
    True
    >>> v is None
    True

    >>> try:
    ...     s, v = escape("1" * 1_073_741_826, ("x", ))
    ... except ValueError as ve:
    ...     print(ve)
    We rather not escape a string with 1073741826 characters.

    >>> try:
    ...     s, v = escape("".join(chr(i) for i in range(524_290)), ("x", ))
    ... except ValueError as ve:
    ...     print(ve)
    524290 different characters and 1 escapes are too many.

    >>> try:
    ...     s, v = escape("123", ("x", ""))
    ... except ValueError as ve:
    ...     print(ve)
    Cannot escape empty string.
    """
    text_len: Final[int] = str.__len__(text)
    if text_len <= 0:
        return "", None
    if text_len > 1_073_741_824:
        raise ValueError(
            f"We rather not escape a string with {text_len} characters.")

    # check which of the escapes are actually needed
    forbidden: Final[list[Any]] = []
    charset: set[str] = set()
    needs_escaping: bool = False
    for fb in escapes:
        if str.__len__(fb) <= 0:
            raise ValueError("Cannot escape empty string.")
        if fb in forbidden:
            continue
        charset.update(fb)
        if fb in text:
            forbidden.append(fb)
            needs_escaping = True

    forbidden_len: int = list.__len__(forbidden)
    if (not needs_escaping) or (forbidden_len <= 0):
        return text, None

    # always create the same escape sequences
    forbidden.sort()
    # make sure to escape long sequences first
    forbidden.sort(key=str.__len__)  # type: ignore

    # get the set of all characters in this string
    charset.update(text)
    char_len: Final[int] = set.__len__(charset)
    if (char_len + forbidden_len) > 524_288:
        raise ValueError(
            f"{char_len} different characters and "
            f"{forbidden_len} escapes are too many.")

    # get the characters to be used for escaping
    marker: int = 33
    for i, esc in enumerate(forbidden):
        while True:
            cmarker: str = chr(marker)
            marker += 1
            if cmarker not in charset:
                break
        forbidden[i] = [esc, cmarker, False]  # type: ignore
        charset.add(cmarker)

    # perform the escaping
    last: int = 0
    used: list[tuple[str, str]] = []
    forbidden_len -= 1
    while forbidden_len >= 0:
        first: int = 1_073_741_825
        ft: list[Any] | None = None
        for i in range(forbidden_len, -1, -1):
            ftx = forbidden[i]
            index = text.find(ftx[0], last)
            if index >= last:
                if index < first:
                    ft = ftx
                    first = index
            else:
                del forbidden[i]
                forbidden_len -= 1
        if (first < 0) or (not ft):
            break

        # This form of replacement of subsequences is inefficient.
        text = str.replace(text, ft[0], ft[1], 1)  # Must be first occurence...
        # f"{text[:first]}{p2}{text[first + str.__len__(p1):]}"  # noqa
        last = first + str.__len__(ft[1])
        if ft[2]:
            continue
        used.append((ft[0], ft[1]))
        ft[2] = True

    used.sort()
    return text, used


def unescape(text: str, escapes: Any) -> str:
    """
    Revert the operation of the :func:`escape` function.

    See the documentation of the function :func:`escape`.

    :param text: the text
    :param escapes: the substrings to escape
    :return: a tuple of an escaped version of the string, together with
        the escape sequences.

    >>> s, v = escape('2345123123^21123z41vvvbH34Zxgo493244747261',
    ...     ("1", "11", "45", "v", "vb", "47", "61", "H3"))
    >>> print(s)
    23$!23!23^2#23z4!""('4Zxgo49324%%2&
    >>> print(v)
    [('1', '!'), ('11', '#'), ('45', '$'), ('47', '%'), ('61', '&'), \
('H3', "'"), ('v', '"'), ('vb', '(')]

    >>> unescape(s, v)
    '2345123123^21123z41vvvbH34Zxgo493244747261'

    >>> s, v = escape('23451"23123^2112$3z41#vvvb!H34Zxgo4932%44747261',
    ...     ("1", "11", "45", "v", "vb", "47", "61", "H3"))
    >>> print(s)
    23)&"23&23^2(2$3z4&#''-!,4Zxgo4932%4**2+
    >>> print(v)
    [('1', '&'), ('11', '('), ('45', ')'), ('47', '*'), ('61', '+'), \
('H3', ','), ('v', "'"), ('vb', '-')]

    >>> unescape(s, v)
    '23451"23123^2112$3z41#vvvb!H34Zxgo4932%44747261'

    >>> unescape("", [("a", "b"), ])
    ''

    >>> unescape("b", [("a", "b"), ])
    'a'

    >>> unescape("b", None)
    'b'

    >>> unescape("b", [])
    'b'

    >>> try:
    ...     unescape("1" * 1_073_741_825, [("1", "2"), ])
    ... except ValueError as ve:
    ...     print(ve)
    We rather not unescape a string with 1073741825 characters.
    """
    text_len: Final[int] = str.__len__(text)
    if (text_len <= 0) or (escapes is None) or (
            list.__len__(escapes) <= 0):
        return text
    if text_len > 1_073_741_824:
        raise ValueError(
            f"We rather not unescape a string with {text_len} characters.")

    # perform the un-escaping
    for orig, repl in escapes:
        text = str.replace(text, repl, orig)

    return text
