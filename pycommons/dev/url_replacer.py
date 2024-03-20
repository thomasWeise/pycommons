"""
Process a markdown file in order to make it useful for distribution.

In order to let sphinx properly load and insert the `README.md` file into the
project's documentation, we need to process this file from the GitHub style
markdown to a variant suitable for the myst parser used in sphinx. While we
are at it, we can also turn absolute URLs from the GitHub-`README.md` file
that point to the documentation URL to relative URLs.
"""

from itertools import chain
from re import Match, Pattern, escape, subn
from re import compile as re_compile
from typing import Any, Callable, Final, Iterable, Mapping, cast

from pycommons.net.url import URL
from pycommons.types import type_error

#: the separators for URLs in html
__HTML_URL_SEPARTORS: Final[tuple[tuple[str, str, str, str], ...]] = (
    (r'\s+href\s*=\s*"\s*', r'\s*"', ' href="', '"'),
    (r"\s+href\s*=\s*'\s*", r"\s*'", ' href="', '"'),
    (r'\s+src\s*=\s*"\s*', r'\s*"', ' src="', '"'),
    (r"\s+src\s*=\s*'\s*", r"\s*'", ' src="', '"'),
)

#: the separators for URLs in markdown
__MD_URL_SEPARTORS: Final[tuple[tuple[str, str, str, str], ...]] = (
    (r"\s*\]\s*\(\s*", r"\s*\)", r"](", r")"),
    (r"<\s*", r"\s*>", "<", ">"),
)


def __make_base_url_replacer(
        collector: Callable[[
            tuple[Pattern, Callable[[Match], str] | str]], Any],
        base_url_to_replace: str,
        replace_base_url_with: str = "./",
        for_markdown: bool = True) -> None:
    r"""
    Make `(Pattern, Callable)` tuples that replace base URLs in Markdown.

    :param collector: the collector (e.g. :meth:`list.append`) to receive the
        tuple
    :param base_url_to_replace: the base url to be replaced
    :param replace_base_url_with: the string with which the base URL should be
        replaced
    :param for_markdown: should replacers for Markdown be add (`True`) or only
        for HTML (`False`)

    >>> from re import sub
    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "./")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\/?(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x\\/?(.*)\\s*>'
    >>> sub(coll[3][0], coll[3][1], " src= ' https://example.com/x/y '")
    ' src="./y"'
    >>> sub(coll[1][0], coll[1][1], " href ='http://example.com/x/y  '")
    ' href="./y"'
    >>> sub(coll[2][0], coll[2][1], ' src ="https://example.com/x/y"')
    ' src="./y"'
    >>> sub(coll[0][0], coll[0][1], '  href ="http://example.com/x/y"')
    ' href="./y"'
    >>> sub(coll[4][0], coll[4][1], '[l](  https://example.com/x/y)')
    '[l](./y)'
    >>> sub(coll[4][0], coll[4][1], '![xx ] (http://example.com/x/y/g.jpg)')
    '![xx](./y/g.jpg)'
    >>> sub(coll[5][0], coll[5][1], '<  https://example.com/x/y >')
    '<./y>'
    >>> sub(coll[3][0], coll[3][1], "src='https://example.com/x/y ")
    "src='https://example.com/x/y "

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "./")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\/?(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x\\/?(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "./", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "/")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\/?(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x\\/?(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "/", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "bb")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x/", "bb", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "./")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\/?(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x\\/?(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "./", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "/")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\/?(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x\\/?(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "/", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\/?(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\/?(.*)\\s*'"

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "bb")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x(.*)\\s*\\)'
    '<\\s*https?://example\\.com/x(.*)\\s*>'

    >>> coll = list()
    >>> __make_base_url_replacer(
    ...     coll.append, "https://example.com/x", "bb", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x(.*)\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x(.*)\\s*'"

    >>> try:
    ...     __make_base_url_replacer(None, "https://example.com/x", "bb")
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is None.

    >>> try:
    ...     __make_base_url_replacer(1, "https://example.com/x", "bb")
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is int, namely '1'.

    >>> try:
    ...     __make_base_url_replacer(coll.append, None, "bb")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __make_base_url_replacer(coll.append, 1, "bb")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __make_base_url_replacer(
    ...         coll.append, "https://example.com/x", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     __make_base_url_replacer(coll.append, "https://example.com/x", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     __make_base_url_replacer(coll.append, "tweise@hfuu.edu.cn", "x")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid scheme 'mailto' for url 'tweise@hfuu.edu.cn'.

    >>> try:
    ...     __make_base_url_replacer(coll.append, "https://example.com/x",
    ...         "./", None)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is None.

    >>> try:
    ...     __make_base_url_replacer(coll.append, "https://example.com/x",
    ...         "./", 1)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is int, namely '1'.
    """
    if not callable(collector):
        raise type_error(collector, "collector", call=True)
    if not isinstance(for_markdown, bool):
        raise type_error(for_markdown, "for_markdown", bool)
    url: Final[URL] = URL(base_url_to_replace)
    if url.scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid scheme {url.scheme!r} for url {base_url_to_replace!r}.")
    use_repl: Final[str] = str.strip(replace_base_url_with)

    use_url: str = f"https?{escape(url[str.__len__(url.scheme):])}"
    if use_repl.startswith(("/", "./")):
        use_url += "?" if use_url.endswith("/") else r"\/?"

    for sr, er, ss, es in chain(__HTML_URL_SEPARTORS, __MD_URL_SEPARTORS) \
            if for_markdown else __HTML_URL_SEPARTORS:
        collector((
            cast(Pattern, re_compile(f"{sr}{use_url}(.*){er}")),
            cast(Callable[[Match], str],
                 lambda mm, _ss=ss, _es=es, _rr=use_repl:
                 f"{_ss}{_rr}{str.strip(mm.group(1))}{_es}")))


