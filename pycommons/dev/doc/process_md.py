"""
Process a markdown file in order to make it useful for distribution.

In order to let sphinx properly load and insert the `README.md` file into the
project's documentation, we need to process this file from the GitHub style
markdown to a variant suitable for the myst parser used in sphinx. While we
are at it, we can also turn absolute URLs from the GitHub-`README.md` file
that point to the documentation URL to relative URLs.
"""

from re import Pattern, sub
from re import compile as re_compile
from typing import Any, Callable, Final, Iterable, Mapping, cast

from pycommons.dev.url_replacer import make_url_replacer
from pycommons.types import type_error

#: detects strings of the form [xyz](#123-bla) and gives \1=xyz and \2=bla
__FIX_LINKS: Final[Pattern] = re_compile("(\\[.+?])\\(#\\d+-(.+?)\\)")


def __process_markdown(
        source: Iterable[str], dest: Callable[[str], Any],
        line_processor: Callable[[str], str] = lambda s: s,
        discard_until: str | None = "## 1. Introduction") -> None:
    """
    Process a markdown file in order to make it useful for distribution.

    This process changes the GitHub-style markdown to a format that the myst
    parser, which is used by sphinx, can render properly. This involves
    several issues:

    1. We discard the top-level heading.
    2. We need to move all sub-headings one step up.
    3. Furthermore, we can turn all absolute URLs pointing to the
       documentation website to local references starting with `./`.

    :param source: the source line iterable
    :param dest: the destination callable receiving the output
    :param line_processor: an optional callable for processing lines
    :param discard_until: discard all strings until reaching this line. If
        this is `None`, all lines will be used. If this is not `None`, then
        this will be the first line to be forwarded to `dest`f

    >>> lp = list()
    >>> lpp = make_url_replacer({"https://example.com/": "./"},
    ...                         {"https://example.com/A": "xyz"})
    >>> src = ["![image](https://example.com/1.jp)",
    ...        "# This is `pycommons!`",
    ...        "Table of contents",
    ...        "## 1. Introduction",
    ...        "blabla bla <https://example.com/A>!",
    ...        "## 2. Some More Text",
    ...        "We [also say](https://example.com/z/hello.txt) stuff.",
    ...        "### 2.4. Code Example",
    ...        "```",
    ...        "But [not in code](https://example.com/z/hello.txt).",
    ...        "```",
    ...        "See also [here](#24-code-example)."]
    >>> __process_markdown(src, print, lpp)
    # 1. Introduction
    blabla bla <xyz>!
    # 2. Some More Text
    We [also say](./z/hello.txt) stuff.
    ## 2.4. Code Example
    ```
    But [not in code](https://example.com/z/hello.txt).
    ```
    See also [here](#24-code-example).

    >>> try:
    ...     __process_markdown(None, print, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is None.

    >>> try:
    ...     __process_markdown(1, print, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     __process_markdown([None], print, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     __process_markdown([1], print, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     __process_markdown([""], None, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    dest should be a callable but is None.

    >>> try:
    ...     __process_markdown([""], 1, lambda x: x, "bla")
    ... except TypeError as te:
    ...     print(te)
    dest should be a callable but is int, namely '1'.

    >>> try:
    ...     __process_markdown([""], print, None, "bla")
    ... except TypeError as te:
    ...     print(te)
    line_processor should be a callable but is None.

    >>> try:
    ...     __process_markdown([""], print, 1, "bla")
    ... except TypeError as te:
    ...     print(te)
    line_processor should be a callable but is int, namely '1'.

    >>> try:
    ...     __process_markdown([""], print, lambda x: x, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __process_markdown([""], print, lambda x: x, "")
    ... except ValueError as ve:
    ...     print(ve)
    discard_until cannot be ''.

    >>> __process_markdown([""], print, lambda x: x, None)
    <BLANKLINE>
    """
    if not isinstance(source, Iterable):
        raise type_error(source, "source", Iterable)
    if not callable(dest):
        raise type_error(dest, "dest", call=True)
    if not callable(line_processor):
        raise type_error(line_processor, "line_processor", call=True)

    skip: bool = False
    if discard_until is not None:
        if str.__len__(discard_until) <= 0:
            raise ValueError(f"discard_until cannot be {discard_until!r}.")
        skip = True
    else:
        discard_until = ""

    in_code: bool = False  # we only process non-code lines
    needs_newline: bool = False  # required after image lines
    add_images_anyway: bool = True
    for the_line in source:
        line = str.rstrip(the_line)  # enforce string

        # we skip everything until the introduction section
        if skip:
            the_line_lstr = str.lstrip(the_line)
            if str.__len__(the_line_lstr) <= 0:
                continue
            if the_line_lstr.startswith(discard_until):
                skip = False
            elif the_line_lstr.startswith("[![") and add_images_anyway:
                needs_newline = True
                dest(line)
                continue
            else:
                add_images_anyway = False
                continue

        if needs_newline:
            dest("")
            needs_newline = False

        if in_code:
            if line.startswith("```"):
                in_code = False  # toggle to non-code
        elif line.startswith("```"):
            in_code = True  # toggle to code
        elif line.startswith("#"):
            line = line[1:]  # move all sub-headings one step up
        else:  # e.g., fix all urls via the line processor
            line = str.rstrip(line_processor(line))

        dest(line)


