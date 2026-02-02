"""Test the simple cache."""
from random import randint
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.io.parser import Parser
from pycommons.io.path import Path
from pycommons.io.temp import temp_dir, temp_file


class CorrectParser(Parser[object]):
    """The internal correct parser."""

    def __init__(self,
                 should_parse_file_always_true: bool = True,
                 parse_file_always_not_none: bool = True,
                 list_all_dirs: bool = True,
                 list_all_files: bool = True,
                 permitted: set[Path] | None = None) -> None:
        """
        Initialize.

        :param should_parse_file_always_true: should all files be parsed?
        :param parse_file_always_not_none: should all parsed files return an
            object?
        :param list_all_dirs: should we list all dirs?
        :param list_all_files: should we list all files?
        """
        super().__init__()
        #: the permitted files
        self.permitted: Final[set[Path] | None] = permitted
        #: should all files be parsed?
        self.should_parse_file_always_true: Final[bool] = (
            should_parse_file_always_true)
        #: should all parsed files return an object?
        self.parse_file_always_not_none: Final[bool] = (
            parse_file_always_not_none)
        #: should we list all directories?
        self.list_all_dirs: Final[bool] = list_all_dirs
        #: should we list all files?
        self.list_all_files: Final[bool] = list_all_files

        #: the file to parse
        self.__file_to_parse: Path | None = None

        #: the number of times start_parse was called
        self.n_start_parse: int = 0

        #: the number of times should_parse_file was called
        self.n_should_parse_file: int = 0
        #: how often did start_parse_file return true?
        self.n_should_parse_file_true: int = 0
        #: how often did start_parse_file return false?
        self.n_should_parse_file_false: int = 0
        #: how often was start_parse_file called?
        self.n_start_parse_file: int = 0

        #: the number of times parse_file was called
        self.n_parse_file: int = 0
        #: the number of times parse_file returned None
        self.n_parse_file_none: int = 0
        #: the number of times parse_file returned not None
        self.n_parse_file_not_none: int = 0

        #: the end parse file
        self.n_end_parse_file: int = 0

        #: the number of times should_list_directory was called
        self.n_should_list_directory: int = 0
        #: the number of times we returned true for listing dirs
        self.n_should_list_directory_dir_true: int = 0
        #: the number of times we returned false for listing dirs
        self.n_should_list_directory_dir_false: int = 0
        #: the number of times we returned true for listing files
        self.n_should_list_directory_files_true: int = 0
        #: the number of times we returned false for listing files
        self.n_should_list_directory_files_false: int = 0

        #: the number of times start-list-dir was called
        self.n_start_list_directory: int = 0
        #: the number of times end list dir was called
        self.n_end_list_directory: int = 0

        #: the number of times end parse was called
        self.n_end_parse: int = 0

        #: the list of returned objects
        self.returned: list[object] = []
        #: the messages
        self.messages: Final[list[str]] = []

        #: the root path
        self.root: Path | None = None
        self.check()

    def _start_parse(self, root: Path) -> None:
        """
        Begin the parsing process.

        :param root: the root path
        """
        super()._start_parse(root)
        assert self.n_start_parse == 0
        assert self.n_end_parse == 0
        assert self.root is None
        assert root is not None
        assert isinstance(root, Path)
        assert self.n_should_parse_file == 0
        assert self.n_start_parse_file == 0
        assert self.n_parse_file == 0
        assert self.n_end_parse_file == 0
        assert self.n_should_list_directory == 0
        assert self.n_start_list_directory == 0
        assert self.n_end_list_directory == 0

        self.n_start_parse = 1
        self.root = root
        self.check()

    def _end_parse(self, root: Path) -> None:
        """
        End the parsing process.

        :param root: the root path
        """
        assert self.n_start_parse == 1
        assert self.n_end_parse == 0
        assert root is not None
        assert isinstance(root, Path)
        assert root is self.root
        self.n_end_parse = 1
        self.check()
        super()._end_parse(root)

    def check_path(self, current: Path) -> None:
        """
        Check the path.

        :param current: the current directory path
        """
        assert self is not None
        assert isinstance(self, CorrectParser)
        assert self.n_end_parse == 0
        assert self.n_start_parse == 1
        assert current is not None
        assert isinstance(current, Path)
        if self.permitted is not None:
            assert current in self.permitted
        assert (self.root is current) or (self.root.contains(current))

    def _should_parse_file(self, file: Path) -> bool:
        """
        Check whether the start file parsing method always returns `True`.

        :param file: the current directory path
        :returns: the result
        """
        CorrectParser.check_path(self, file)
        file.enforce_file()
        assert super()._should_parse_file(file)
        assert self.__file_to_parse is None
        assert self.n_should_parse_file == (
            self.n_should_parse_file_true
            + self.n_should_parse_file_false)
        assert self.n_should_parse_file_true == self.n_start_parse_file
        assert self.n_should_parse_file_true == self.n_parse_file
        assert self.n_should_parse_file_true == self.n_end_parse_file
        self.n_should_parse_file += 1
        ret_val: bool = False
        if self.should_parse_file_always_true or (randint(0, 1) > 0):
            self.__file_to_parse = file
            self.n_should_parse_file_true += 1
            ret_val = True
        else:
            self.n_should_parse_file_false += 1
        self.check()
        return ret_val

    def _start_parse_file(self, file: Path) -> None:
        """
        Start the file parsing.

        :param root: the root path of the parsing process
        :param current: the current directory path
        :returns: the result
        """
        super()._start_parse_file(file)
        CorrectParser.check_path(self, file)
        file.enforce_file()
        assert self.__file_to_parse is file
        self.n_start_parse_file += 1
        assert self.n_start_parse_file == self.n_should_parse_file_true
        assert self.n_start_parse_file == (self.n_parse_file + 1)
        assert self.n_start_parse_file == (self.n_end_parse_file + 1)
        self.check()

    def _parse_file(self, file: Path) -> object | None:
        """
        Do the parsing.

        :param file: the current file path
        :returns: the result
        """
        assert super()._parse_file(file) is None
        CorrectParser.check_path(self, file)
        file.enforce_file()
        assert self.__file_to_parse is file
        assert (self.n_parse_file
                == self.n_parse_file_none + self.n_parse_file_not_none)
        self.n_parse_file += 1
        assert self.n_parse_file == self.n_should_parse_file_true
        assert self.n_parse_file == self.n_start_parse_file
        ret_val: object | None = None
        if self.parse_file_always_not_none or (randint(0, 1) > 0):
            self.n_parse_file_not_none += 1
            ret_val = object()
            self.returned.append(ret_val)
        else:
            self.n_parse_file_none += 1
        self.check()
        return ret_val

    def _end_parse_file(self, file: Path) -> None:
        """
        End a file parsing.

        :param file: the current file path
        """
        CorrectParser.check_path(self, file)
        file.enforce_file()
        assert self.__file_to_parse is file
        self.__file_to_parse = None
        self.n_end_parse_file += 1
        assert self.n_end_parse_file == self.n_should_parse_file_true
        assert self.n_end_parse_file == self.n_start_parse_file
        assert self.n_end_parse_file == self.n_parse_file
        self.check()
        super()._end_parse_file(file)

    def _should_list_directory(self, directory: Path) -> tuple[bool, bool]:
        """
        Start listing the directory.

        :param directory: the current directory path
        :returns: the dir/file result
        """
        CorrectParser.check_path(self, directory)
        directory.enforce_dir()
        assert (self.n_should_list_directory == (
            self.n_should_list_directory_dir_true
            + self.n_should_list_directory_dir_false)
            == (self.n_should_list_directory_files_true
                + self.n_should_list_directory_files_false))
        self.n_should_list_directory += 1
        dd: bool = self.list_all_dirs or (randint(0, 1) > 0)
        if dd:
            self.n_should_list_directory_dir_true += 1
        else:
            self.n_should_list_directory_dir_false += 1
        ff: bool = self.list_all_files or (randint(0, 1) > 0)
        if ff:
            self.n_should_list_directory_files_true += 1
        else:
            self.n_should_list_directory_files_false += 1
        assert super()._should_list_directory(directory) == (True, True)
        assert (self.n_should_list_directory == (
            self.n_should_list_directory_dir_true
            + self.n_should_list_directory_dir_false)
            == (self.n_should_list_directory_files_true
                + self.n_should_list_directory_files_false))
        self.check()
        return dd, ff

    def _start_list_directory(self, directory: Path) -> None:
        """
        Start the directory listing.

        :param directory: the current directory path
        """
        super()._start_list_directory(directory)
        CorrectParser.check_path(self, directory)
        directory.enforce_dir()
        self.n_start_list_directory += 1
        assert self.n_start_list_directory >= max(
            self.n_should_list_directory_dir_true,
            self.n_should_list_directory_files_true)
        self.check()

    def _end_list_directory(self, directory: Path) -> None:
        """
        End the directory listing.

        :param directory: the current directory path
        """
        CorrectParser.check_path(self, directory)
        directory.enforce_dir()
        self.n_end_list_directory += 1
        assert self.n_end_list_directory <= self.n_start_list_directory
        self.check()
        super()._end_list_directory(directory)

    def _progress_logger(self, text: str) -> None:
        """
        Log the progress.

        :param text: the log text
        """
        super()._progress_logger(text)
        assert str.__len__(text) > 0
        self.messages.append(text)
        self.check()

    def check(self) -> None:
        """Check the internal state."""
        assert self.n_end_list_directory <= self.n_start_list_directory
        assert (self.n_should_list_directory == (
            self.n_should_list_directory_dir_true
            + self.n_should_list_directory_dir_false)
            == (self.n_should_list_directory_files_true
                + self.n_should_list_directory_files_false))
        if self.should_parse_file_always_true:
            assert self.n_should_parse_file_false == 0
            assert (self.n_start_parse_file <= self.n_should_parse_file_true
                    <= (self.n_start_parse_file + 1))
        if self.list_all_dirs:
            assert self.n_should_list_directory_dir_false == 0
            assert (self.n_should_list_directory_dir_true
                    == self.n_should_list_directory)
        if self.list_all_files:
            assert self.n_should_list_directory_files_false == 0
            assert (self.n_should_list_directory_files_true
                    == self.n_should_list_directory)
        if self.parse_file_always_not_none:
            assert self.n_parse_file == self.n_parse_file_not_none
        assert list.__len__(self.returned) == self.n_parse_file_not_none

        if self.permitted is not None:
            n_paths: Final[int] = set.__len__(self.permitted)
            assert self.n_should_parse_file <= n_paths
            assert self.n_should_list_directory <= n_paths
            assert (self.n_should_list_directory + self.n_should_list_directory
                    <= n_paths)
        assert (self.n_end_parse_file <= self.n_should_parse_file_true
                <= (self.n_end_parse_file + 1))
        assert (self.n_end_parse_file <= self.n_parse_file
                <= (self.n_end_parse_file + 1))
        assert (self.n_parse_file
                == self.n_parse_file_none + self.n_parse_file_not_none)
        assert self.n_parse_file <= self.n_should_parse_file_true <= (
            self.n_parse_file + 1)
        assert (self.n_should_parse_file
                == self.n_should_parse_file_false
                + self.n_should_parse_file_true)
        assert self.n_parse_file_not_none == list.__len__(self.returned)
        if list.__len__(self.messages) > 0:
            self.messages[0].startswith("beginning to parse")
            for m in self.messages[1:]:
                assert m.startswith((
                    "beginning to parse", "entering directory",
                    "finished parsing"))
        assert 0 <= self.n_end_parse <= self.n_start_parse <= 1


