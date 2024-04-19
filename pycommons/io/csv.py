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

from typing import Any, Callable, Final, Iterable, TypeVar, cast

from pycommons.strings.chars import NEWLINE
from pycommons.types import type_error

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
    :return: the scope joined with the key

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
             consumer: Callable[[T], Any] = lambda _: None,
             separator: str = CSV_SEPARATOR,
             comment_start: str | None = COMMENT_START) -> None:
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

    :param rows: the rows of text
    :param setup: a function which creates an object holding the necessary
        information for row parsing
    :param parse_row: the unction parsing the rows
    :param consumer: the consumer function receiving the parsed results
    :param separator: the string used to separate columns
    :param comment_start: the string starting comments
    :raises TypeError: if any of the parameters has the wrong type
    :raises ValueError: if the separator or comment start character are
        incompatible or if the data has some internal error

    >>> def _setup(colidx: dict[str, int]) -> dict[str, int]:
    ...     return colidx

    >>> def _parse_row(colidx: dict[str, int], row: list[str]) -> None:
    ...         return {x: row[y] for x, y in colidx.items()}

    >>> def _consumer(d: dict[str, str]):
    ...     print(d)

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> csv_read(text, _setup, _parse_row, _consumer)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_read((t.replace(";", ",") for t in text), _setup, _parse_row,
    ...            _consumer, ",")
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_read((t.replace(";", "\t") for t in text), _setup, _parse_row,
    ...           _consumer, "\t")
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_read(text, _setup, _parse_row, _consumer, comment_start=None)
    {'a': '# test', 'b': '', 'c': '', 'd': ''}
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}
    {'a': '# 11', 'b': '12', 'c': '', 'd': ''}

    >>> try:
    ...     csv_read(None, _setup, _parse_row, _consumer)
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is None.

    >>> try:
    ...     csv_read(1, _setup, _parse_row, _consumer)
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     csv_read(text, None, _parse_row, _consumer)
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is None.

    >>> try:
    ...     csv_read(text, 1, _parse_row, _consumer)
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_read(text, _setup, None, _consumer)
    ... except TypeError as te:
    ...     print(te)
    parse_row should be a callable but is None.

    >>> try:
    ...     csv_read(text, _setup, 1, _consumer)
    ... except TypeError as te:
    ...     print(te)
    parse_row should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, None)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is None.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, 1)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid separator ''.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, "-", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, "-", "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ''.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, "-", " ")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ' '.

    >>> try:
    ...     csv_read(text, _setup, _parse_row, _consumer, ";", ";")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ';'.

    >>> text2 = ["a;b;a;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9"]

    >>> try:
    ...     csv_read(text2, _setup, _parse_row, _consumer)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid column headers: ['a', 'b', 'a', 'd'].
    """
    if not isinstance(rows, Iterable):
        raise type_error(rows, "rows", Iterable)
    if not callable(setup):
        raise type_error(setup, "setup", call=True)
    if not callable(parse_row):
        raise type_error(parse_row, "parse_row", call=True)
    if not callable(consumer):
        raise type_error(consumer, "consumer", call=True)
    if str.__len__(separator) <= 0:
        raise ValueError(f"Invalid separator {separator!r}.")
    if (comment_start is not None) and (
            (str.__len__(comment_start) <= 0) or (
            str.strip(comment_start) != comment_start) or (
            comment_start in separator)):
        raise ValueError(f"Invalid comment start: {comment_start!r}.")

    col_count: int = -1

    # cannot strip spaces that are part of the separator
    stripper: Callable[[str], str] = str.strip if (
        str.strip(separator) == separator) else str.rstrip
    info: S | None = None

    for orig_line in rows:
        line: str = orig_line
        if comment_start is not None:
            deli = str.find(line, comment_start)
            if deli >= 0:
                line = line[:deli]
        line = stripper(line)
        if str.__len__(line) <= 0:
            continue

        cols: list[str] = str.split(line, separator)
        for i, v in enumerate(cols):
            cols[i] = str.strip(v)

        if info is None:
            col_count = list.__len__(cols)
            colmap: dict[str, int] = {s: i for i, s in enumerate(cols)}
            if any(str.__len__(s) <= 0 for s in cols) or (
                    dict.__len__(colmap) != col_count) or (col_count <= 0):
                raise ValueError(f"Invalid column headers: {cols!r}.")
            info = setup(colmap)
            del colmap
            continue

        count: int = list.__len__(cols)
        if count > col_count:
            raise ValueError(
                f"Invalid row {orig_line!r} contains {count} columns, but "
                f"says we got {col_count}.")
        if count < col_count:
            for _ in range(count, col_count):
                cols.append("")
        consumer(parse_row(info, cols))


def csv_write(data: Iterable[T], consumer: Callable[[str], Any],
              get_column_titles: Callable[[S, Callable[[str], None]], Any],
              get_row: Callable[[S, T, Callable[[str], None]], Any],
              setup: Callable[[Iterable[T]], S] = lambda t: cast(S, t),
              separator: str = CSV_SEPARATOR,
              comment_start: str | None = COMMENT_START,
              get_header_comments: Callable[[S, Callable[[str], None]], Any] =
              lambda _, __: None,
              get_footer_comments: Callable[[S, Callable[[str], None]], Any] =
              lambda _, __: None) -> None:
    r"""
    Write data in CSV format to a text destination.

    The data is provided in form of a :class:`Iterable`. In a first step, the
    function `setup` is invoked and applied to the `data` :class:`Iterable`.
    It can return an object that sort of stores the structure of the data,
    e.g., which columns should be generated and how they should be formatted.

    This returned object is passed to `get_column_titles`, which should pass
    the titles of the columns to a :class:`Callable`. These titles are
    :meth:`~str.strip`-ped and concatenated to use the column `separator`
    string and the resulting header string is passed to `consumer`.

    Then, for each element `e` in the `data` :class:`Iterable`, the function
    `get_row` is invoked. This function receives the setup information object
    (previously returned by `setup`) and a :class:`Callable` to which one
    string per column should be passed. These strings are then each
    :meth:`~str.strip`-ped and concatenated using the column `separator`
    string. All trailing `separator` are removed, but if all strings are
    empty, at least a single `separator` is retained. The resulting string
    (per row) is again passed to `consumer`.

    Additionally, `get_header_comments` and `get_footer_comments` can be
    provided to pass row comments as :class:`str` to a :class:`Callable` which
    then prepends or appends them as comment rows before or after all of the
    above, respectively. In that case, `comment_start` is prepended to each
    line.

    :param data: the iterable of data to be written
    :param consumer: the consumer to which it will be written
    :param get_column_titles: get the column titles
    :param get_row: transform a row of data into a list of strings
    :param setup: the setup function that computes how the data should be
        represented
    :param separator: the string used to separate columns
    :param comment_start: the string starting comments
    :param get_header_comments: get the comments to be placed above the CSV
        header row
    :param get_footer_comments: get the comments to be placed after the last
        row
    :raises TypeError: if any of the parameters has the wrong type
    :raises ValueError: if the separator or comment start character are
        incompatible or if the data has some internal error

    >>> dd = [{"a": 1, "c": 2}, {"b": 6, "c": 8},
    ...       {"a": 4, "d": 12, "b": 3}, {}]

    >>> def __setup(datarows) -> list[str]:
    ...     return sorted({dkey for datarow in datarows for dkey in datarow})

    >>> def __get_column_titles(keyd: list[str], app: Callable[[str], None]):
    ...     for kx in keyd:
    ...         app(kx)

    >>> def __get_row(keyd: list[str], row: dict[str, int],
    ...               app: Callable[[str], None]):
    ...     for kx in map(str, (row.get(key, "") for key in keyd)):
    ...         app(kx)

    >>> def __get_header_cmt(keyd: list[str], app: Callable[[str], None]):
    ...     app("This is a header comment.")
    ...     app(" We have two of it. ")

    >>> def __get_footer_cmt(keyd: list[str], app: Callable[[str], None]):
    ...     app(" This is a footer comment.")

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    # This is a header comment.
    # We have two of it.
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    # This is a footer comment.

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ",", "@@", __get_header_cmt, __get_footer_cmt)
    @@ This is a header comment.
    @@ We have two of it.
    a,b,c,d
    1,,2
    ,6,8
    4,3,,12
    ,
    @@ This is a footer comment.

    >>> try:
    ...     csv_write(None, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    data should be an instance of typing.Iterable but is None.

    >>> try:
    ...     csv_write(1, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    data should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, None, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is None.

    >>> try:
    ...     csv_write(dd, 1, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, print, None, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_column_titles should be a callable but is None.

    >>> try:
    ...     csv_write(dd, print, 1, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_column_titles should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, None, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_row should be a callable but is None.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, 1, __setup,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_row should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, None,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is None.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, 1,
    ...           ";", "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    setup should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           None, "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           1, "#", __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", 1, __get_header_cmt, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", None, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_header_comments should be a callable but is None.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", 1, __get_footer_cmt)
    ... except TypeError as te:
    ...     print(te)
    get_header_comments should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "", __get_header_cmt, __get_footer_cmt)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ''.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", " ", __get_header_cmt, __get_footer_cmt)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ' '.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "# ", __get_header_cmt, __get_footer_cmt)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: '# '.

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup, ";",
    ...             None)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", None, __get_header_cmt)
    ... except ValueError as ve:
    ...     print(str(ve)[:60])
    Cannot place header comment 'This is a header comment.' if c

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", None, get_footer_comments=__get_footer_cmt)
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    Cannot place footer comment ' This is a footer comment.' if

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, None)
    ... except TypeError as te:
    ...     print(te)
    get_footer_comments should be a callable but is None.

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __get_header_cmt, 1)
    ... except TypeError as te:
    ...     print(te)
    get_footer_comments should be a callable but is int, namely '1'.

    >>> def __err_cmt_1(keyd: list[str], app: Callable[[str], None]):
    ...     app("This is\n a comment with error.")

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __err_cmt_1)
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    Header comment must not contain newline, but 'This is\n a c

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", get_footer_comments=__err_cmt_1)
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;
    Footer comment must not contain newline, but 'This is\n a c

    >>> def __empty_cmt(keyd: list[str], app: Callable[[str], None]):
    ...     app(" ")

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __empty_cmt)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", get_footer_comments=__empty_cmt)
    a;b;c;d
    1;;2
    ;6;8
    4;3;;12
    ;

    >>> def __error_column_titles_1(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     pass

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_1, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have zero columns.

    >>> def __error_column_titles_2(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     app(" ")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_2, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title ' ', must neither be empty no

    >>> def __error_column_titles_3(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     app("bla\nblugg")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_3, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title 'bla\nblugg', must neither be

    >>> def __error_column_titles_4(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     app(None)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_4, __get_row, __setup,
    ...           ";", "#")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_column_titles_5(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     app(1)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_5, __get_row, __setup,
    ...           ";", "#")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> def __error_column_titles_6(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     for xa in ("a", "b", "c", "a"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_6, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have duplicated columns: ['a', 'b', 'c', 'a'].

    >>> def __error_column_titles_7(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     for xa in ("a", "b", "c;4"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_7, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'c;4', must neither be empty

    >>> def __error_column_titles_8(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     for xa in ("a", "b#x", "c"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_8, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'b#x', must neither be empty

    >>> def __error_row_1(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     for xa in ("bla", None, "blubb"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_1,
    ...               __setup, ";", "#")
    ... except TypeError as te:
    ...     print(te)
    a;b;c;d
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_row_2(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     for xa in ("bla", 2.3, "blubb"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_2,
    ...               __setup, ";", "#")
    ... except TypeError as te:
    ...     print(te)
    a;b;c;d
    descriptor 'strip' for 'str' objects doesn't apply to a 'float' object

    >>> def __error_row_3(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     for xa in ("bla", "x\ny", "blubb"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_3,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    a;b;c;d
    Invalid column value 'x\ny', cannot contain any of

    >>> def __error_row_4(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     for xa in ("bla", "x#", "blubb"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_4,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    a;b;c;d
    Invalid column value 'x#', cannot contain any of [

    >>> def __error_row_5(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     for xa in ("bla", "x;#", "blubb"):
    ...         app(xa)

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_5,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    a;b;c;d
    Invalid column value 'x;#', cannot contain any of

    >>> def __error_column_titles_9(keyd: list[str],
    ...                             app: Callable[[str], None]):
    ...     app("a")

    >>> def __error_row_6(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     app("")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_9, __error_row_6,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    a
    Cannot have empty row in a single-column format, but got [''].

    >>> def __error_row_7(keyd: list[str], row: dict[str, int],
    ...                   app: Callable[[str], None]):
    ...     app("x")
    ...     app("y")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_9, __error_row_7,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    a
    Too many columns in ['x', 'y'], should be 1.
    """
    if not isinstance(data, Iterable):
        raise type_error(data, "data", Iterable)
    if not callable(consumer):
        raise type_error(consumer, "consumer", call=True)
    if not callable(get_column_titles):
        raise type_error(get_column_titles, "get_column_titles", call=True)
    if not callable(get_row):
        raise type_error(get_row, "get_row", call=True)
    if not callable(setup):
        raise type_error(setup, "setup", call=True)
    if str.__len__(separator) <= 0:
        raise ValueError(f"Invalid separator {separator!r}.")
    forbidden_maker: Final[set[str]] = set(NEWLINE)
    forbidden_maker.add(separator)
    if comment_start is not None:
        if (str.__len__(comment_start) <= 0) or (
                str.strip(comment_start) != comment_start) or (
                comment_start in separator):
            raise ValueError(f"Invalid comment start: {comment_start!r}.")
        forbidden_maker.add(comment_start)

    if not callable(get_header_comments):
        raise type_error(get_header_comments, "get_header_comments", call=True)
    if not callable(get_footer_comments):
        raise type_error(get_footer_comments, "get_footer_comments", call=True)

    # get the setup data
    setting: Final[S] = setup(data)
    collected: Final[list[str]] = []
    collected_append: Final[Callable[[str], None]] = collected.append
    forbidden: Final[list[str]] = sorted(forbidden_maker)

    # first put header comments
    get_header_comments(setting, collected_append)
    not_first: bool = False
    for cmt in collected:
        xcmt = str.strip(cmt)  # strip and typecheck
        if comment_start is None:
            raise ValueError(f"Cannot place header comment {cmt!r} "
                             f"if comment_start={comment_start!r}.")
        if str.__len__(xcmt) <= 0:
            if not_first:
                consumer(comment_start)
                not_first = False
            continue
        if any(map(xcmt.__contains__, NEWLINE)):
            raise ValueError(
                f"Header comment must not contain newline, but {cmt!r} does.")
        not_first = True
        consumer(f"{comment_start} {xcmt}")

    # now process the column titles
    collected.clear()
    get_column_titles(setting, collected_append)
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
    consumer(separator.join(collected))

    # now do the single rows
    for element in data:
        if element is None:
            raise type_error(element, "data element", object)
        collected.clear()
        get_row(setting, element, collected_append)
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
                consumer(separator)
                continue
            del collected[last_non_empty:]
        consumer(separator.join(collected))

    # finally put footer comments
    collected.clear()
    get_footer_comments(setting, collected_append)
    not_first = False
    for cmt in collected:
        xcmt = str.strip(cmt)  # strip and typecheck
        if comment_start is None:
            raise ValueError(f"Cannot place footer comment {cmt!r} "
                             f"if comment_start={comment_start!r}.")
        if str.__len__(xcmt) <= 0:
            if not_first:
                consumer(comment_start)
                not_first = False
            continue
        if any(map(xcmt.__contains__, NEWLINE)):
            raise ValueError(
                f"Footer comment must not contain newline, but {cmt!r} does.")
        not_first = True
        consumer(f"{comment_start} {xcmt}")


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
    :return: the string or nothing

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
    :return: the object

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
