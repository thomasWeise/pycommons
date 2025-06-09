"""
Tools for CSV output and input.

Our CSV format tools are intended to read and write structured objects from
and to a comma-separated-values format. This format consists of one header,
where the column titles are included (separated by a :const:`CSV_SEPARATOR`)
and one row per data object, with one value per column.

Different from other CSV processing tools, we want to

1. Permit that data is extracted from / parsed in form of hierarchically
   structured objects.
2. Columns have fixed types based on the object definition.
3. The data read and written is strictly validated during the process.
4. Data can be processed in form of a stream and is not necessarily all loaded
   into memory at once.
5. The order of the columns is unimportant.
6. Useless white space is automatically stripped and ignored.
7. Multiple objects may be written per row, maybe even nested objects, and
   this is signified by "scope" column titles, e.g., something like
   `"weight.min"`, `"weight.median"`, ..., `"age.min"`, `"age.median"`, ...
8. Comments may be added to the header or footer of the CSV file that describe
   the contents of the columns.

The separator is configurable, but by default set to :const:`CSV_SEPARATOR`.
Comments start with a comment start with :const:`COMMENT_START` by default.
"""
from typing import (
    Any,
    Callable,
    Final,
    Generator,
    Iterable,
    Mapping,
    TypeVar,
    cast,
)

from pycommons.ds.sequences import reiterable
from pycommons.strings.chars import NEWLINE, WHITESPACE_OR_NEWLINE
from pycommons.types import check_int_range, type_error
from pycommons.version import __version__ as pycommons_version

#: the default CSV separator
CSV_SEPARATOR: Final[str] = ";"

#: everything after this character is considered a comment
COMMENT_START: Final[str] = "#"

#: the separator to be used between scopes for nested column prefixes
SCOPE_SEPARATOR: Final[str] = "."

#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T")

# mypy: disable-error-code=valid-type
#: the type variable for the CSV output setup
S = TypeVar("S")


def csv_scope(scope: str | None, key: str | None) -> str:
    """
    Combine a scope and a key.

    :param scope: the scope, or `None`
    :param key: the key, or `None`
    :returns: the scope joined with the key

    >>> csv_scope("a", "b")
    'a.b'
    >>> csv_scope("a", None)
    'a'
    >>> csv_scope(None, "b")
    'b'

    >>> try:
    ...     csv_scope(1, "b")
    ... except TypeError as te:
    ...     print(str(te))
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_scope("a", 1)
    ... except TypeError as te:
    ...     print(str(te))
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_scope("a ", "b")
    ... except ValueError as ve:
    ...     print(str(ve))
    Invalid csv scope 'a '.

    >>> try:
    ...     csv_scope("", "b")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid csv scope ''.

    >>> try:
    ...     csv_scope("a", " b")
    ... except ValueError as ve:
    ...     print(str(ve))
    Invalid csv key ' b'.

    >>> try:
    ...     csv_scope("a", "")
    ... except ValueError as ve:
    ...     print(str(ve))
    Invalid csv key ''.

    >>> try:
    ...     csv_scope(None, None)
    ... except ValueError as ve:
    ...     print(str(ve))
    Csv scope and key cannot both be None.
    """
    if (key is not None) and ((str.__len__(key) <= 0) or (
            str.strip(key) != key)):
        raise ValueError(f"Invalid csv key {key!r}.")
    if scope is None:
        if key is None:
            raise ValueError("Csv scope and key cannot both be None.")
        return key
    if (str.__len__(scope) <= 0) or (str.strip(scope) != scope):
        raise ValueError(f"Invalid csv scope {scope!r}.")
    if key is None:
        return scope
    return f"{scope}{SCOPE_SEPARATOR}{key}"


def csv_read(rows: Iterable[str],
             setup: Callable[[dict[str, int]], S],
             parse_row: Callable[[S, list[str]], T],
             separator: str = CSV_SEPARATOR,
             comment_start: str | None = COMMENT_START) \
        -> Generator[T, None, None]:
    r"""
    Read (parse) a sequence of strings as CSV data.

    All lines str :meth:`~str.split` based on the `separator` string and each
    of the resulting strings is stripped via :meth:`~str.strip`.
    The first non-empty line of the data is interpreted as header line.

    This header is passed to the `setup` function in form of a :class:`dict`
    that maps column titles to column indices. This function then returns an
    object of setup data. To each of the rows of CSV data, the function
    `parse_row` is applied. This function receives the object returned by
    `setup` as first argument and the row as list of strings as second
    argument. Each line is therefore :meth:`~str.split` (by the CSV separator)
    and its component :meth:`~str.strip`-ped.
    It is permitted that a line in the CSV file contains fewer columns than
    declared in the header. In this case, the missing columns are set to empty
    strings. Lines that are entirely empty are skipped.

    If `comment_start` is not none, then all text in a line starting at the
    first occurence of `comment_start` is discarted before the line is
    processed.

    If you want to read more complex CSV structures, then using the class
    :class:`CsvReader` and its class method :meth:`CsvReader.read` are a more
    convenient approach. They are wrappers around :func:`csv_read`.

    :param rows: the rows of text
    :param setup: a function which creates an object holding the necessary
        information for row parsing
    :param parse_row: the unction parsing the rows
    :param separator: the string used to separate columns
    :param comment_start: the string starting comments
    :returns: an :class:`Generator` with the parsed data rows
    :raises TypeError: if any of the parameters has the wrong type
    :raises ValueError: if the separator or comment start character are
        incompatible or if the data has some internal error

    >>> def _setup(colidx: dict[str, int]) -> dict[str, int]:
    ...     return colidx

    >>> def _parse_row(colidx: dict[str, int], row: list[str]) -> dict:
    ...         return {x: row[y] for x, y in colidx.items()}

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> for p in csv_read(text, _setup, _parse_row):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> for p in csv_read((t.replace(";", ",") for t in text), _setup,
    ...                   _parse_row, ","):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> for p in csv_read((t.replace(";", "\t") for t in text), _setup,
    ...                   _parse_row, "\t"):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> for p in csv_read(text, _setup, _parse_row, comment_start=None):
    ...     print(p)
    {'a': '# test', 'b': '', 'c': '', 'd': ''}
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}
    {'a': '# 11', 'b': '12', 'c': '', 'd': ''}

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", "5;6", ";8;;9",
    ...         "", "10", "# 11;12"]
    >>> for p in csv_read(text, _setup, _parse_row):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> try:
    ...     list(csv_read(None, _setup, _parse_row))
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is None.

    >>> try:
    ...     list(csv_read(1, _setup, _parse_row))
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is int, namely 1.

    >>> try:
    ...     list(csv_read(text, None, _parse_row))
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is None.

    >>> try:
    ...     list(csv_read(text, 1, _parse_row))
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is int, namely 1.

    >>> try:
    ...     list(csv_read(text, _setup, None))
    ... except TypeError as te:
    ...     print(te)
    parse_row should be a callable but is None.

    >>> try:
    ...     list(csv_read(text, _setup, 1))
    ... except TypeError as te:
    ...     print(te)
    parse_row should be a callable but is int, namely 1.

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, None))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, 1))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, ""))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid separator ''.

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, "-", 1))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, "-", ""))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ''.

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, "-", " "))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ' '.

    >>> try:
    ...     list(csv_read(text, _setup, _parse_row, ";", ";"))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ';'.

    >>> text2 = ["a;b;a;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9"]
    >>> try:
    ...     list(csv_read(text2, _setup, _parse_row))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid column headers: ['a', 'b', 'a', 'd'].

    >>> text2 = ["a;b;c;d", "# test", " 1; 2;3;4", "1;2;3;4;5;6;7", ";8;;9"]
    >>> try:
    ...     list(csv_read(text2, _setup, _parse_row))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid row '1;2;3;4;5;6;7' contains 7 columns, but should have at most 4.
    """
    if not isinstance(rows, Iterable):
        raise type_error(rows, "rows", Iterable)
    if not callable(setup):
        raise type_error(setup, "setup", call=True)
    if not callable(parse_row):
        raise type_error(parse_row, "parse_row", call=True)
    if str.__len__(separator) <= 0:
        raise ValueError(f"Invalid separator {separator!r}.")
    if (comment_start is not None) and (
            (str.__len__(comment_start) <= 0) or (
            str.strip(comment_start) != comment_start) or (
            comment_start in separator)):
        raise ValueError(f"Invalid comment start: {comment_start!r}.")

    col_count: int = -1

    # cannot strip spaces that are part of the separator
    strip: Final[Callable[[str], str]] = str.strip
    stripper: Final[Callable[[str], str]] = strip if (  # type: ignore
        strip(separator) == separator) else str.rstrip  # type: ignore
    find: Final[Callable[[str, str], int]] = str.find  # type: ignore
    split: Final[Callable[[str, str], list[str]]] = str.split  # type: ignore
    listlen: Final[Callable[[list], int]] = list.__len__  # type: ignore
    strlen: Final[Callable[[str], int]] = str.__len__  # type: ignore
    info: S | None = None  # the column definition info generated by setup
    exts: dict[int, list[str]] = {}  # the list of extensions

    for orig_line in rows:  # iterate over all the rows
        line: str = orig_line
        if comment_start is not None:  # delete comment part, if any
            deli = find(line, comment_start)
            if deli >= 0:
                line = line[:deli]
        line = stripper(line)
        if strlen(line) <= 0:
            continue  # nothing to do here

        cols: list[str] = split(line, separator)  # split into columns
        for i, v in enumerate(cols):  # string whitespace off columns
            cols[i] = strip(v)

        if info is None:  # need to load column definition
            col_count = listlen(cols)
            colmap: dict[str, int] = {s: i for i, s in enumerate(cols)}
            if any(strlen(s) <= 0 for s in cols) or (
                    dict.__len__(colmap) != col_count) or (col_count <= 0):
                raise ValueError(f"Invalid column headers: {cols!r}.")
            info = setup(colmap)  # obtain the column setup object
            del colmap  # column map no longer needed
            continue  # proceed with next line

        count: int = listlen(cols)  # get number of columns
        if count > col_count:  # too many columns, throw error
            raise ValueError(
                f"Invalid row {orig_line!r} contains {count} columns, but "
                f"should have at most {col_count}.")
        if count < col_count:  # do we need to add dummy columns?
            add: int = col_count - count  # number of needed columns
            if add not in exts:  # check if in cache
                exts[add] = [""] * add  # add to cache
            cols.extend(exts[add])
        yield parse_row(info, cols)


