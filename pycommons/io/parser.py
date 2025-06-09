"""
A tool for recursively parsing data from directories.

This module provides a unified API for parsing data from files in
directories. The goal is to offer a way to return a generator that
allows us to iterate over the data loaded. While we iterate over this
data, the generator internally iterates over the files.

This means that the control of how the data is loaded stays with the user,
while the programmer can implement the necessary methods to load and process
data in a natural way.
"""

from typing import Final, Generator, Iterable, TypeVar

from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path, file_path
from pycommons.types import type_error

#: the type variable for data to be read from the directories
T = TypeVar("T")


class Parser[T]:
    """
    The parser class.

    This class allows you to implement convenient parsing routines that can
    hierarchically process nested directories of files and return a stream,
    i.e., a :class:`Generator` of results. In other words, it flattens the
    hierarchical processing of directories into a linear sequence of data.
    This allows the user of the API stay in control of when the data is loaded
    while the programmer of the parser API can work in a convenient way with
    high-level abstractions. Another advantage of this parsing API is that its
    results can be processed like a stream and be piped into some filters,
    processors, or even output destinations while it is loaded from the files.
    For example, we can extract certain elements of data from huge collections
    of files and while they are loaded, they could already be processed and
    stored to a stream of CSV data.

    The method :meth:`~pycommons.io.parser.Parser.parse` can be applied to any
    path to a file or directory and will hierarchically process the path and
    yield the parsing results one by one. This is the normal entry point
    function for this parsing API.
    The method :meth:`~pycommons.io.parser.Parser.parse_file` is a convenient
    wrapper that processes a single file in *exactly the same way*.
    The method :meth:`~pycommons.io.parser.Parser.parse_directory` parses a
    path that identifies a directory.

    This class offers an internal API, where the internal functions are
    prefixed with `_`, that allows you to customize the hierarchical parsing
    process to a high degree. You can decide which directories and files to
    process, and you can set up and tear down datastructures on a per-file or
    per-directory basis. All the internal functions are invoked in a
    consistent way, regardless whether you parse single files or nested
    directories.
    """

    def _start_parse(self, root: Path) -> None:
        """
        Begin the parsing process.

        This method is called before the recursing parsing begins. It can be
        used to initialize any internal datastructures to make the parser
        reusable.

        :param root: the root path of the parsing process
        """

    # pylint: disable=W0613
    def _should_parse_file(self, file: Path) -> bool:  # noqa: ARG002
        """
        Check whether we should start parsing a file.

        The other file-parsing routines are only called if this method returns
        `True` for a file. Any overriding method should first call the super
        method.

        :param file: the current file path
        :returns: `True` if the file should be parsed, `False` otherwise
        """
        return True

    def _start_parse_file(self, file: Path) -> None:
        """
        Check whether we should start parsing a file.

        Any method overriding this method should first invoke the super method
        and then perform its own startup code.

        :param file: the current file path
        """

    # pylint: disable=W0613
    def _parse_file(self, file: Path) -> T | None:  # noqa: ARG002
        """
        Parse a file and return the result.

        :param file: the current file path
        :returns: the parsing result
        """
        return None

    def _end_parse_file(self, file: Path) -> None:
        """
        Cleanup after a file has been parsed.

        Any method overriding this function should first perform its own
        cleanup and then call the super implementation.

        :param file: the current file path
        """

    # pylint: disable=W0613
    def _should_list_directory(self, directory: Path) \
            -> tuple[bool, bool]:  # noqa: ARG002
        """
        Check whether we should parse a directory.

        This method is called whenever the parser enters a directory.
        It should return a :class:`tuple` of two :class:`bool` values.
        The first one indicates whether the sub-directories of this directory
        should be processed. `True` means that they are listed and processed.
        `False` means that they are skipped. The second Boolean value
        indicates whether the files inside the directory should be listed.
        `True` means that the files should be listed, `False` means that they
        are not.

        Any overriding method should first call the super method.

        :param directory: the current directory path
        :returns: A :class:`tuple` of two `bool` values, where the first one
            indicates whether sub-directories should be visited and the
            second one indicates whether files should be listed
        """
        return True, True

    def _start_list_directory(self, directory: Path) -> None:
        """
        Prepare for listing a directory.

        This method is only called if `_should_list_directory` returned
        `True`.

        :param directory: the current directory path
        """

    def _end_list_directory(self, directory: Path) -> None:
        """
        Clean up after a directory has been processed.

        :param directory: the current directory path
        """

    def _end_parse(self, root: Path) -> None:
        """
        End the parsing process.

        This method can perform any cleanup and purging of internal
        datastructures to make the parser reusable.

        :param root: the root path of the parsing process
        """

    def _progress_logger(self, text: str) -> None:
        """
        Log the progress.

        This method is called with a string that should be logged. By default,
        it forwards the string to :func:`logger`.

        :param text: the test
        """
        logger(text)

    def __internal_parse(self, paths: Iterable[Path], log_progress: bool,
                         is_root: bool) \
            -> Generator[T, None, None]:
        """
        Perform the internal parsing work.

        This method should never be called directly. It is called by `parse`.

        :param paths: the paths to parse.
        :param log_progress: should we log progress?
        :param is_root: is this the root of parsing
        :returns: the generator
        """
        current: Path | None = None
        for current in paths:
            if current.is_file():
                # The current path identifies a file. We need to check whether
                # this file should be parsed and, if so, parse it and yield
                # from the parsing results.
                should: bool = self._should_parse_file(current)
                if not isinstance(should, bool):  # type check
                    raise type_error(should, "should", bool)
                if should:  # OK, the file should be parsed.
                    self._start_parse_file(current)
                    result: T | None = self._parse_file(current)
                    if result is not None:  # We got some result.
                        yield result
                    # Notify the end of parsing.
                    self._end_parse_file(current)
            elif current.is_dir():  # The path is a directory.
                # Check if we should parse.
                list_dirs, list_files = self._should_list_directory(current)
                if not isinstance(list_dirs, bool):
                    raise type_error(  # wrong type
                        list_dirs, "retval[1] of start_list_dir", bool)
                if not isinstance(list_files, bool):
                    raise type_error(  # wrong type
                        list_files, "retval[2] of start_list_dir", bool)
                if list_dirs or list_files:
                    self._start_list_directory(current)
                    # add the current directory name
                    if log_progress:
                        self._progress_logger(
                            f"entering directory {current!r}.")
                    yield from self.__internal_parse(current.list_dir(
                        list_files, list_dirs), log_progress, False)
                    self._end_list_directory(current)
        if is_root:
            self._end_parse(current)
            if log_progress:
                self._progress_logger(f"finished parsing {current!r}.")

    def parse(self, path: str, log_progress: bool = True) \
            -> Generator[T, None, None]:
        """
        Parse the given path.

        :param path: the path to parse
        :param log_progress: should the progress be logged?
        :returns: the parsed sequence
        """
        root: Final[Path] = Path(path)
        if not isinstance(log_progress, bool):
            raise type_error(log_progress, "log_progress", bool)

        if log_progress:
            self._progress_logger(f"beginning to parse {root!r}.")
        self._start_parse(root)
        return self.__internal_parse((root, ), log_progress, True)

    def parse_file(self, file: str, log_progress: bool = False) -> T:
        """
        Parse a single file.

        This method guarantees to not return `None`. If the internal parsing
        process yields `None` anyway, it will raise a :class:`TypeError`.
        It will also raise a :class:`ValueError` if `file` does not identify a
        file.

        :param file: the file to parse
        :param log_progress: should the progress be logged?
        :returns: the parsing result.
        """
        path: Final[Path] = file_path(file)
        try:
            return next(self.parse(path, log_progress))
        except StopIteration as se:
            raise TypeError(
                f"result of parsing file {path!r} should not be None.")\
                from se

    def parse_directory(self, directory: str, log_progress: bool = True) \
            -> Generator[T, None, None]:
        """
        Parse a directory of files.

        This function basically works exactly as
        :meth:`~pycommons.io.parser.Parser.parse`, but it enforces that
        `directory` is a directory and raises a :class:`ValueError` otherwise.

        :param directory: the directory to parse
        :param log_progress: should the progress be logged?
        :returns: the generator with the parsing results
        """
        return self.parse(directory_path(directory), log_progress)
