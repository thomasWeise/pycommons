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


def csv_parse(rows: Iterable[str],
              create_row_parser: Callable[[dict[str, int]], Callable[
                  [list[str]], Any]],
              separator: str = CSV_SEPARATOR,
              comment_start: str | None = COMMENT_START) -> None:
    r"""
    Parse a sequence of strings as CSV data.

    All lines str :meth:`~str.split` based on the `separator` string and each
    of the resulting string is stripped via :meth:`~str.strip`.
    The first non-empty line of the data is interpreted as header line.

    This header is passed to the `create_row_parser` function in form of
    a :class:`dict` that maps column titles to column indices. This function
    is then supposed to return another function that will then iteratively be
    fed the :meth:`~str.split` and :meth:`~str.strip`-ped lines row by row.
    It is permitted that a line in the CSV file contains less columns than
    declared in the header. In this case, the missing columns are set to empty
    strings. Lines that are entirely empty are skipped.

    If `comment_start` is not none, then all text in a line starting at the
    first occurence of `comment_start` is discarted before the line is
    processed.

    :param rows: the rows of text
    :param create_row_parser: a function to create the row parser to which
        rows of the same length as the header are passed
    :param separator: the string used to separate columns
    :param comment_start: the string starting comments
    :raises TypeError: if any of the parameters has the wrong type
    :raises ValueError: if the separator or comment start character are
        incompatible or if the data has some internal error

    >>> def _create(ccc: dict[str, str]) -> Callable[[list[str]], None]:
    ...     def __print(line, _hl=ccc):
    ...         print({x: line[y] for x, y in _hl.items()})
    ...     return __print

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> csv_parse(text, _create)
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_parse((t.replace(";", ",") for t in text), _create, ",")
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_parse((t.replace(";", "\t") for t in text), _create, "\t")
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> csv_parse(text, _create, comment_start=None)
    {'a': '# test', 'b': '', 'c': '', 'd': ''}
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}
    {'a': '# 11', 'b': '12', 'c': '', 'd': ''}

    >>> try:
    ...     csv_parse(None, _create)
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is None.

    >>> try:
    ...     csv_parse(1, _create)
    ... except TypeError as te:
    ...     print(te)
    rows should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     csv_parse(text, None)
    ... except TypeError as te:
    ...     print(te)
    create_row_parser should be a callable but is None.

    >>> try:
    ...     csv_parse(text, 1)
    ... except TypeError as te:
    ...     print(te)
    create_row_parser should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_parse(text, _create, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     csv_parse(text, _create, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_parse(text, _create, "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid separator ''.

    >>> try:
    ...     csv_parse(text, _create, "-", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     csv_parse(text, _create, "-", "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ''.

    >>> try:
    ...     csv_parse(text, _create, "-", " ")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ' '.

    >>> try:
    ...     csv_parse(text, _create, ";", ";")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid comment start: ';'.

    >>> text2 = ["a;b;a;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9"]

    >>> try:
    ...     csv_parse(text2, _create)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid column headers: ['a', 'b', 'a', 'd'].

    >>> try:
    ...     csv_parse(text, lambda sy: None)
    ... except TypeError as te:
    ...     print(te)
    result of create_row_parser should be a callable but is None.

    >>> try:
    ...     csv_parse(text, lambda sy: 1)
    ... except TypeError as te:
    ...     print(te)
    result of create_row_parser should be a callable but is int, namely '1'.
    """
    if not isinstance(rows, Iterable):
        raise type_error(rows, "rows", Iterable)
    if not callable(create_row_parser):
        raise type_error(
            create_row_parser, "create_row_parser", call=True)
    if str.__len__(separator) <= 0:
        raise ValueError(f"Invalid separator {separator!r}.")
    if (comment_start is not None) and (
            (str.__len__(comment_start) <= 0) or (
            str.strip(comment_start) != comment_start) or (
            comment_start in separator)):
        raise ValueError(f"Invalid comment start: {comment_start!r}.")

    col_count: int = -1
    handler: Callable[[list[str]], None] | None = None

    # cannot strip spaces that are part of the separator
    stripper: Callable[[str], str] = str.strip if (
        str.strip(separator) == separator) else str.rstrip

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

        if handler is None:
            col_count = list.__len__(cols)
            colmap: dict[str, int] = {s: i for i, s in enumerate(cols)}
            if any(str.__len__(s) <= 0 for s in cols) or (
                    dict.__len__(colmap) != col_count) or (col_count <= 0):
                raise ValueError(f"Invalid column headers: {cols!r}.")
            handler = create_row_parser(colmap)
            del colmap
            if not callable(handler):
                raise type_error(handler, "result of create_row_parser",
                                 call=True)
            continue

        count: int = list.__len__(cols)
        if count > col_count:
            raise ValueError(
                f"Invalid row {orig_line!r} contains {count} columns, but "
                f"says we got {col_count}.")
        if count < col_count:
            for _ in range(count, col_count):
                cols.append("")
        handler(cols)