def pycommons_footer_bottom_comments(
        _: Any, additional: str | None = None) -> Iterable[str]:
    """
    Print standard footer bottom comments for `pycommons`.

    :param _: ignored
    :param additional: an optional line of additional comments
    :returns: an :class:`Iterable` of standard pycommons comments

    >>> for p in pycommons_footer_bottom_comments(""):
    ...     print(p[:70])
    This CSV output has been created using the versatile CSV API of pycomm
    You can find pycommons at https://thomasweise.github.io/pycommons.

    >>> for p in pycommons_footer_bottom_comments("", "Statistics are cool."):
    ...     print(p[:70])
    This CSV output has been created using the versatile CSV API of pycomm
    Statistics are cool.
    You can find pycommons at https://thomasweise.github.io/pycommons.
    """
    yield ("This CSV output has been created using the versatile CSV API of "
           f"pycommons.io.csv, version {pycommons_version}.")
    if (additional is not None) and (str.__len__(additional) > 0):
        yield additional
    yield "You can find pycommons at https://thomasweise.github.io/pycommons."


def __print_comments(comments: Iterable[str] | None,
                     comment_start: str, comment_type: str,
                     empty_first_row: bool) -> Generator[str, None, None]:
    r"""
    Produce the comments after formatting and checking them.

    :param comments: the comment source
    :param comment_start: the comment start string
    :param comment_type: the comment type
    :param empty_first_row: should we put an empty first row?
    :returns: the generator of the comment strings
    :raises TypeError: if an argument is of the wrong type
    :raises ValueError: if comments cannot be placed or contain newlines

    >>> col = ["", "First comment.", "Second comment.", "", "",
    ...        " Third comment. "]
    >>> for p in __print_comments(col, "#", "header", False):
    ...     print(p)
    # First comment.
    # Second comment.
    #
    # Third comment.

    >>> col.clear()
    >>> list(__print_comments(col, "#", "header", True))
    []

    >>> col = ["", "First comment.", "Second comment.", "", "",
    ...        " Third comment. "]
    >>> for p in __print_comments(col, "#", "header", True):
    ...     print(p)
    #
    # First comment.
    # Second comment.
    #
    # Third comment.

    >>> col = ["First comment.", "Second comment.", "", "",
    ...        " Third comment. "]
    >>> for p in __print_comments(col, "#", "header", True):
    ...     print(p)
    #
    # First comment.
    # Second comment.
    #
    # Third comment.

    >>> col = ["", "", "First comment.", "Second comment.", "", "",
    ...        " Third comment. "]
    >>> for p in __print_comments(col, "#", "header", True):
    ...     print(p)
    #
    # First comment.
    # Second comment.
    #
    # Third comment.

    >>> list(__print_comments([], "#", "header", False))
    []
    >>> list(__print_comments([""], "#", "header", False))
    []
    >>> list(__print_comments(["", ""], "#", "header", False))
    []
    >>> list(__print_comments([], "#", "header", True))
    []
    >>> list(__print_comments([""], "#", "header", True))
    []
    >>> list(__print_comments(["", ""], "#", "header", True))
    []

    >>> list(__print_comments(None, "#", "header", True))
    []

    >>> try:
    ...     list(__print_comments(1, "#", "header", True))
    ... except TypeError as te:
    ...     print(te)
    comments should be an instance of typing.Iterable but is int, namely 1.

    >>> try:
    ...     list(__print_comments(["", 1, "Second comment."], "x", "header",
    ...                           False))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     list(__print_comments(["", None, "Second."], "x", "header",
    ...                           False))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     list(__print_comments(["Hello", "x\ny", "z"], "#", "header",
    ...                           False))
    ... except ValueError as ve:
    ...     print(ve)
    A header comment must not contain a newline character, but 'x\ny' does.
    """
    if comments is None:
        return
    if not isinstance(comments, Iterable):
        raise type_error(comments, "comments", Iterable)
    not_first = False
    for cmt in comments:
        xcmt = str.strip(cmt)  # strip and typecheck
        if str.__len__(xcmt) <= 0:
            if not_first:
                yield comment_start
                empty_first_row = not_first = False
            continue
        if any(map(xcmt.__contains__, NEWLINE)):
            raise ValueError(f"A {comment_type} comment must not contain "
                             f"a newline character, but {cmt!r} does.")
        not_first = True
        if empty_first_row:
            yield comment_start
            empty_first_row = False
        yield f"{comment_start} {xcmt}"


def __default_row(s: Iterable[str], t: Any) -> Iterable[str]:
    """
    Generate row data in the default way.

    :param s: the setup object: an :class:`Iterable` of string
    :param t: the row object
    :returns: an :class:`Iterable` of string

    >>> list(__default_row(("a", "b"), ("1", "2")))
    ['1', '2']

    >>> list(__default_row(("a", "b"), {"b": 45, "c": 44, "a": 6}))
    ['6', '45']
    """
    if isinstance(t, Mapping):
        return (str(t[ss]) if ss in t else "" for ss in s)
    return map(str, cast("Iterable[Any]", t))


