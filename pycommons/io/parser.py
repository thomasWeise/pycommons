"""
A tool for recursively parsing data from directories.

This module provides a unified API for parsing data from files in
directories. The goal is to offer a way to return a generator that
allows us to iterate over the data loaded. While we iterate over this
data, the generator internally iterates over the files.
"""

from typing import Any, Callable, Final, Generator, Iterable, TypeVar, cast

from pycommons.io.console import logger
from pycommons.io.path import Path
from pycommons.types import type_error

#: the type variable for data to be read from the directories
T = TypeVar("T")

#: the parser data object type
P = TypeVar("P")


def __inner_parse(
        root: Path, source: Iterable[Path], parser: P,
        start_parse_file: Callable[[P, Path, Path], bool],
        parse_file: Callable[[P, Path, Path], T | None],
        end_parse_file: Callable[[P, Path, Path], Any],
        start_list_dir: Callable[[P, Path, Path], tuple[bool, bool]],
        end_list_dir: Callable[[P, Path, Path], Any],
        end_parse: Callable[[P, Path], Any] | None,
        progress_logger: Callable[[P, str], Any] | None) \
        -> Generator[T, None, None]:
    """
    Perform the recursive parsing for `parse`.

    :param root: the root path
    :param source: the paths to parse
    :param parser: the parser object
    :param start_parse_file: a function receiving `parser` and the path stack.
        This function should return `True` if the file should be processed by
        `parse_file` and `False` otherwise.
    :param parse_file: a function receiving `parser` and the path stack.
        It should then parse the file highest on the stack and return either
        an object or `None` if the file did not contain enough data.
    :param end_parse_file: For every encountered file: If `start_parse_file`
        returned `True`, then this function will be invoked after the file
        parsing has been completed. If `start_parse_file` returned `False`,
        this function will not be called. This function receives the `parser`,
        the root path, and the current path as parameters.
    :param start_list_dir: This function should return a tuple of two `bool`
        values. The first one should indicate whether to recursively
        investigate sub-directories, the second one whether files should be
        loaded. This function receives the `parser`, the root path, and the
        current path as parameters.
    :param end_list_dir: For every encountered directory: If `start_list_dir`
        returned one `True` value, then `end_list_dir` is called after
        processing the directory has finished. Otherwise, `end_list_dir` is
        not called. This function receives the `parser`, the root path, and
        the current path as parameters.
    :param end_parse: the end parsing function, receiving the `parser`
        and the root path as parameter
    :param progress_logger: a function receiving `parser` and
        a progress information strings, or `None` if such information is not
        needed.
    :return: the elements found
    """
    current: Path | None = None
    for current in source:
        if current.is_file():
            # The current path identifies a file. We need to check whether
            # this file should be parsed and, if so, parse it and yield from
            # the parsing results.
            should: bool = start_parse_file(parser, root, current)
            if not isinstance(should, bool):  # type check
                raise type_error(should, "should", bool)
            if should:  # OK, the file should be parsed.
                result = parse_file(parser, root, current)
                if result is not None:  # We got some result.
                    yield result
                # Notify the end of parsing.
                end_parse_file(parser, root, current)
        elif current.is_dir():  # The path is a directory.
            # Check if we should parse.
            list_dirs, list_files = start_list_dir(parser, root, current)
            if not isinstance(list_dirs, bool):
                raise type_error(  # wrong type
                    list_dirs, "retval[1] of start_list_dir", bool)
            if not isinstance(list_files, bool):
                raise type_error(  # wrong type
                    list_files, "retval[2] of start_list_dir", bool)
            if list_dirs or list_files:
                # add the current directory name
                if progress_logger is not None:
                    progress_logger(
                        parser, f"entering directory {current!r}.")
                yield from __inner_parse(
                    root=root, source=current.list_dir(
                        list_files, list_dirs), parser=parser,
                    start_parse_file=start_parse_file, parse_file=parse_file,
                    end_parse_file=end_parse_file,
                    start_list_dir=start_list_dir, end_list_dir=end_list_dir,
                    progress_logger=progress_logger, end_parse=None)
                end_list_dir(parser, root, current)
        else:  # We got a path that is neither a file nor a directory
            raise ValueError(  # this should never happen
                f"{current!r} is neither a file nor a directory.")
    if (end_parse is not None) and (root is current):
        end_parse(parser, root)
        if progress_logger is not None:
            progress_logger(parser, f"finished parsing {root!r}.")