def __create_temp(root: Path, allp: set[Path], md: int) -> None:
    """
    Create a set of temp files and directories.

    :param root: the root directory
    :param allp: the set to store all files
    :param md: the maximum depth
    """
    if md > 0:
        for _ in range(randint(0, 5)):
            d = temp_dir(root)
            allp.add(d)
            __create_temp(d, allp, md - 1)
    for _ in range(randint(0, 5)):
        f = temp_file(root)
        allp.add(f)


def test_parsing() -> None:
    """Test the parsing API."""
    with temp_dir() as root:
        allp: Final[set] = {root}
        __create_temp(root, allp, 3)
        __create_temp(root, allp, 4)
        for should_parse_file_always_true in [True, False]:
            for parse_file_always_not_none in [True, False]:
                for list_all_dirs in [True, False]:
                    for list_all_files in [True, False]:
                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        parser.check()
                        result = list(parser.parse(root))
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned

                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        parser.check()
                        result = list(parser.parse_directory(root))
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned

                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        result = list(parser.parse(root, False))
                        parser.check()
                        assert list.__len__(parser.messages) == 0
                        assert result == parser.returned

                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        with pytest.raises(TypeError):
                            parser.parse(root, 1)  # type: ignore

    with temp_file() as root:
        allf: set[Path] = {root}
        for should_parse_file_always_true in [True, False]:
            for parse_file_always_not_none in [True, False]:
                for list_all_dirs in [True, False]:
                    for list_all_files in [True, False]:
                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allf)
                        parser.check()
                        result = list(parser.parse(root, True))
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned

                        parser = CorrectParser(
                            should_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files,
                            allf)
                        try:
                            found = parser.parse_file(root)
                            assert [found] == parser.returned
                        except TypeError:
                            assert (parser.n_should_parse_file_false == 1) or (
                                parser.n_parse_file_none == 1)


