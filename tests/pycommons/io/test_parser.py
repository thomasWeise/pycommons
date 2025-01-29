"""Test the simple cache."""
from random import randint
from typing import Final

# noinspection PyPackageRequirements
import pytest

from pycommons.io.parser import Parser, parse_path
from pycommons.io.path import Path
from pycommons.io.temp import temp_dir, temp_file


class CorrectParser(Parser[object]):
    """The internal correct parser."""

    def __init__(self,
                 start_parse_file_always_true: bool,
                 parse_file_always_not_none: bool,
                 list_all_dirs: bool, list_all_files: bool,
                 permitted: set[Path]) -> None:
        """
        Initialize.

        :param start_parse_file_always_true: should all files be parsed?
        :param parse_file_always_not_none: should all parsed files return an
            object?
        :param list_all_dirs: should we list all dirs?
        :param list_all_files: should we list all files?
        """
        super().__init__()
        #: the permitted files
        self.permitted: Final[set[Path]] = permitted
        #: should all files be parsed?
        self.start_parse_file_always_true: Final[bool] = (
            start_parse_file_always_true)
        #: should all parsed files return an object?
        self.parse_file_always_not_none: Final[bool] = (
            parse_file_always_not_none)
        #: the file to parse
        self.__file_to_parse: Path | None = None
        #: how often was start_parse_file called?
        self.n_start_parse_file: int = 0
        #: how often did start_parse_file return true?
        self.n_start_parse_file_true: int = 0
        #: how often did start_parse_file return false?
        self.n_start_parse_file_false: int = 0
        #: the number of times parse_file was called
        self.n_parse_file: int = 0
        #: the number of times parse_file returned None
        self.n_parse_file_none: int = 0
        #: the number of times parse_file returned not None
        self.n_parse_file_not_none: int = 0
        #: the end parse file
        self.n_end_parse_file: int = 0
        #: should we list all directories?
        self.list_all_dirs: Final[bool] = list_all_dirs
        #: should we list all files?
        self.list_all_files: Final[bool] = list_all_files
        #: the number of times start-list-dir was called
        self.n_start_list_dir: int = 0
        #: the number of times we returned true for listing dirs
        self.n_start_list_dir_dir_true: int = 0
        #: the number of times we returned false for listing dirs
        self.n_start_list_dir_dir_false: int = 0
        #: the number of times we returned true for listing files
        self.n_start_list_dir_files_true: int = 0
        #: the number of times we returned false for listing files
        self.n_start_list_dir_files_false: int = 0
        #: the number of times end list dir was called
        self.n_end_list_dir: int = 0
        #: the list of returned objects
        self.returned: list[object] = []
        #: the messages
        self.messages: Final[list[str]] = []
        #: the number of times start_parse was called
        self.n_start_parse: int = 0
        #: the number of times end_parse was called
        self.n_end_parse: int = 0
        #: the root path
        self.root: Path | None = None
        self.check()

    def start_parse(self, root: Path) -> None:
        """
        Begin the parsing process.

        :param root: the root path
        """
        assert self.n_start_parse == 0
        assert self.n_end_parse == 0
        assert self.root is None
        assert root is not None
        assert isinstance(root, Path)
        assert self.n_start_parse_file == 0
        assert self.n_end_parse_file == 0
        assert self.n_start_list_dir == 0
        assert self.n_parse_file == 0
        assert self.n_start_list_dir_dir_true == 0
        assert self.n_start_list_dir_dir_false == 0
        assert self.n_start_list_dir_files_true == 0
        assert self.n_start_list_dir_files_false == 0
        self.n_start_parse = 1
        self.root = root
        self.check()

    def end_parse(self, root: Path) -> None:
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

    def check_inner(self, root: Path, current: Path) -> None:
        """
        Check the paths.

        :param root: the root path of the parsing process
        :param current: the current directory path
        """
        assert self is not None
        assert isinstance(self, CorrectParser)
        assert self.n_end_parse == 0
        assert self.n_start_parse == 1
        assert root is not None
        assert isinstance(root, Path)
        assert current is not None
        assert isinstance(current, Path)
        if root is not current:
            root.enforce_contains(current)

    def start_parse_file(self, root: Path, current: Path) -> bool:
        """
        A correct start file parsing method always returning `True`.

        :param root: the root path of the parsing process
        :param current: the current directory path
        :return: the result
        """
        CorrectParser.check_inner(self, root, current)
        current.enforce_file()
        assert self.__file_to_parse is None
        assert (self.n_start_parse_file
                == self.n_start_parse_file_false
                + self.n_start_parse_file_true)
        self.n_start_parse_file += 1
        ret_val: bool = False
        if self.start_parse_file_always_true or (randint(0, 1) > 0):
            self.__file_to_parse = current
            self.n_start_parse_file_true += 1
            ret_val = True
        else:
            self.n_start_parse_file_false += 1
        self.check()
        return ret_val

    def parse_file(self, root: Path, current: Path) -> object | None:
        """
        Do the parsing.

        :param root: the root path of the parsing process
        :param current: the current directory path
        :return: the result
        """
        CorrectParser.check_inner(self, root, current)
        current.enforce_file()
        assert self.__file_to_parse is current
        assert (self.n_parse_file
                == self.n_parse_file_none + self.n_parse_file_not_none)
        self.n_parse_file += 1
        assert self.n_parse_file == self.n_start_parse_file_true
        ret_val: object | None = None
        if self.parse_file_always_not_none or (randint(0, 1) > 0):
            self.n_parse_file_not_none += 1
            ret_val = object()
            self.returned.append(ret_val)
        else:
            self.n_parse_file_none += 1
        self.check()
        return ret_val

    def end_parse_file(self, root: Path, current: Path) -> None:
        """
        End a file parsing.

        :param root: the root path of the parsing process
        :param current: the current directory path
        """
        CorrectParser.check_inner(self, root, current)
        current.enforce_file()
        assert self.__file_to_parse is current
        self.__file_to_parse = None
        self.n_end_parse_file += 1
        assert self.n_end_parse_file == self.n_start_parse_file_true
        assert self.n_end_parse_file == self.n_parse_file
        self.check()

    def start_list_dir(self, root: Path, current: Path) -> tuple[bool, bool]:
        """
        Start listing the directory.

        :param root: the root path of the parsing process
        :param current: the current directory path
        :return: the dir/file result
        """
        CorrectParser.check_inner(self, root, current)
        current.enforce_dir()
        assert (self.n_start_list_dir == (
            self.n_start_list_dir_dir_true
            + self.n_start_list_dir_dir_false)
            == (self.n_start_list_dir_files_true
                + self.n_start_list_dir_files_false))
        self.n_start_list_dir += 1
        dd: bool = self.list_all_dirs or (randint(0, 1) > 0)
        if dd:
            self.n_start_list_dir_dir_true += 1
        else:
            self.n_start_list_dir_dir_false += 1
        ff: bool = self.list_all_files or (randint(0, 1) > 0)
        if ff:
            self.n_start_list_dir_files_true += 1
        else:
            self.n_start_list_dir_files_false += 1
        self.check()
        return dd, ff

    def end_list_dir(self, root: Path, current: Path) -> None:
        """
        End the directory listing.

        :param root: the root path of the parsing process
        :param current: the current directory path
        """
        CorrectParser.check_inner(self, root, current)
        current.enforce_dir()
        self.n_end_list_dir += 1
        assert self.n_start_list_dir >= self.n_end_list_dir
        self.check()

    def progress_logger(self, text: str) -> None:
        """
        Log the progress.

        :param text: the log text
        """
        assert str.__len__(text) > 0
        self.messages.append(text)
        self.check()

    def check(self) -> None:
        """Check the internal state."""
        assert self.n_start_list_dir >= self.n_end_list_dir
        assert self.n_start_list_dir == (
            self.n_start_list_dir_dir_true
            + self.n_start_list_dir_dir_false) == (
            self.n_start_list_dir_files_true
            + self.n_start_list_dir_files_false)
        if self.start_parse_file_always_true:
            assert self.n_start_parse_file_false == 0
            assert self.n_start_parse_file_true == self.n_start_parse_file
        if self.list_all_dirs:
            assert self.n_start_list_dir_dir_false == 0
            assert self.n_start_list_dir_dir_true == self.n_start_list_dir
        if self.list_all_files:
            assert self.n_start_list_dir_files_false == 0
            assert self.n_start_list_dir_files_true == self.n_start_list_dir
        if self.parse_file_always_not_none:
            assert self.n_parse_file == self.n_parse_file_not_none
        assert list.__len__(self.returned) == self.n_parse_file_not_none
        assert self.n_parse_file <= set.__len__(self.permitted)
        assert self.n_start_list_dir <= set.__len__(self.permitted)
        assert (self.n_start_parse_file + self.n_start_list_dir
                <= set.__len__(self.permitted))
        assert (self.n_end_parse_file <= self.n_start_parse_file_true
                <= (self.n_end_parse_file + 1))
        assert (self.n_end_parse_file <= self.n_parse_file
                <= (self.n_end_parse_file + 1))
        assert (self.n_parse_file
                == self.n_parse_file_none + self.n_parse_file_not_none)
        assert self.n_parse_file <= self.n_start_parse_file_true <= (
            self.n_parse_file + 1)
        assert (self.n_start_parse_file
                == self.n_start_parse_file_false
                + self.n_start_parse_file_true)
        assert self.n_parse_file_not_none == list.__len__(self.returned)
        if list.__len__(self.messages) > 0:
            self.messages[0].startswith("beginning to parse")
            for m in self.messages[1:]:
                assert m.startswith((
                    "beginning to parse", "parsing file",
                    "entering directory", "finished parsing"))
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
        for start_parse_file_always_true in [True, False]:
            for parse_file_always_not_none in [True, False]:
                for list_all_dirs in [True, False]:
                    for list_all_files in [True, False]:
                        parser = CorrectParser(
                            start_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        parser.check()
                        result = list(parse_path(
                            root, parser,
                            CorrectParser.start_parse,  # type: ignore
                            CorrectParser.start_parse_file,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            CorrectParser.start_list_dir,  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned

                        parser = CorrectParser(
                            start_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        result = list(parser.parse(root))
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned

                        parser = CorrectParser(
                            start_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        result = list(parser.parse(root, False))
                        parser.check()
                        assert list.__len__(parser.messages) == 0
                        assert result == parser.returned

                        parser = CorrectParser(
                            start_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allp)
                        with pytest.raises(TypeError):
                            parser.parse(root, 1)  # type: ignore

    with temp_file() as root:
        allf: set[Path] = {root}
        for start_parse_file_always_true in [True, False]:
            for parse_file_always_not_none in [True, False]:
                for list_all_dirs in [True, False]:
                    for list_all_files in [True, False]:
                        parser = CorrectParser(
                            start_parse_file_always_true,
                            parse_file_always_not_none,
                            list_all_dirs, list_all_files, allf)
                        parser.check()
                        result = list(parse_path(
                            root, parser,
                            CorrectParser.start_parse,  # type: ignore
                            CorrectParser.start_parse_file,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            CorrectParser.start_list_dir,  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
                        parser.check()
                        assert parser.messages[-1].startswith(
                            "finished parsing")
                        assert result == parser.returned
        # the default parsing setup returns nothing
        assert list.__len__(list(parse_path(root))) == 0


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
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(1, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       2,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       3,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       4,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       5,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       6,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       7,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       8,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       9,  # type: ignore
                       CorrectParser.progress_logger)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            parse_path(root, parser,  # type: ignore
                       CorrectParser.start_parse,  # type: ignore
                       CorrectParser.start_parse_file,  # type: ignore
                       CorrectParser.parse_file,  # type: ignore
                       CorrectParser.end_parse_file,  # type: ignore
                       CorrectParser.start_list_dir,  # type: ignore
                       CorrectParser.end_list_dir,  # type: ignore
                       CorrectParser.end_parse,  # type: ignore
                       10)  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            list(parse_path(root, parser,  # type: ignore
                            CorrectParser.start_parse,  # type: ignore
                            lambda _, __, ___: 11,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            CorrectParser.start_list_dir,  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            list(parse_path(root, parser,  # type: ignore
                            CorrectParser.start_parse,  # type: ignore
                            CorrectParser.start_parse_file,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            lambda _, __, ___: 12,  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            list(parse_path(root, parser,  # type: ignore
                            CorrectParser.start_parse,  # type: ignore
                            CorrectParser.start_parse_file,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            lambda _, __, ___: (13, True),  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
        parser = CorrectParser(True, True, True, True, allp)
        with pytest.raises(TypeError):
            list(parse_path(root, parser,  # type: ignore
                            CorrectParser.start_parse,  # type: ignore
                            CorrectParser.start_parse_file,  # type: ignore
                            CorrectParser.parse_file,  # type: ignore
                            CorrectParser.end_parse_file,  # type: ignore
                            lambda _, __, ___: (True, 14),  # type: ignore
                            CorrectParser.end_list_dir,  # type: ignore
                            CorrectParser.end_parse,  # type: ignore
                            CorrectParser.progress_logger))  # type: ignore