def csv_write(
        data: Iterable[T],
        column_titles: Iterable[str] | Callable[[S], Iterable[str]] =
        lambda t: cast("Iterable[str]", t),
        get_row: Callable[[S, T], Iterable[str]] =
        cast("Callable[[S, T], Iterable[str]]", __default_row),
        setup: Callable[[Iterable[T]], S] = lambda t: cast("S", t),
        separator: str = CSV_SEPARATOR,
        comment_start: str | None = COMMENT_START,
        header_comments:
        Iterable[str] | Callable[[S], Iterable[str] | None] | None = None,
        footer_comments:
        Iterable[str] | Callable[[S], Iterable[str] | None] | None = None,
        footer_bottom_comments: Iterable[str] | Callable[[
            S], Iterable[str] | None] | None =
        pycommons_footer_bottom_comments) -> Generator[str, None, None]:
    r"""
    Produce a sequence of CSV formatted text.

    The data is provided in form of a :class:`Iterable`. In a first step, the
    function `setup` is invoked and applied to the `data` :class:`Iterable`.
    It can return an object that sort of stores the structure of the data,
    e.g., which columns should be generated and how they should be formatted.

    `column_titles` can either be an :class:`Iterable` with the column titles
    or a :class:`Callable`. In the latter case, the object generated by `setup`
    is passed to `column_titles`, which should generate the column titles.
    These titles are :meth:`~str.strip`-ped and concatenated to use the column
    `separator` string and the resulting header string is passed to `consumer`.

    Then, for each element `e` in the `data` :class:`Iterable`, the function
    `get_row` is invoked. This function receives the setup information object
    (previously returned by `setup`). It should generate one string per
    column. These strings are then each :meth:`~str.strip`-ped and
    concatenated using the column `separator` string. All trailing `separator`
    are removed, but if all strings are empty, at least a single `separator`
    is retained. The resulting string (per row) is again passed to `consumer`.

    Additionally, `header_comments` and `footer_comments` can be `None`, to
    not include any such comments, an :class:`Iterable` of comments, or
    functions to generate row comments as :class:`str`. These are then
    prepended or appends as comment rows before or after all of the
    above, respectively. In that case, `comment_start` is prepended to each
    line. If `comment_start is None`, then these comments are not printed.
    `footer_bottom_comments` provides means to print additional comments
    after the footer comments `comment_start is not None`.

    If you create nested CSV formats, i.e., such where the `setup` function
    invokes the `setup` function of other data, and the data that you receive
    could come from a :class:`~typing.Generator` (or some other one-shot
    :class:`~typing.Iterator`), then you need to make sure to solidify the
    iterable data with :func:`~pycommons.ds.sequences.reiterable`. The
    structure of our CSV output is that `setup` is first invoked and then
    `get_row`. If `setup` already consumes the data away, then `get_row` may
    print nothing. Alternatively, if you apply multiple `setup` routines to
    the same data that extract different information, then the first `setup`
    run may consume all the data, leaving nothing for the second one.

    If you want to write more complex CSV structures, then implementing the
    class :class:`CsvWriter` and using its class method
    :meth:`CsvWriter.write` may be a more convenient solution.
    They are wrappers around :func:`csv_write`.

    :param data: the iterable of data to be written
    :param column_titles: get the column titles
    :param get_row: transform a row of data into a list of strings
    :param setup: the setup function that computes how the data should be
        represented
    :param separator: the string used to separate columns
    :param comment_start: the string starting comments
    :param header_comments: get the comments to be placed above the CSV
        header row -- only invoked if `comment_start is not None`.
    :param footer_comments: get the comments to be placed after the last
        row -- only invoked if `comment_start is not None`.
    :param footer_bottom_comments: get the footer bottom comments, i.e.,
        comments to be printed after all other footers. These commonts may
        include something like the version information of the software used.
        This function is only invoked if `comment_start is not None`.
    :returns: a :class:`Generator` with the rows of CSV text
    :raises TypeError: if any of the parameters has the wrong type
    :raises ValueError: if the separator or comment start character are
        incompatible or if the data has some internal error

    >>> dd = [{"a": 1, "c": 2}, {"b": 6, "c": 8},
    ...       {"a": 4, "d": 12, "b": 3}, {}]

    >>> def __setup(datarows) -> list[str]:
    ...     return sorted({dkey for datarow in datarows for dkey in datarow})

    >>> def __get_row(keyd: list[str], row: dict[str, int]) -> Iterable[str]:
    ...     return map(str, (row.get(key, "") for key in keyd))

    >>> def __get_header_cmt(keyd: list[str]) -> list[str]:
    ...     return ["This is a header comment.", " We have two of it. "]

    >>> def __get_footer_cmt(keyd: list[str]) -> list[str]:
    ...     return [" This is a footer comment."]

    >>> for p in csv_write(dd, lambda x: x, __default_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt,
    ...                    lambda _: ()):
    ...     print(p)
    # This is a header comment.
    # We have two of it.
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    # This is a footer comment.

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt):
    ...     print(p[:70])
    # This is a header comment.
    # We have two of it.
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    # This is a footer comment.
    #
    # This CSV output has been created using the versatile CSV API of pyco
    # You can find pycommons at https://thomasweise.github.io/pycommons.

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ",", "@@", __get_header_cmt, __get_footer_cmt,
    ...                    lambda _: ()):
    ...     print(p)
    @@ This is a header comment.
    @@ We have two of it.
    a,b,c,d
    1,,2
    ,6,8
    4,3,,12
    ,
    @@ This is a footer comment.

    >>> try:
    ...     list(csv_write(None, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(str(te)[:60])
    source should be an instance of any in {typing.Iterable, typ

    >>> try:
    ...     list(csv_write(1, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(str(te)[:60])
    source should be an instance of any in {typing.Iterable, typ

    >>> try:
    ...     list(csv_write(dd, None, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    column_titles should be an instance of typing.Iterable or a callable b

    >>> try:
    ...     list(csv_write(dd, 1, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    column_titles should be an instance of typing.Iterable or a callable b

    >>> try:
    ...     list(csv_write(dd, lambda x: x, None, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    get_row should be a callable but is None.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, 1, __setup,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    get_row should be a callable but is int, namely 1.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, None,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is None.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, 1,
    ...                    ";", "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is int, namely 1.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    None, "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    1, "#", __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", 1, __get_header_cmt, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", 1, __get_footer_cmt))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    header_comments should be an instance of typing.Iterable or a callable

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "", __get_header_cmt, __get_footer_cmt))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ''.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", " ", __get_header_cmt, __get_footer_cmt))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ' '.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "# ", __get_header_cmt, __get_footer_cmt))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: '# '.

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup, ";",
    ...                    None, None):
    ...     print(p)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", None, __get_header_cmt):
    ...     print(p)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", None, footer_comments=__get_footer_cmt,
    ...                    footer_bottom_comments= None):
    ...     print(p)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __get_header_cmt, 1))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    footer_comments should be an instance of typing.Iterable or a callable

    >>> def __err_cmt_1(keyd: list[str]) -> Iterable[str]:
    ...     return ("This is\n a comment with error.", )

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __err_cmt_1))
    ... except ValueError as ve:
    ...     print(str(ve)[:58])
    A header comment must not contain a newline character, but

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", footer_comments=__err_cmt_1,
    ...                    footer_bottom_comments=None))
    ... except ValueError as ve:
    ...     print(str(ve)[:58])
    A footer comment must not contain a newline character, but

    >>> def __empty_cmt(keyd: list[str]) -> Iterable[str]:
    ...     return (" ", )

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", __empty_cmt, __empty_cmt, __empty_cmt):
    ...     print(p)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> for p in csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    ";", "#", footer_comments=__empty_cmt,
    ...                    footer_bottom_comments=lambda _: ()):
    ...     print(p)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> def __error_column_titles_1(keyd: list[str]) -> Iterable[str]:
    ...     return ()

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_1, __get_row,
    ...                    __setup, ";", "#"))
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have zero columns.

    >>> dde = dd.copy()
    >>> dde.append(None)
    >>> try:
    ...     list(csv_write(dde, lambda x: x, __get_row,
    ...                    lambda _: ["a", "b", "c", "d"],
    ...                    ";", "#", footer_comments=__empty_cmt,
    ...                    footer_bottom_comments=lambda _: ()))
    ... except TypeError as te:
    ...     print(te)
    data element should be an instance of object but is None.

    >>> def __error_column_titles_2(keyd: list[str]) -> Iterable[str]:
    ...     return (" ", )

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_2, __get_row, __setup,
    ...                    ";", "#"))
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title ' ', must neither be empty no

    >>> def __error_column_titles_3(keyd: list[str]) -> Iterable[str]:
    ...     return ("bla\nblugg", )

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_3, __get_row, __setup,
    ...                    ";", "#"))
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title 'bla\nblugg', must neither be

    >>> def __error_column_titles_4(keyd: list[str]) -> Iterable[str]:
    ...     return (None, )

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_4, __get_row, __setup,
    ...                    ";", "#"))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_column_titles_5(keyd: list[str]) -> Iterable[str]:
    ...     return (1, )

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_5, __get_row, __setup,
    ...                    ";", "#"))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> def __error_column_titles_6(keyd: list[str]) -> Iterable[str]:
    ...     return ("a", "b", "c", "a")

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_6, __get_row, __setup,
    ...                    ";", "#"))
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have duplicated columns: ['a', 'b', 'c', 'a'].

    >>> def __error_column_titles_7(keyd: list[str]) -> Iterable[str]:
    ...     return ("a", "b", "c;4")

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_7, __get_row, __setup,
    ...                    ";", "#"))
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'c;4', must neither be empty

    >>> def __error_column_titles_8(keyd: list[str]) -> Iterable[str]:
    ...     return ("a", "b#x", "c")

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_8, __get_row, __setup,
    ...                    ";", "#"))
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'b#x', must neither be empty

    >>> def __error_row_1(keyd: list[str], row: dict[str, int]):
    ...     return ("bla", None, "blubb")

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __error_row_1,
    ...                    __setup, ";", "#",
    ...                    footer_bottom_comments=lambda _, __: None))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_row_2(keyd: list[str], row: dict[str, int]):
    ...     return ("bla", 2.3, "blubb")

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __error_row_2,
    ...                    __setup, ";", "#",
    ...                    footer_bottom_comments=lambda _: None))
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'float' object

    >>> def __error_row_3(keyd: list[str], row: dict[str, int]):
    ...     return ("bla", "x\ny", "blubb")

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __error_row_3,
    ...                    __setup, ";", "#",
    ...                    footer_bottom_comments=lambda _: None))
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column value 'x\ny', cannot contain any of

    >>> def __error_row_4(keyd: list[str], row: dict[str, int]):
    ...     return ("bla", "x#", "blubb")

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __error_row_4,
    ...                    __setup, ";", "#",
    ...                    footer_bottom_comments=lambda _: None))
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column value 'x#', cannot contain any of [

    >>> def __error_row_5(keyd: list[str], row: dict[str, int]):
    ...     return ("bla", "x;#", "blubb")

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __error_row_5,
    ...                    __setup, ";", "#"))
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column value 'x;#', cannot contain any of

    >>> def __error_column_titles_9(keyd: list[str]) -> Iterable[str]:
    ...     return ("a", )

    >>> def __error_row_6(keyd: list[str], row: dict[str, int]):
    ...     return ("", )

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_9, __error_row_6,
    ...                    __setup, ";", "#"))
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have empty row in a single-column format, but got [''].

    >>> def __error_row_7(keyd: list[str], row: dict[str, int]):
    ...     return ("x", "y")

    >>> try:
    ...     list(csv_write(dd, __error_column_titles_9, __error_row_7,
    ...                    __setup, ";", "#"))
    ... except ValueError as ve:
    ...     print(ve)
    Too many columns in ['x', 'y'], should be 1.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    "", "#", footer_comments=__err_cmt_1))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid separator ''.

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    "x", "#", footer_comments=1))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    footer_comments should be an instance of typing.Iterable or a callable

    >>> try:
    ...     list(csv_write(dd, lambda x: x, __get_row, __setup,
    ...                    "x", "#", footer_bottom_comments=1))
    ... except TypeError as te:
    ...     print(str(te)[:70])
    footer_bottom_comments should be an instance of typing.Iterable or a c

    >>> ddx = [{"a": 1, "c": 2}, None,
    ...        {"a": 4, "d": 12, "b": 3}, {}]
    >>> def __error_row_9(_, __):
    ...     return ("1", "2", "3", "4")
    >>> def __error_row_10(_):
    ...     __error_row_9(1, 2)

    >>> try:
    ...     list(csv_write(ddx, __error_row_10,
    ...                    __error_row_9, lambda x: x, ";", "#"))
    ... except TypeError as te:
    ...     print(te)
    'NoneType' object is not iterable
    """
    if not (isinstance(column_titles, Iterable) or callable(column_titles)):
        raise type_error(column_titles, "column_titles", Iterable, call=True)
    if not callable(get_row):
        raise type_error(get_row, "get_row", call=True)
    if not callable(setup):
        raise type_error(setup, "setup", call=True)
    if str.__len__(separator) <= 0:
        raise ValueError(f"Invalid separator {separator!r}.")
    forbidden_marker: Final[set[str]] = set(NEWLINE)
    forbidden_marker.add(separator)
    if comment_start is not None:
        if (str.__len__(comment_start) <= 0) or (
                str.strip(comment_start) != comment_start) or (
                comment_start in separator):
            raise ValueError(f"Invalid comment start: {comment_start!r}.")
        forbidden_marker.add(comment_start)
    if (header_comments is not None) and (not (isinstance(
            header_comments, Iterable) or callable(header_comments))):
        raise type_error(
            header_comments, "header_comments", Iterable, call=True)
    if (footer_comments is not None) and (not (isinstance(
            footer_comments, Iterable) or callable(footer_comments))):
        raise type_error(
            footer_comments, "footer_comments", Iterable, call=True)
    if (footer_bottom_comments is not None) and (not (isinstance(
            footer_bottom_comments, Iterable) or callable(
            footer_bottom_comments))):
        raise type_error(footer_bottom_comments,
                         "footer_bottom_comments", Iterable, call=True)

    data = reiterable(data)  # make sure we can iterate over the data twice
    setting: Final[S] = setup(data)
    forbidden: Final[list[str]] = sorted(forbidden_marker)

    # first put header comments
    if (comment_start is not None) and (header_comments is not None):
        yield from __print_comments(
            header_comments(setting) if callable(header_comments)
            else header_comments, comment_start, "header", False)

    # now process the column titles
    collected: list[str] = list(
        column_titles(setting) if callable(column_titles) else column_titles)
    col_count: Final[int] = list.__len__(collected)
    if col_count <= 0:
        raise ValueError("Cannot have zero columns.")
    for i, col in enumerate(collected):
        collected[i] = xcol = str.strip(col)
        if (str.__len__(xcol) <= 0) or any(map(xcol.__contains__, forbidden)):
            raise ValueError(f"Invalid column title {col!r}, must neither be"
                             f" empty nor contain any of {forbidden!r}.")
    if set.__len__(set(collected)) != col_count:
        raise ValueError(f"Cannot have duplicated columns: {collected!r}.")
    yield separator.join(collected)

    # now do the single rows
    for element in data:
        if element is None:
            raise type_error(element, "data element", object)
        collected.clear()
        collected.extend(get_row(setting, element))
        list_len: int = list.__len__(collected)
        if list_len > col_count:
            raise ValueError(
                f"Too many columns in {collected!r}, should be {col_count}.")
        last_non_empty: int = -1
        for i, col in enumerate(collected):
            collected[i] = xcol = str.strip(col)
            if any(map(xcol.__contains__, forbidden)):
                raise ValueError(f"Invalid column value {col!r}, cannot "
                                 f"contain any of {forbidden!r}.")
            if str.__len__(xcol) > 0:
                last_non_empty = i + 1
        if last_non_empty < list_len:
            if last_non_empty <= 0:
                if col_count <= 1:
                    raise ValueError(
                        f"Cannot have empty row in a single-column format, "
                        f"but got {collected!r}.")
                yield separator
                continue
            del collected[last_non_empty:]
        yield separator.join(collected)

    # finally put footer comments
    if comment_start is not None:
        empty_next: bool = False
        if footer_comments is not None:
            for c in __print_comments(footer_comments(setting) if callable(
                    footer_comments) else footer_comments, comment_start,
                    "footer", False):
                yield c
                empty_next = True
        if footer_bottom_comments is not None:
            yield from __print_comments(
                footer_bottom_comments(setting) if callable(
                    footer_bottom_comments) else footer_bottom_comments,
                comment_start, "footer bottom", empty_next)