def test_parsing_typerror() -> None:
    """Test whether the type errors are correctly raised."""
    with temp_dir() as root:
        allp: Final[set] = {root}
        __create_temp(root, allp, 4)
        allp.add(temp_file(root))
        x = temp_dir(root)
        allp.add(x)
        allp.add(temp_file(x))
        allp.add(temp_dir(x))

        parser = CorrectParser()
        with pytest.raises(TypeError):
            parser.parse(root, 1)  # type: ignore
        parser = CorrectParser()
        with pytest.raises(TypeError):
            parser.parse(2)  # type: ignore

        class _P1(CorrectParser):  # type: ignore
            def _should_list_directory(  # type: ignore
                    self, directory: Path) -> tuple:  # type: ignore
                return 3  # type: ignore
        parser = _P1()
        with pytest.raises(TypeError):
            list(parser.parse(root))

        class _P2(CorrectParser):  # type: ignore
            def _should_list_directory(  # type: ignore
                    self, directory: Path) -> tuple:  # type: ignore
                return 4, True  # type: ignore
        parser = _P2()
        with pytest.raises(TypeError):
            list(parser.parse(root))

        class _P3(CorrectParser):  # type: ignore
            def _should_list_directory(  # type: ignore
                    self, directory: Path) -> tuple:  # type: ignore
                return True, 5  # type: ignore
        parser = _P3()
        with pytest.raises(TypeError):
            list(parser.parse(root))

        class _P4(CorrectParser):  # type: ignore
            def _should_parse_file(self, file: Path) -> bool:  # type: ignore
                return 6  # type: ignore
        parser = _P4()
        with pytest.raises(TypeError):
            list(parser.parse(root))