def process_markdown_for_sphinx(
        source: Iterable[str], dest: Callable[[str], Any],
        base_urls: Mapping[str, str] | None = None,
        full_urls: Mapping[str, str] | None = None,
        discard_until: str | None = "## 1. Introduction") -> None:
    """
    Process a markdown file in order to make it useful for distribution.

    This process changes the GitHub-style markdown to a format that the myst
    parser, which is used by sphinx, can render properly. This involves
    several issues:

    1. We discard the top-level heading.
    2. We need to move all sub-headings one step up.
    3. Furthermore, we can turn all absolute URLs pointing to the
       documentation website to local references starting with `./`.
    4. The myst parser drops the numerical prefixes of links, i.e., it tags
       `## 1.2. Hello` with id `hello` instead of `12-hello`. This means that
       we need to fix all references following the pattern `[xxx](#12-hello)`
       to `[xxx](#hello)`.

    :param source: the source line iterable
    :param dest: the destination callable receiving the output
    :param base_urls: a mapping of basic urls to shortcuts
    :param full_urls: a mapping of full urls to abbreviations
    :param discard_until: discard all strings until reaching this line. If
        this is `None`, all lines will be used. If this is not `None`, then
        this will be the first line to be forwarded to `dest`

    >>> lp = list()
    >>> src = ["![image](https://example.com/1.jp)",
    ...        "# This is `pycommons!`",
    ...        "Table of contents",
    ...        "## 1. Introduction",
    ...        "blabla bla <https://example.com/A>!",
    ...        "## 2. Some More Text",
    ...        "We [also say](https://example.com/z/hello.txt) stuff.",
    ...        "### 2.4. Code Example",
    ...        "```",
    ...        "But [not in code](https://example.com/z/hello.txt).",
    ...        "```",
    ...        "See also [here](#24-code-example)."]
    >>> process_markdown_for_sphinx(src, print,
    ...     {"https://example.com/": "./"},
    ...     {"https://example.com/A": "xyz"})
    # 1. Introduction
    blabla bla <xyz>!
    # 2. Some More Text
    We [also say](./z/hello.txt) stuff.
    ## 2.4. Code Example
    ```
    But [not in code](https://example.com/z/hello.txt).
    ```
    See also [here](#code-example).

    >>> try:
    ...     process_markdown_for_sphinx(None, print)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is None.

    >>> try:
    ...     process_markdown_for_sphinx(1, print)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     process_markdown_for_sphinx([None], print)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     process_markdown_for_sphinx([1], print)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'rstrip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     process_markdown_for_sphinx([""], None)
    ... except TypeError as te:
    ...     print(te)
    dest should be a callable but is None.

    >>> try:
    ...     process_markdown_for_sphinx([""], 1)
    ... except TypeError as te:
    ...     print(te)
    dest should be a callable but is int, namely '1'.

    >>> try:
    ...     process_markdown_for_sphinx([""], print, 1, None, "bla")
    ... except TypeError as te:
    ...     print(te)
    base_urls should be an instance of typing.Mapping but is int, namely '1'.

    >>> try:
    ...     process_markdown_for_sphinx([""], print, None, 1, "bla")
    ... except TypeError as te:
    ...     print(te)
    full_urls should be an instance of typing.Mapping but is int, namely '1'.

    >>> try:
    ...     process_markdown_for_sphinx([""], print, None, None, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     process_markdown_for_sphinx([""], print, None, None, "")
    ... except ValueError as ve:
    ...     print(ve)
    discard_until cannot be ''.

    >>> process_markdown_for_sphinx([""], print, None, None, None)
    <BLANKLINE>
    """
    __process_markdown(source, dest, cast(
        Callable[[str], str], lambda s, __l=make_url_replacer(
            base_urls, full_urls): __l(sub(__FIX_LINKS, "\\1(#\\2)",
                                           s))), discard_until)