def csv_str_or_none(data: list[str | None] | None,
                    index: int | None) -> str | None:
    """
    Get a string or `None` from a data row.

    This function is a shortcut for when data elements or columns are
    optional. If `index` is `None` or outside of the valid index range of the
    list `data`, then `None` is returned. If `data` itself is `None` or the
    element at index `index` is the empty string, then `None` is returned.
    Only if `data` and `index` are both not `None` and `index` is a valid
    index into `data` and the element at index `index` in `data` is not the
    empty string, then this element is returned. In other words, this is a
    very tolerant function to handle optional data and to return `None` if the
    data is not present. The function :func:`csv_val_or_none` further extends
    this function by converting the data to another data type if it is
    present.

    :param data: the data
    :param index: the index, if any
    :returns: the string or nothing

    >>> ddd = ["a", "b", "", "d"]
    >>> print(csv_str_or_none(ddd, 0))
    a
    >>> print(csv_str_or_none(ddd, 1))
    b
    >>> print(csv_str_or_none(ddd, 2))
    None
    >>> print(csv_str_or_none(ddd, 3))
    d
    >>> print(csv_str_or_none(ddd, None))
    None
    >>> print(csv_str_or_none(ddd, 10))
    None
    >>> print(csv_str_or_none(ddd, -1))
    None
    >>> print(csv_str_or_none(None, 0))
    None
    """
    if (index is None) or (data is None):
        return None
    if 0 <= index <= list.__len__(data):
        d: str = data[index]
        return None if (d is None) or (str.__len__(d) <= 0) else d
    return None