def __make_full_url_replacer(
        collector: Callable[[
            tuple[Pattern, Callable[[Match], str] | str]], Any],
        url_to_replace: str, replace_url_with: str = "./",
        for_markdown: bool = True) -> None:
    r"""
    Make `(Pattern, Callable)` tuples that replace full URLs in Markdown.

    :param collector: the collector (e.g. :meth:`list.append`) to receive the
        tuple
    :param url_to_replace: the full url to be replaced
    :param replace_url_with: the string with which the URL should be
        replaced
    :param for_markdown: should replacers for Markdown be add (`True`) or only
        for HTML (`False`)

    >>> from re import sub
    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/x.jpg", "x.jpg")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com/x\\.jpg\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com/x\\.jpg\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com/x\\.jpg\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com/x\\.jpg\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com/x\\.jpg\\s*\\)'
    '<\\s*https?://example\\.com/x\\.jpg\\s*>'
    >>> sub(coll[1][0], coll[1][1], " href= ' https://example.com/x.jpg '")
    ' href="x.jpg"'
    >>> sub(coll[1][0], coll[1][1], " href='https://example.com/x.jpg  '")
    ' href="x.jpg"'
    >>> sub(coll[2][0], coll[2][1], ' src="https://example.com/x.jpg"')
    ' src="x.jpg"'
    >>> sub(coll[2][0], coll[2][1], ' src="https://example.com/x.jpg"')
    ' src="x.jpg"'
    >>> sub(coll[4][0], coll[4][1], '[l](  https://example.com/x.jpg)')
    '[l](x.jpg)'
    >>> sub(coll[4][0], coll[4][1], '![xx ] (https://example.com/x.jpg)')
    '![xx](x.jpg)'
    >>> sub(coll[5][0], coll[5][1], '<  https://example.com/x.jpg>')
    '<x.jpg>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "./x")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\/?\\s*\\)'
    '<\\s*https?://example\\.com\\/?\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "./x", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "/x")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\/?\\s*\\)'
    '<\\s*https?://example\\.com\\/?\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "/x", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "bb")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\s*\\)'
    '<\\s*https?://example\\.com\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com/", "bb", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\s*'"

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "./x")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\/?\\s*\\)'
    '<\\s*https?://example\\.com\\/?\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "./x", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "/x")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\/?\\s*\\)'
    '<\\s*https?://example\\.com\\/?\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "/x", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\/?\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\/?\\s*'"

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "bb")
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s*\\]\\s*\\(\\s*https?://example\\.com\\s*\\)'
    '<\\s*https?://example\\.com\\s*>'

    >>> coll = list()
    >>> __make_full_url_replacer(
    ...     coll.append, "https://example.com", "bb", False)
    >>> for k, y in coll:
    ...     print(repr(k.pattern))
    '\\s+href\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+href\\s*=\\s*'\\s*https?://example\\.com\\s*'"
    '\\s+src\\s*=\\s*"\\s*https?://example\\.com\\s*"'
    "\\s+src\\s*=\\s*'\\s*https?://example\\.com\\s*'"

    >>> try:
    ...     __make_full_url_replacer(None, "https://example.com", "bb")
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is None.

    >>> try:
    ...     __make_full_url_replacer(1, "https://example.com", "bb")
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is int, namely '1'.

    >>> try:
    ...     __make_full_url_replacer(coll.append, None, "bb")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __make_full_url_replacer(coll.append, 1, "bb")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __make_full_url_replacer(coll.append, "http://example.com", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     __make_full_url_replacer(coll.append, "http://example.com", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     __make_full_url_replacer(coll.append, "tweise@hfuu.edu.cn", "1")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid scheme 'mailto' for url 'tweise@hfuu.edu.cn'.

    >>> try:
    ...     __make_full_url_replacer(coll.append, "http://example.com", " ")
    ... except ValueError as ve:
    ...     print(ve)
    Cannot replace URL 'http://example.com' with ' '.

    >>> try:
    ...     __make_full_url_replacer(coll.append, "http://example.com",
    ...         ".", None)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is None.

    >>> try:
    ...     __make_full_url_replacer(coll.append, "http://example.com",
    ...         ".", 1)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is int, namely '1'.
    """
    if not callable(collector):
        raise type_error(collector, "collector", call=True)
    if not isinstance(for_markdown, bool):
        raise type_error(for_markdown, "for_markdown", bool)
    url: Final[URL] = URL(url_to_replace)
    if url.scheme not in ("http", "https"):
        raise ValueError(
            f"Invalid scheme {url.scheme!r} for url {url_to_replace!r}.")
    use_repl: Final[str] = str.strip(replace_url_with)
    if str.__len__(use_repl) <= 0:
        raise ValueError(
            f"Cannot replace URL {url!r} with {replace_url_with!r}.")

    use_url: str = f"https?{escape(url[str.__len__(url.scheme):])}"
    if use_repl.startswith(("/", "./")):
        use_url += "?" if use_url.endswith("/") else r"\/?"

    for sr, er, ss, es in chain(__HTML_URL_SEPARTORS, __MD_URL_SEPARTORS) \
            if for_markdown else __HTML_URL_SEPARTORS:
        collector((
            cast(Pattern, re_compile(f"{sr}{use_url}{er}")),
            f"{ss}{use_repl}{es}"))