#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T")


def csv_make_consumer(
        create_row_parser: Callable[[dict[str, int]], Callable[
            [list[str]], T]], consumer: Callable[[T], Any]) \
        -> Callable[[dict[str, int]], Callable[[list[str]], None]]:
    r"""
    Forward the results of a CSV row parser to a consumer function.

    This function is to be used in conjunction with :func:`csv_parse`. It
    allows for a line processor to forward its results to a collector, e.g.,
    `list.append`. If you implement a row parser constructor, then this
    function wraps this constructor into one which will forward the results
    of the row parser generated by the constructor to a consumer function.

    :param create_row_parser: the row consumer creator
    :param consumer: the consumer to which the line parsing result should be
        forwarded
    :return: the wrapped processor
    :raises TypeError: if any of the parameters has the wrong type

    >>> def _ccreate(ccc: dict[str, str]) -> Callable[[list[str]], None]:
    ...     def __create(line, _hl=ccc):
    ...         return repr({x: line[y] for x, y in _hl.items()})
    ...     return __create

    >>> text = ["a;b;c;d", "# test", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
    ...         "", "10", "# 11;12"]

    >>> csv_parse(text, csv_make_consumer(_ccreate, print))
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> l: list[str] = []
    >>> csv_parse(text, csv_make_consumer(_ccreate, l.append))
    >>> print("\n".join(l))
    {'a': '1', 'b': '2', 'c': '3', 'd': '4'}
    {'a': '5', 'b': '6', 'c': '', 'd': ''}
    {'a': '', 'b': '8', 'c': '', 'd': '9'}
    {'a': '10', 'b': '', 'c': '', 'd': ''}

    >>> try:
    ...     csv_make_consumer(print, None)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is None.

    >>> try:
    ...     csv_make_consumer(print, 1)
    ... except TypeError as te:
    ...     print(te)
    consumer should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_parse(text, csv_make_consumer(lambda k: None, print))
    ... except TypeError as te:
    ...     print(te)
    result of create_row_parser should be a callable but is None.

    >>> try:
    ...     csv_parse(text, csv_make_consumer(lambda k: 1, print))
    ... except TypeError as te:
    ...     print(te)
    result of create_row_parser should be a callable but is int, namely '1'.

    >>> try:
    ...     csv_make_consumer(None, print)
    ... except TypeError as te:
    ...     print(te)
    create_row_parser should be a callable but is None.

    >>> try:
    ...     csv_make_consumer(1, print)
    ... except TypeError as te:
    ...     print(te)
    create_row_parser should be a callable but is int, namely '1'.
    """
    if not callable(consumer):
        raise type_error(consumer, "consumer", call=True)
    if not callable(create_row_parser):
        raise type_error(create_row_parser, "create_row_parser", call=True)

    def __create_row_parser(
            header: dict[str, int], __consumer=consumer,
            __create_row_parser=create_row_parser) \
            -> Callable[[list[str]], None]:
        proc = __create_row_parser(header)
        if not callable(proc):
            raise type_error(proc, "result of create_row_parser", call=True)

        def __row_consumer(
                row: list[str], __orig=proc, __dest=__consumer) -> None:
            __dest(__orig(row))

        return cast(Callable[[list[str]], None], __row_consumer)

    return cast(Callable[[dict[str, int]], Callable[[list[str]], None]],
                __create_row_parser)