#: a type variable for :func:`csv_val_or_none`.
U = TypeVar("U")


def csv_val_or_none(data: list[str | None] | None, index: int | None,
                    conv: Callable[[str], U]) -> U | None:
    """
    Get a value or `None`.

    See :func:`csv_str_or_none` allows us to extract an optional data element
    from a CSV row and get `None` if the element is not present or if the
    `index` is `None` or outside of the valid range. In case the data is
    present and not the empty string, then the function `conv` is invoked to
    convert it to another value. Otherwise, `None` is returned.

    :param data: the data
    :param index: the index
    :param conv: the conversation function
    :returns: the object

    >>> ddd = ["11", "22", "", "33"]
    >>> print(csv_val_or_none(ddd, 0, int))
    11
    >>> print(csv_val_or_none(ddd, 1, int))
    22
    >>> print(csv_val_or_none(ddd, 2, int))
    None
    >>> print(csv_val_or_none(ddd, 3, int))
    33
    >>> print(csv_val_or_none(ddd, None, int))
    None
    """
    t: Final[str | None] = csv_str_or_none(data, index)
    return None if t is None else conv(t)


def csv_column(columns: dict[str, int], key: str,
               remove_col: bool = True) -> int:
    """
    Get the index of a CSV column.

    This function will extract the index of a column from a column description
    map. The index will be checked whether it is in a valid range and
    returned. If no column fitting to `key` exists, this function will throw a
    `KeyError`. If `remove_col` is `True` and a column fitting to `key`
    exists, then this column will be deleted from `columns`.

    :param columns: the columns set
    :param key: the key
    :param remove_col: should we remove the column?
    :returns: the column
    :raises TypeError: if any of the parameters is not of the prescribed type
    :raises ValueError: if the column or key are invalid
    :raises KeyError: if no column of the name `key` eixists

    >>> csv_column({"a": 5}, "a")
    5

    >>> cols = {"a": 5, "b": 7}
    >>> csv_column(cols, "a", False)
    5
    >>> cols
    {'a': 5, 'b': 7}
    >>> csv_column(cols, "a", True)
    5
    >>> cols
    {'b': 7}

    >>> try:
    ...     csv_column({"a": 5}, "b")
    ... except KeyError as ke:
    ...     print(ke)
    'b'

    >>> try:
    ...     csv_column({"a": 5}, "a", "3")
    ... except TypeError as te:
    ...     print(te)
    remove_col should be an instance of bool but is str, namely '3'.

    >>> try:
    ...     csv_column(None, "b")
    ... except TypeError as te:
    ...     print(str(te)[:50])
    descriptor '__getitem__' for 'dict' objects doesn'

    >>> try:
    ...     csv_column({"a": 5}, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_column({"a": -1}, "a")
    ... except ValueError as ve:
    ...     print(ve)
    a=-1 is invalid, must be in 0..1000000.

    >>> try:
    ...     csv_column({"a": -1}, "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid key ''.
    """
    if str.__len__(key) <= 0:
        raise ValueError(f"Invalid key {key!r}.")
    if not isinstance(remove_col, bool):
        raise type_error(remove_col, "remove_col", bool)
    res: Final[int] = check_int_range(dict.__getitem__(
        columns, key), key, 0, 1_000_000)
    if remove_col:
        dict.__delitem__(columns, key)
    return res


def csv_column_or_none(columns: dict[str, int] | None = None,
                       key: str | None = None,
                       remove_col: bool = True) -> int | None:
    """
    Get an optional CSV column index.

    This function will extract the index of a column from a column description
    map. The index will be checked whether it is in a valid range and
    returned. If no column fitting to `key` exists, this function returns
    `None`. If `remove_col` is `True` and a column fitting to `key` exists,
    then this column will be deleted from `columns`.

    :param columns: the columns
    :param key: the key
    :param remove_col: should we remove the column?
    :returns: the column, or `None` if none was found
    :raises TypeError: if any of the parameters is not of the prescribed type
    :raises ValueError: if the column or key are invalid

    >>> csv_column_or_none({"a": 5}, "a")
    5

    >>> cols = {"a": 5, "b": 7}
    >>> csv_column_or_none(cols, "a", False)
    5
    >>> cols
    {'a': 5, 'b': 7}
    >>> csv_column_or_none(cols, "a", True)
    5
    >>> cols
    {'b': 7}

    >>> try:
    ...     csv_column_or_none({"a": 5}, "a", "3")
    ... except TypeError as te:
    ...     print(te)
    remove_col should be an instance of bool but is str, namely '3'.

    >>> print(csv_column_or_none({"a": 5}, "b"))
    None

    >>> print(csv_column_or_none(None, "b"))
    None

    >>> print(csv_column_or_none({"a": 5}, None))
    None

    >>> print(csv_column_or_none({"a": 5}, ""))
    None

    >>> try:
    ...     csv_column({"a": 5}, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_column({"a": -1}, "a")
    ... except ValueError as ve:
    ...     print(ve)
    a=-1 is invalid, must be in 0..1000000.
    """
    if not isinstance(remove_col, bool):
        raise type_error(remove_col, "remove_col", bool)
    if (key is None) or (columns is None) or (str.__len__(key) <= 0):
        return None
    res: Final[int | None] = dict.get(columns, key)
    if res is None:
        return None
    check_int_range(res, key, 0, 1_000_000)
    if remove_col:
        dict.__delitem__(columns, key)
    return res