def parse_path(
        path: str, parser: P = None,  # type: ignore
        start_parse: Callable[[P, Path], Any]
        = lambda _, __: None,  # type: ignore
        start_parse_file: Callable[[P, Path, Path], bool]
        = lambda _, __, ___: True,  # type: ignore
        parse_file: Callable[[P, Path, Path], T | None]
        = lambda _, __, ___: None,  # type: ignore
        end_parse_file: Callable[[P, Path, Path], Any]
        = lambda _, __, ___: None,  # type: ignore
        start_list_dir: Callable[[P, Path, Path], tuple[bool, bool]]
        = lambda _, __, ___: (True, True),  # type: ignore
        end_list_dir: Callable[[P, Path, Path], Any]
        = lambda _, __, ___: None,  # type: ignore
        end_parse: Callable[[P, Path], Any] | None
        = lambda _, __: None,  # type: ignore
        progress_logger: Callable[[P, str], Any] | None = lambda _, txt:
        logger(txt)) -> Generator[T, None, None]:  # type: ignore
    """
    Potentially recursively parse a given path identifying a file or directory.

    :param path: the path to parse
    :param parser: the parser object
    :param start_parse: the start parsing function, receiving the `parser`
        and the root path as parameter
    :param start_parse_file: returns `True` if the file should be processed by
        `parse_file` and `False` otherwise. This function receives the
        `parser`, the root path, and the current path as parameters.
    :param parse_file: parses the current file and returns either
        an object or `None` if the file did not contain enough data. This
        function receives the `parser`, the root path, and the current path as
        parameters.
    :param end_parse_file: For every encountered file: If `start_parse_file`
        returned `True`, then this function will be invoked after the file
        parsing has been completed. If `start_parse_file` returned `False`,
        this function will not be called. This function receives the `parser`,
        the root path, and the current path as parameters.
    :param start_list_dir: returns a tuple of two `bool` values for a
        directory. The first one should indicate whether to recursively
        investigate sub-directories, the second one whether files should be
        loaded. This function receives the `parser`, the root path, and the
        current path as parameters.
    :param end_list_dir: For every encountered directory: If `start_list_dir`
        returned one `True` value, then `end_list_dir` is called after
        processing the directory has finished. Otherwise, `end_list_dir` is
        not called. This function receives the `parser`, the root path, and
        the current path as parameters.
    :param end_parse: the end parsing function, receiving the `parser`
        and the root path as parameter
    :param progress_logger: a function receiving `parser` and
        a progress information strings, or `None` if such information is not
        needed.
    :return: the elements found
    """
    if not callable(start_parse):
        raise type_error(start_parse, "start_parse", call=True)
    if not callable(start_parse_file):
        raise type_error(start_parse_file, "start_parse_file", call=True)
    if not callable(parse_file):
        raise type_error(parse_file, "parse_file", call=True)
    if not callable(end_parse_file):
        raise type_error(end_parse_file, "end_parse_file", call=True)
    if not callable(start_list_dir):
        raise type_error(start_list_dir, "start_list_dir", call=True)
    if not callable(end_list_dir):
        raise type_error(end_list_dir, "end_list_dir", call=True)
    if (progress_logger is not None) and (not callable(progress_logger)):
        raise type_error(progress_logger, "progress_logger",
                         expected=type(None), call=True)
    if not callable(end_parse):
        raise type_error(end_parse, "end_parse", call=True)
    root: Final[Path] = Path(path)
    if progress_logger is not None:
        progress_logger(parser, f"beginning to parse {root!r}.")
    start_parse(parser, root)
    return __inner_parse(
        root, source=(root, ), parser=parser,
        start_parse_file=start_parse_file, parse_file=parse_file,
        end_parse_file=end_parse_file, start_list_dir=start_list_dir,
        end_list_dir=end_list_dir, end_parse=end_parse,
        progress_logger=progress_logger)


class Parser[T]:
    """The parser class."""

    def start_parse(self, root: Path) -> None:
        """
        Begin the parsing process.

        :param root: the root path of the parsing process
        """

    # pylint: disable=W0613
    def start_parse_file(self, root: Path, current: Path) -> bool:
        """
        Check whether we should start parsing a file.

        :param root: the root path of the parsing process
        :param current: the current file path
        :return: `True` if the file should be parsed, `False` otherwise
        """
        return True

    # pylint: disable=W0613
    def parse_file(self, root: Path, current: Path) -> T:
        """
        Parse a file and return the result.

        :param root: the root path of the parsing process
        :param current: the current file path
        :return: the parsing result
        """
        return cast(T, None)

    def end_parse_file(self, root: Path, current: Path) -> None:
        """
        Process the end of a parsed file.

        :param root: the root path of the parsing process
        :param current: the current file path
        """

    # pylint: disable=W0613
    def start_list_dir(self, root: Path, current: Path) \
            -> tuple[bool, bool]:
        """
        Check whether we should parse a directory.

        :param root: the root path of the parsing process
        :param current: the current directory path
        :return: A :class:`tuple` of two `bool` values, where the first one
            indicates whether sub-directories should be visited and the
            second one indicates whether files should be listed
        """
        return True, True

    def end_list_dir(self, root: Path, current: Path) -> None:
        """
        Check whether we should start parsing a file.

        :param root: the root path of the parsing process
        :param current: the current directory path
        """

    def end_parse(self, root: Path) -> None:
        """
        End the parsing process.

        :param root: the root path of the parsing process
        """

    def progress_logger(self, text: str) -> None:
        """
        Log the progress.

        :param text: the test
        """
        logger(text)

    def parse(self, path: str, log_progress: bool = True) \
            -> Generator[T, None, None]:
        """
        Parse the given path.

        :param path: the path to parse
        :param log_progress: the progress logger
        :returns: the parsed sequence
        """
        if not isinstance(log_progress, bool):
            raise type_error(log_progress, "log_progress", bool)
        cls: type[Parser] = type(self)
        return parse_path(
            path, self, cls.start_parse,  # type: ignore
            cls.start_parse_file,  # type: ignore
            cls.parse_file,  # type: ignore
            cls.end_parse_file,  # type: ignore
            cls.start_list_dir,  # type: ignore
            cls.end_list_dir,  # type: ignore
            cls.end_parse,  # type: ignore
            cls.progress_logger if log_progress else None)  # type: ignore