def __make_replacer(replacers: Iterable[tuple[
        Pattern, Callable[[Match], str] | str]]) -> Callable[[str], str]:
    """
    Make a function that replaces all URL parts in a string.

    :param replacers: the replacers patterns
    :return: the function that can apply the replacers

    >>> coll = list()
    >>> __make_full_url_replacer(coll.append, "https://example.com/log.txt",
    ...                        "https://example.org/log.txt")
    >>> __make_base_url_replacer(coll.append, "https://example.com/", "./")
    >>> f = __make_replacer(coll)
    >>> f("bla <a href='https://example.com/log.txt'>x</a> bla")
    'bla <a href="https://example.org/log.txt">x</a> bla'
    >>> f("bla <a href='https://example.com/xlog.txt'>x</a> bla")
    'bla <a href="./xlog.txt">x</a> bla'

    >>> try:
    ...     f(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     f(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'int' object

    >>> coll.append((None, coll[0][1]))
    >>> try:
    ...     __make_replacer(coll)
    ... except TypeError as te:
    ...     print(te)
    pattern should be an instance of re.Pattern but is None.

    >>> coll[-1] = (1, coll[0][1])
    >>> try:
    ...     __make_replacer(coll)
    ... except TypeError as te:
    ...     print(te)
    pattern should be an instance of re.Pattern but is int, namely '1'.

    >>> coll[-1] = (coll[0][0], None)
    >>> try:
    ...     __make_replacer(coll)
    ... except TypeError as te:
    ...     print(te)
    replacer should be an instance of str or a callable but is None.

    >>> coll[-1] = (coll[0][0], 1)
    >>> try:
    ...     __make_replacer(coll)
    ... except TypeError as te:
    ...     print(te)
    replacer should be an instance of str or a callable but is int, namely '1'.

    >>> try:
    ...     __make_replacer(None)
    ... except TypeError as te:
    ...     print(te)
    replacers should be an instance of typing.Iterable but is None.

    >>> try:
    ...     __make_replacer(1)
    ... except TypeError as te:
    ...     print(te)
    replacers should be an instance of typing.Iterable but is int, namely '1'.

    >>> coll = list()
    >>> __make_full_url_replacer(coll.append, "https://example.com",
    ...                        "https://example.com")
    >>> f = __make_replacer(coll)
    >>> try:
    ...     f("<a href='http://example.com' />")
    ... except ValueError as ve:
    ...     print(str(ve)[:60])
    Endless loop: "<a href='http://example.com' />" -> '<a href=
    """
    if not isinstance(replacers, Iterable):
        raise type_error(replacers, "replacers", Iterable)

    pats: Final[tuple[tuple[Pattern, Callable[[Match], str] | str],
                ...]] = tuple(replacers)
    for pattern, replacer in pats:
        if not isinstance(pattern, Pattern):
            raise type_error(pattern, "pattern", Pattern)
        if not (isinstance(replacer, str) or callable(replacer)):
            raise type_error(replacer, "replacer", str, True)

    def __func(text: str, __pats=pats) -> str:
        out_str: str = str.rstrip(text)  # enforce string
        if str.__len__(out_str) <= 0:
            return ""
        rc: int = 1
        iteration: int = 0
        while rc > 0:
            rc = 0
            for pp, rr in __pats:
                out_str, nn = subn(pp, rr, out_str)
                rc += nn
            iteration += 1
            if iteration > 100:
                raise ValueError(f"Endless loop: {text!r} -> {out_str!r}.")
        return str.rstrip(out_str)  # enforce string

    return cast(Callable[[str], str], __func)