def csv_select_scope(
        conv: Callable[[dict[str, int]], U],
        columns: dict[str, int],
        scope: str | None = None,
        additional: Iterable[tuple[str, int]] = (),
        skip_orig_key: Callable[[str], bool] = lambda _: False,
        skip_final_key: Callable[[str], bool] = lambda _: False,
        skip_col: Callable[[int], bool] = lambda _: False,
        include_scope: bool = True,
        remove_cols: bool = True) -> U:
    """
    Get all the columns of a given scope and pass them to the function `conv`.

    This function is intended for selecting some keys from a column set and
    pass them as parameters to a constructor of a CSV reader. It can do this
    selection based on a `scope` prefix which is then removed from the column
    names before passing them into the constructor. If no column matches, this
    function throws a :class:`ValueError`.
    All columns that are passed on to `conv` are deleted from `columns` if
    `remove_cols == True`, which is the default.

    :param conv: the function to which the selected columns should be passed,
        and that creates the return value
    :param columns: the existing columns
    :param scope: the scope, or `None` or the empty string to select all
        columns
    :param skip_orig_key: a function that returns `True` for any original,
        unchanged key in `columns` that should be ignored and that
        returns `False` if the key can be processed normally (i.e., if we can
        check if it starts with the given scope and move on)
    :param skip_final_key: a function that returns `True` for any key in
        `columns` that would fall into the right scope but that should still
        be ignored. This function receives the key without the scope prefix.
    :param skip_col: any column that should be ignored
    :param additional: the additional columns to add *if* some keys/columns
        remain after all the transformation and selection
    :param include_scope: if scope appears as a lone column, should we
        include it?
    :param remove_cols: should we remove all selected columns?
    :returns: The result of the function `conv` applied to all matching
        columns (and those in `additional` are appended to them)
    :raises ValueError: if no columns could be selected
    :raises TypeError: if any of the elements passed in is of the wrong type

    >>> csv_select_scope(lambda x: x, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "")
    {'a.x': 1, 'a.y': 2, 'a': 3, 'b': 4, 'b.t': 5}

    >>> try:
    ...     csv_select_scope(print, {"a.x": 1, "a.y": 2}, "v")
    ... except ValueError as ve:
    ...     print(ve)
    Did not find sufficient data of scope 'v' in {'a.x': 1, 'a.y': 2}.

    >>> try:
    ...     csv_select_scope(print, {}, "v")
    ... except ValueError as ve:
    ...     print(ve)
    Did not find sufficient data of scope 'v' in {}.
    """
    res: Final[U | None] = csv_select_scope_or_none(
        conv, columns, scope, additional, skip_orig_key, skip_final_key,
        skip_col, include_scope, remove_cols) \
        if dict.__len__(columns) > 0 else None
    if res is None:
        raise ValueError("Did not find sufficient data of "
                         f"scope {scope!r} in {columns!r}.")
    return res