# mypy: disable-error-code=valid-type
#: the type variable for the CSV output setup
S = TypeVar("S")


def csv_write(data: Iterable[T], consumer: Callable[[str], Any],
              get_column_titles: Callable[[S, list[str]], Any],
              get_row: Callable[[S, T, list[str]], Any],
              setup: Callable[[Iterable[T]], S] = lambda t: cast(S, t),
              separator: str = CSV_SEPARATOR,
              comment_start: str | None = COMMENT_START,
              get_header_comments: Callable[[S, list[str]], Any] =
              lambda _, __: None,
              get_footer_comments: Callable[[S, list[str]], Any] =
              lambda _, __: None) -> None:
    r"""
    Write data in CSV format to a text destination.

    The data is provided in form of a :class:`Iterable`. In a first step, the
    function `setup` is invoked and applied to the `data` :class:`Iterable`.
    It can return an object that sort of stores the structure of the data,
    e.g., which columns should be generated and how they should be formatted.
    This returned object is passed to `get_column_titles`, which should append
    the titles of the columns to a :class:`list` of :class:`str`. These titles
    are :meth:`~str.strip`-ped concatenated to use the column `separator`
    string and the resulting header string is passed to `consumer`. Then, for
    each element `e` in the `data` :class:`Iterable`, the function `get_row`
    is invoked. This function receives the setup information object
    (previously returned by `setup`) and should append one string per column
    to the :class:`list` it receives as third parameter. These strings are
    then each :meth:`~str.strip`-ped and concatenated using the column
    `separator` string. All trailing `separator` are removed, but if all
    strings are empty, at least a single `separator` is retained. The
    resulting string (per row) is again passed to `consumer`.

    Additionally, `get_header_comments` and `get_footer_comments` can be
    provided to generate instances of :class:`Iterable` of :class:`str` to
    prepend or append as comment rows before or after all of the above,
    respectively. In that case, `comment_start` is prepended to each line.

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

    >>> def __get_column_titles(keyd: list[str], lst: list[str]):
    ...     lst.extend(keyd)

    >>> def __get_row(keyd: list[str], row: dict[str, int], lst: list[str]):
    ...     lst.extend(map(str, (row.get(key, "") for key in keyd)))

    >>> def __get_header_cmt(keyd: list[str], dst: list[str]):
    ...     dst.append("This is a header comment.")
    ...     dst.append(" We have two of it. ")

    >>> def __get_footer_cmt(keyd: list[str], dst: list[str]):
    ...     dst.append(" This is a footer comment.")

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

    >>> def __err_cmt_1(keyd: list[str], dst: list[str]):
    ...     dst.append("This is\n a comment with error.")

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

    >>> def __empty_cmt(keyd: list[str], dst: list[str]):
    ...     dst.append(" ")

    >>> csv_write(dd, print, __get_column_titles, __get_row, __setup,
    ...           ";", "#", __empty_cmt)
    #
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
    #

    >>> def __error_column_titles_1(keyd: list[str], lst: list[str]):
    ...     pass

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_1, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have zero columns.

    >>> def __error_column_titles_2(keyd: list[str], lst: list[str]):
    ...     lst.append(" ")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_2, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title ' ', must neither be empty no

    >>> def __error_column_titles_3(keyd: list[str], lst: list[str]):
    ...     lst.append("bla\nblugg")

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_3, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Invalid column title 'bla\nblugg', must neither be

    >>> def __error_column_titles_4(keyd: list[str], lst: list[str]):
    ...     lst.append(None)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_4, __get_row, __setup,
    ...           ";", "#")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_column_titles_5(keyd: list[str], lst: list[str]):
    ...     lst.append(1)

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_5, __get_row, __setup,
    ...           ";", "#")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> def __error_column_titles_6(keyd: list[str], lst: list[str]):
    ...     lst.extend(("a", "b", "c", "a"))

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_6, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    Cannot have duplicated columns: ['a', 'b', 'c', 'a'].

    >>> def __error_column_titles_7(keyd: list[str], lst: list[str]):
    ...     lst.extend(("a", "b", "c;4"))

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_7, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'c;4', must neither be empty

    >>> def __error_column_titles_8(keyd: list[str], lst: list[str]):
    ...     lst.extend(("a", "b#x", "c"))

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_8, __get_row, __setup,
    ...           ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    Invalid column title 'b#x', must neither be empty

    >>> def __error_row_1(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("bla", None, "blubb"))

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_1,
    ...               __setup, ";", "#")
    ... except TypeError as te:
    ...     print(te)
    a;b;c;d
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> def __error_row_2(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("bla", 2.3, "blubb"))

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_2,
    ...               __setup, ";", "#")
    ... except TypeError as te:
    ...     print(te)
    a;b;c;d
    descriptor 'strip' for 'str' objects doesn't apply to a 'float' object

    >>> def __error_row_3(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("bla", "x\ny", "blubb"))

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_3,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    a;b;c;d
    Invalid column value 'x\ny', cannot contain any of

    >>> def __error_row_4(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("bla", "x#", "blubb"))

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_4,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    a;b;c;d
    Invalid column value 'x#', cannot contain any of [

    >>> def __error_row_5(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("bla", "x;#", "blubb"))

    >>> try:
    ...     csv_write(dd, print, __get_column_titles, __error_row_5,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(str(ve)[:49])
    a;b;c;d
    Invalid column value 'x;#', cannot contain any of

    >>> def __error_column_titles_9(keyd: list[str], lst: list[str]):
    ...     lst.extend(("a"))

    >>> def __error_row_6(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("", ))

    >>> try:
    ...     csv_write(dd, print, __error_column_titles_9, __error_row_6,
    ...               __setup, ";", "#")
    ... except ValueError as ve:
    ...     print(ve)
    a
    Cannot have empty row in a single-column format, but got [''].

    >>> def __error_row_7(keyd: list[str], row: dict[str, int],
    ...                   lst: list[str]):
    ...     lst.extend(("x", "y"))

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
    forbidden: Final[list[str]] = sorted(forbidden_maker)

    # first put header comments
    get_header_comments(setting, collected)
    for cmt in collected:
        xcmt = str.strip(cmt)  # strip and typecheck
        if comment_start is None:
            raise ValueError(f"Cannot place header comment {cmt!r} "
                             f"if comment_start={comment_start!r}.")
        if str.__len__(xcmt) <= 0:
            consumer(comment_start)
            continue
        if any(map(xcmt.__contains__, NEWLINE)):
            raise ValueError(
                f"Header comment must not contain newline, but {cmt!r} does.")
        consumer(f"{comment_start} {xcmt}")

    # now process the column titles
    collected.clear()
    get_column_titles(setting, collected)
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
        get_row(setting, element, collected)
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
    get_footer_comments(setting, collected)
    for cmt in collected:
        xcmt = str.strip(cmt)  # strip and typecheck
        if comment_start is None:
            raise ValueError(f"Cannot place footer comment {cmt!r} "
                             f"if comment_start={comment_start!r}.")
        if str.__len__(xcmt) <= 0:
            consumer(comment_start)
            continue
        if any(map(xcmt.__contains__, NEWLINE)):
            raise ValueError(
                f"Footer comment must not contain newline, but {cmt!r} does.")
        consumer(f"{comment_start} {xcmt}")