def make_url_replacer(base_urls: Mapping[str, str] | None = None,
                      full_urls: Mapping[str, str] | None = None,
                      for_markdown: bool = True) \
        -> Callable[[str], str]:
    r"""
    Create the url replacers that fix absolute to relative URLs.

    :param base_urls: a mapping of basic urls to shortcuts
    :param full_urls: a mapping of full urls to abbreviations
    :param for_markdown: should the replace be for Markdown (`True`) or for
        HTML only (`False`)
    :returns: a single callable that can process strings and fix the URLs
        therein
    :raises TypeError: if any of the inputs is of the wrong type
    :raises ValueError: if any of the inputs is incorrect

    >>> f = make_url_replacer(None, None)
    >>> f("1")
    '1'

    >>> f = make_url_replacer({"https://example.com/1": "./a/",
    ...                          "https://example.com": "./"},
    ...                         {"https://example.com/1/1.txt": "y.txt",
    ...                          "https://example.com/x/1.txt": "z.txt"})
    >>> f("<a href='http://example.com/1/2.txt' />")
    '<a href="./a/2.txt" />'
    >>> f("<a href='http://example.com/1' />")
    '<a href="./a/" />'
    >>> f("<a href='http://example.com' />")
    '<a href="./" />'
    >>> f("<a href='http://example.com/x.txt' />")
    '<a href="./x.txt" />'
    >>> f("<a href='http://example.com/1/1.txt' />")
    '<a href="y.txt" />'
    >>> f("<a href='http://example.com/x/1.txt' />")
    '<a href="z.txt" />'

    >>> try:
    ...     make_url_replacer(1, None)
    ... except TypeError as te:
    ...     print(te)
    base_urls should be an instance of typing.Mapping but is int, namely '1'.

    >>> try:
    ...     make_url_replacer(None, 1)
    ... except TypeError as te:
    ...     print(te)
    full_urls should be an instance of typing.Mapping but is int, namely '1'.

    >>> try:
    ...     make_url_replacer(None, None, None)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is None.

    >>> try:
    ...     make_url_replacer(None, None, 1)
    ... except TypeError as te:
    ...     print(te)
    for_markdown should be an instance of bool but is int, namely '1'.
    """
    if not isinstance(for_markdown, bool):
        raise type_error(for_markdown, "for_markdown", bool)
    keys: list[tuple[str, bool]] = []

    if base_urls is not None:
        if not isinstance(base_urls, Mapping):
            raise type_error(base_urls, "base_urls", Mapping)
        keys.extend((kk, False) for kk in base_urls)
    if full_urls is not None:
        if not isinstance(full_urls, Mapping):
            raise type_error(full_urls, "full_urls", Mapping)
        keys.extend((kk, True) for kk in full_urls)

    if list.__len__(keys) <= 0:  # no need to do anything
        return lambda s: s

    # long keys and full urls first
    keys.sort(key=lambda tt: (str.__len__(tt[0]), tt[1], tt[0]), reverse=True)
    mappings: list[tuple[Pattern, Callable[[Match], str] | str]] = []
    for k, w in keys:
        if w:
            __make_full_url_replacer(mappings.append, k, full_urls[k],
                                     for_markdown)
        else:
            __make_base_url_replacer(mappings.append, k, base_urls[k],
                                     for_markdown)
    return __make_replacer(mappings)