def csv_select_scope_or_none(
        conv: Callable[[dict[str, int]], U],
        columns: dict[str, int] | None,
        scope: str | None = None,
        additional: Iterable[tuple[str, int]] = (),
        skip_orig_key: Callable[[str], bool] = lambda _: False,
        skip_final_key: Callable[[str], bool] = lambda _: False,
        skip_col: Callable[[int], bool] = lambda _: False,
        include_scope: bool = True,
        remove_cols: bool = True) -> U | None:
    """
    Get all the columns of a given scope and pass them to the function `conv`.

    This function is intended for selecting some keys from a column set and
    pass them as parameters to a constructor of a CSV reader. It can do this
    selection based on a `scope` prefix which is then removed from the column
    names before passing them into the constructor. If no column matches, this
    function returns `None`.
    All columns that are passed on to `conv` are deleted from `columns` if
    `remove_cols == True`, which is the default.

    :param conv: the function to which the selected columns should be passed,
        if any, and that - in this case, returns the return value of this
        function
    :param columns: the existing columns
    :param scope: the scope, or `None` or the empty string to select all
        columns
    :param skip_orig_key: a function that returns `True` for any original,
        unchanged key in `columns` that should be ignored and that
        returns `False` if the key can be processed normally (i.e., if we can
        check if it starts with the given scope and move on)
    :param skip_final_key: a function that returns `True` for any key in
        `columns` that would fall into the right scope but that should still
        be ignored. This function receives the key without the scope prefix.
    :param skip_col: any column that should be ignored
    :param additional: the additional columns to add *if* some keys/columns
        remain after all the transformation and selection
    :param include_scope: if scope appears as a lone column, should we
        include it?
    :param remove_cols: should we remove all selected columns?
    :returns: `None` if no keys fall into the provided scope does not have any
        keys matching it in `columns`. The result of `conv` otherwise, i.e.,
        if there are matching columns, these are selected (and those in
        `additional` are appended to them) and these are then passed to `conv`
        and the result of `conv` is returned

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a")
    {'x': 1, 'y': 2, 'a': 3}

    >>> exa1 = {"a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}
    >>> csv_select_scope_or_none(print, exa1, "a", remove_cols=False)
    {'x': 1, 'y': 2, 'a': 3}
    >>> exa1
    {'a.x': 1, 'a.y': 2, 'a': 3, 'b': 4, 'b.t': 5}
    >>> csv_select_scope_or_none(print, exa1, "a", remove_cols=True)
    {'x': 1, 'y': 2, 'a': 3}
    >>> exa1
    {'b': 4, 'b.t': 5}
    >>> csv_select_scope_or_none(print, exa1, "b", remove_cols=True)
    {'b': 4, 't': 5}
    >>> exa1
    {}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "")
    {'a.x': 1, 'a.y': 2, 'a': 3, 'b': 4, 'b.t': 5}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, None)
    {'a.x': 1, 'a.y': 2, 'a': 3, 'b': 4, 'b.t': 5}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...     include_scope=False)
    {'x': 1, 'y': 2}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b")
    {'b': 4, 't': 5}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b",
    ...     additional=(('z', 23), ('v', 45)))
    {'b': 4, 't': 5, 'z': 23, 'v': 45}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b",
    ...     additional=(('t', 23), ('v', 45)))
    {'b': 4, 't': 5, 'v': 45}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...     additional=(('x', 44), ('v', 45)))
    {'x': 1, 'y': 2, 'a': 3, 'v': 45}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b",
    ...     additional=(('z', 23), ('v', 45)),
    ...     skip_col=lambda c: c == 23)
    {'b': 4, 't': 5, 'v': 45}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b",
    ...     additional=(('z', 23), ('v', 45)),
    ...     skip_orig_key=lambda ok: ok == "b.t")
    {'b': 4, 'z': 23, 'v': 45}

    >>> csv_select_scope_or_none(print, {
    ...     "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "b",
    ...     additional=(('z', 23), ('v', 45)),
    ...     skip_final_key=lambda fk: fk == "z")
    {'b': 4, 't': 5, 'v': 45}

    >>> print(csv_select_scope_or_none(print, {}, "a"))
    None

    >>> print(csv_select_scope_or_none(print, {}, None))
    None

    >>> print(csv_select_scope_or_none(print, None, None))
    None

    >>> print(csv_select_scope_or_none(print, {"a.x": 45}, "a",
    ...         skip_col=lambda c: c == 45))
    None

    >>> try:
    ...     csv_select_scope_or_none(None, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a")
    ... except TypeError as te:
    ...     print(te)
    conv should be a callable but is None.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         remove_cols=1)
    ... except TypeError as te:
    ...     print(te)
    remove_cols should be an instance of bool but is int, namely 1.

    >>> try:
    ...     csv_select_scope_or_none("x", {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a")
    ... except TypeError as te:
    ...     print(te)
    conv should be a callable but is str, namely 'x'.

    >>> try:
    ...     csv_select_scope_or_none(print, "x", "a")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'dict' object but received a 'str'

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, int)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'type'

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=2)
    ... except TypeError as te:
    ...     print(str(te)[:-7])
    additional should be an instance of typing.Iterable but is int, na

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=((1, 2), ))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=(None, ))
    ... except TypeError as te:
    ...     print(te)
    cannot unpack non-iterable NoneType object

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=(("yx", "a"), ))
    ... except TypeError as te:
    ...     print(te)
    yx should be an instance of int but is str, namely 'a'.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=(("yx", -2), ))
    ... except ValueError as ve:
    ...     print(ve)
    yx=-2 is invalid, must be in 0..1000000.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "a.b": -4, "b.t": 5}, "a")
    ... except ValueError as ve:
    ...     print(ve)
    a.b=-4 is invalid, must be in 0..1000000.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         skip_col=None)
    ... except TypeError as te:
    ...     print(te)
    skip_col should be a callable but is None.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         skip_orig_key=None)
    ... except TypeError as te:
    ...     print(te)
    skip_orig_key should be a callable but is None.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         skip_final_key=None)
    ... except TypeError as te:
    ...     print(te)
    skip_final_key should be a callable but is None.

    >>> try:
    ...     csv_select_scope(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         include_scope=3)
    ... except TypeError as te:
    ...     print(te)
    include_scope should be an instance of bool but is int, namely 3.

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, 4)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_select_scope_or_none(print, 11)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'dict' object but received a 'int'

    >>> try:
    ...     csv_select_scope_or_none(print, {
    ...         "a.x": 1, "a.y": 2, "a": 3, "b": 4, "b.t": 5}, "a",
    ...         additional=(("", 2), ))
    ... except ValueError as ve:
    ...     print(ve)
    Invalid additional column ''.
    """
    if not callable(conv):
        raise type_error(conv, "conv", call=True)
    if not callable(skip_orig_key):
        raise type_error(skip_orig_key, "skip_orig_key", call=True)
    if not callable(skip_final_key):
        raise type_error(skip_final_key, "skip_final_key", call=True)
    if not isinstance(additional, Iterable):
        raise type_error(additional, "additional", Iterable)
    if not isinstance(include_scope, bool):
        raise type_error(include_scope, "include_scope", bool)
    if not callable(skip_col):
        raise type_error(skip_col, "skip_col", call=True)
    if not isinstance(remove_cols, bool):
        raise type_error(remove_cols, "remove_cols", bool)

    if (columns is None) or (dict.__len__(columns) <= 0):
        return None
    selection: Final[list[tuple[str, str, int]]] = [
        (k, k, v) for k, v in columns.items()
        if not (skip_orig_key(k) or skip_col(v))]
    sel_len: Final[int] = list.__len__(selection)
    if sel_len <= 0:
        return None

    if (scope is not None) and (str.__len__(scope) > 0):
        use_scope: Final[str] = f"{scope}{SCOPE_SEPARATOR}"
        usl: Final[int] = str.__len__(use_scope)
        for i in range(sel_len - 1, -1, -1):
            k, _, v = selection[i]
            if str.startswith(k, use_scope):
                use_key = k[usl:]
                if not skip_final_key(use_key):
                    list.__setitem__(selection, i, (k, use_key, v))
                    continue
            elif include_scope and (k == scope):
                if not skip_final_key(k):
                    continue
            list.__delitem__(selection, i)

    if list.__len__(selection) <= 0:
        return None

    if remove_cols:
        for kv in selection:
            dict.__delitem__(columns, kv[0])

    subset: Final[dict[str, int]] = {
        kv[1]: check_int_range(
            kv[2], kv[0], 0, 1_000_000) for kv in selection}

    for kkk, vvv in additional:
        if str.__len__(kkk) <= 0:
            raise ValueError(f"Invalid additional column {kkk!r}.")
        if skip_final_key(kkk) or skip_col(vvv):
            continue
        if kkk not in subset:
            subset[kkk] = check_int_range(vvv, kkk, 0, 1_000_000)
    return conv(subset)


class CsvReader[T]:
    """
    A base class for CSV readers.

    Using this class and its :meth:`read` class method provides for a more
    elegant way to construct nested and combined CSV formats compared to
    creating classes and handing their methods to :func:`csv_read`.

    >>> class R(CsvReader):
    ...     def __init__(self, columns: dict[str, int]) -> None:
    ...         super().__init__(columns)
    ...         self.cols = columns
    ...     def parse_row(self, row: list[str]) -> dict:
    ...         return {x: row[y] for x, y in self.cols.items()}

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> for p in R.read(text):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> text = ["a,b,c,d", "v test", " 1, 2,3,4", " 5 ,6 ", ",8,,9",
    ...         "", "10", "v 11,12"]

    >>> for p in R.read(text, separator=',', comment_start='v'):
    ...     print(p)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> class S(CsvReader):
    ...     def __init__(self, columns: dict[str, int], add: str) -> None:
    ...         super().__init__(columns)
    ...         self.cols = columns
    ...         self.s = add
    ...     def parse_row(self, row: list[str]) -> dict:
    ...         return {x: self.s + row[y] for x, y in self.cols.items()}

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> for p in S.read(text, add="b"):
    ...     print(p)
    {'a': 'b1', 'b': 'b2', 'c': 'b3', 'd': 'b4'}
    {'a': 'b5', 'b': 'b6', 'c': 'b', 'd': 'b'}
    {'a': 'b', 'b': 'b8', 'c': 'b', 'd': 'b9'}
    {'a': 'b10', 'b': 'b', 'c': 'b', 'd': 'b'}

    >>> ccc = S({"a": 1}, add="x")
    >>> print(ccc.parse_optional_row(None))
    None
    >>> print(S.parse_optional_row(None, None))
    None
    >>> print((ccc).parse_optional_row(["x", "y"]))
    {'a': 'xy'}

    >>> try:
    ...     CsvReader("x")
    ... except TypeError as te:
    ...     print(te)
    columns should be an instance of dict but is str, namely 'x'.

    >>> try:
    ...     CsvReader({"a": 1}).parse_row(["a"])
    ... except NotImplementedError as nie:
    ...     print(type(nie))
    <class 'NotImplementedError'>
    """

    def __init__(self, columns: dict[str, int]) -> None:
        """
        Create the CSV reader.

        :param columns: the columns
        :raises TypeError: if `columns` is not a :class:`dict`
        """
        super().__init__()
        if not isinstance(columns, dict):
            raise type_error(columns, "columns", dict)

    def parse_row(self, data: list[str]) -> T:
        """
        Parse a row of data.

        :param data: the data row
        :returns: the object representing the row
        :raises NotImplementedError: because it must be overridden
        :raises ValueError: should raise a :class:`ValueError` if the row is
            incomplete or invalid
        """
        raise NotImplementedError

    def parse_optional_row(self, data: list[str] | None) -> T | None:
        """
        Parse a row of data that may be incomplete or empty.

        The default implementation of this method returns `None` if the data
        row is `None`, or if `self` is `None`, which should never happen.
        Otherwise, it calls :meth:`parse_row`, which will probably raise a
        :class:`ValueError`.

        :param data: the row of data that may be empty
        :returns: an object constructed from the partial row, if possible,
            or `None`
        """
        if (self is None) or (data is None):
            return None
        return self.parse_row(data)

    @classmethod
    def read(cls: type["CsvReader"], rows: Iterable[str],
             separator: str = CSV_SEPARATOR,
             comment_start: str | None = COMMENT_START,
             **kwargs) -> Generator[T, None, None]:
        """
        Parse a stream of CSV data.

        This class method creates a single new instance of `cls` and passes it
        the column names/indices as well as any additional named arguments of
        this method into the constructor. It then uses the method
        :meth:`parse_row` of the class to parse the row data to generate the
        output stream.

        It offers a more convenient wrapper around :func:`csv_read` for cases
        where it makes more sense to implement the parsing functionality in a
        class.

        :param rows: the rows of strings with CSV data
        :param separator: the separator character
        :param comment_start: the comment start character
        """
        def __creator(y: dict[str, int], __c=cls,  # pylint: disable=W0102
                      __x=kwargs) -> "CsvReader":  # noqa  # type: ignore
            return cls(y, **__x)  # noqa  # type: ignore

        yield from csv_read(rows=rows,
                            setup=__creator,
                            parse_row=cls.parse_row,  # type: ignore
                            separator=separator,
                            comment_start=comment_start)


class CsvWriter[T]:
    """
    A base class for structured CSV writers.

    >>> class W(CsvWriter):
    ...     def __init__(self, data: Iterable[dict[str, int]],
    ...                  scope: str | None = None) -> None:
    ...         super().__init__(data, scope)
    ...         self.rows = sorted({dkey for datarow in data
    ...                                 for dkey in datarow})
    ...     def get_column_titles(self) -> Iterable[str]:
    ...         return self.rows
    ...     def get_row(self, row: dict[str, int]) -> Iterable[str]:
    ...         return map(str, (row.get(key, "") for key in self.rows))
    ...     def get_header_comments(self) -> list[str]:
    ...         return ["This is a header comment.", " We have two of it. "]
    ...     def get_footer_comments(self) -> list[str]:
    ...         return [" This is a footer comment."]

    >>> dd = [{"a": 1, "c": 2}, {"b": 6, "c": 8},
    ...       {"a": 4, "d": 12, "b": 3}, {}]

    >>> for p in W.write(dd):
    ...     print(p[:-8] if "version" in p else p)
    # This is a header comment.
    # We have two of it.
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    # This is a footer comment.
    #
    # This CSV output has been created using the versatile CSV API of \
pycommons.io.csv, version
    # You can find pycommons at https://thomasweise.github.io/pycommons.

    >>> class W2(CsvWriter):
    ...     def __init__(self, data: Iterable[dict[str, int]],
    ...                  scope: str | None = None) -> None:
    ...         super().__init__(data, scope)
    ...         self.rows = sorted({dkey for datarow in data
    ...                             for dkey in datarow})
    ...     def get_column_titles(self) -> Iterable[str]:
    ...         return self.rows if self.scope is None else [
    ...             f"{self.scope}.{r}" for r in self.rows]
    ...     def get_row(self, row: dict[str, int]) -> Iterable[str]:
    ...         return map(str, (row.get(key, "") for key in self.rows))
    ...     def get_footer_bottom_comments(self) -> Iterable[str] | None:
    ...         return ["Bla!"]

    >>> for p in W2.write(dd, separator="@", comment_start="B"):
    ...     print(p)
    a@b@c@d
    1@@2
    @6@8
    4@3@@12
    @
    B Bla!

    >>> for p in W2.write(dd, scope="k", separator="@", comment_start="B"):
    ...     print(p)
    k.a@k.b@k.c@k.d
    1@@2
    @6@8
    4@3@@12
    @
    B Bla!

    >>> ";".join(W2(dd).get_optional_row(None))
    ';;;'
    >>> ";".join(W2(dd).get_optional_row(dd[0]))
    '1;;2;'

    >>> try:
    ...     CsvWriter(1, None)
    ... except TypeError as te:
    ...     print(te)
    data should be an instance of typing.Iterable but is int, namely 1.

    >>> try:
    ...     CsvWriter([], 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     CsvWriter([], "x x")
    ... except ValueError as ve:
    ...     print(ve)
    invalid scope 'x x'

    >>> try:
    ...     CsvWriter([], " x")
    ... except ValueError as ve:
    ...     print(ve)
    invalid scope ' x'

    >>> try:
    ...     CsvWriter([]).get_row("x")
    ... except NotImplementedError as nie:
    ...     print(type(nie))
    <class 'NotImplementedError'>

    >>> try:
    ...     CsvWriter([]).get_column_titles()
    ... except NotImplementedError as nie:
    ...     print(type(nie))
    <class 'NotImplementedError'>
    """

    def __init__(self, data: Iterable[T],
                 scope: str | None = None) -> None:
        """
        Initialize the csv writer.

        :param data: the data to be written
        :param scope: the prefix to be pre-pended to all columns
        :raises TypeError: if `data` is not an `Iterable` or if `scope` is
            neither `None` nor a string
        :raises ValueError: if `scope` is not `None` but: an empty string,
            becomes an empty string after stripping, or contains any
            whitespace or newline character
        """
        super().__init__()
        if not isinstance(data, Iterable):
            raise type_error(data, "data", Iterable)
        if (scope is not None) and ((str.strip(scope) != scope) or (
                str.__len__(scope) <= 0) or (any(map(
                scope.__contains__, WHITESPACE_OR_NEWLINE)))):
            raise ValueError(f"invalid scope {scope!r}")
        #: the optional scope
        self.scope: Final[str | None] = scope

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        raise NotImplementedError

    def get_optional_row(self, data: T | None) -> Iterable[str]:
        """
        Attach an empty row of the correct shape to the output.

        :param data: the data item or `None`
        :returns: the optional row data
        """
        if data is None:  # very crude and slow way to create an optional row
            return [""] * list.__len__(list(self.get_column_titles()))
        return self.get_row(data)

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single sample statistics to a CSV row.

        :param data: the data sample statistics
        :returns: the row iterator
        """
        raise NotImplementedError

    def get_header_comments(self) -> Iterable[str]:
        """
        Get any possible header comments.

        :returns: the iterable of header comments
        """
        return ()

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get any possible footer comments.

        :returns: the footer comments
        """
        return ()

    def get_footer_bottom_comments(self) -> Iterable[str] | None:
        """
        Get the bottom footer comments.

        :returns: an iterator with the bottom comments
        """
        return pycommons_footer_bottom_comments(self)

    @classmethod
    def write(
        cls: type["CsvWriter"],
        data: Iterable[T],
        scope: str | None = None,
        separator: str = CSV_SEPARATOR,
        comment_start: str | None = COMMENT_START,
            **kwargs) -> Generator[str, None, None]:
        """
        Write the CSV data based on the methods provided by the class `cls`.

        :param data: the data
        :param separator: the CSV separator
        :param comment_start: the comment start character
        :param scope: the scope, or `None`
        :param kwargs: additional arguments to be passed to the constructor

        :raises TypeError: if `kwargs` is not `None` but also not a
            :class:`dict`
        """
        def __creator(y: Iterable[T], __c=cls,  # pylint: disable=W0102
                      __s=scope,  # noqa  # type: ignore
                      __x=kwargs) -> "CsvWriter":   # noqa  # type: ignore
            return __c(data=y, scope=__s, **__x)   # noqa  # type: ignore

        yield from csv_write(
            data=data,
            column_titles=cls.get_column_titles,  # type: ignore
            get_row=cls.get_row,  # type: ignore
            setup=__creator,
            separator=separator,
            comment_start=comment_start,
            header_comments=cls.get_header_comments,  # type: ignore
            footer_comments=cls.get_footer_comments,  # type: ignore
            footer_bottom_comments=cls.  # type: ignore
            get_footer_bottom_comments)  # type: ignore
