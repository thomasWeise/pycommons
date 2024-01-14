"""
The class `Path` for handling paths to files and directories.

The instances of :class:`Path` identify file system paths.
They are always fully canonicalized with all relative components resolved.
They thus allow the clear identification of files and directories.
They also offer support for opening streams, creating paths to sub-folders,
and so on.
"""

import codecs
from io import TextIOBase
from os import O_CREAT, O_EXCL, makedirs
from os import close as osclose
from os import open as osopen
from os.path import (
    abspath,
    commonpath,
    expanduser,
    expandvars,
    isdir,
    isfile,
    join,
    normcase,
    realpath,
)
from re import MULTILINE
from re import compile as _compile
from typing import Final, Iterable, Pattern, cast

from pycommons.strings.regex import regex_sub
from pycommons.types import must_be_str, type_error


def _canonicalize_path(path: str) -> str:
    """
    Check and canonicalize a path.

    A canonicalized path does not contain any relative components, is fully
    expanded, and, in case-insensitive file systems, using the normal case.

    >>> try:
    ...     _canonicalize_path(1)
    ... except TypeError as te:
    ...     print(te)
    path should be an instance of str but is int, namely '1'.

    >>> try:
    ...     _canonicalize_path(None)
    ... except TypeError as te:
    ...     print(te)
    path should be an instance of str but is None.

    >>> try:
    ...     _canonicalize_path("")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not be empty.

    >>> from os.path import dirname
    >>> _canonicalize_path(dirname(realpath(__file__)) + "/..") == \
dirname(dirname(realpath(__file__)))
    True

    >>> _canonicalize_path(dirname(realpath(__file__)) + "/.") == \
dirname(realpath(__file__))
    True

    >>> _canonicalize_path(__file__) == realpath(__file__)
    True

    >>> from os import getcwd
    >>> _canonicalize_path(".") == realpath(getcwd())
    True

    >>> from os import getcwd
    >>> _canonicalize_path("..") == dirname(realpath(getcwd()))
    True

    >>> from os import getcwd
    >>> _canonicalize_path("../.") == dirname(realpath(getcwd()))
    True

    >>> from os import getcwd
    >>> _canonicalize_path("../1.txt") == \
join(dirname(realpath(getcwd())), "1.txt")
    True

    >>> from os import getcwd
    >>> _canonicalize_path("./1.txt") == join(realpath(getcwd()), "1.txt")
    True

    >>> from os.path import isabs
    >>> isabs(_canonicalize_path(".."))
    True

    :param path: the path
    :return: the canonicalized path
    """
    if not isinstance(path, str):
        raise type_error(path, "path", str)
    if len(path) <= 0:
        raise ValueError("Path must not be empty.")
    path = normcase(abspath(realpath(expanduser(expandvars(path)))))
    if not isinstance(path, str):  # this should never happen
        raise type_error(path, "canonicalized path", str)
    if len(path) <= 0:  # this should never happen either
        raise ValueError("Canonicalization must yield non-empty string, "
                         f"but returned {path!r}.")
    if path in [".", ".."]:  # this should never happen, too
        raise ValueError(f"Canonicalization cannot yield {path!r}.")
    return path


#: the UTF-8 encoding
UTF8: Final[str] = "utf-8-sig"

#: The list of possible text encodings
__ENCODINGS: Final[tuple[tuple[tuple[bytes, ...], str], ...]] = \
    (((codecs.BOM_UTF8,), UTF8),
     ((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE), "utf-32"),
     ((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE), "utf-16"))


def _get_text_encoding(filename: str) -> str:
    r"""
    Get the text encoding from a BOM if present.

    If no encoding BOM can be found, we return the standard UTF-8 encoding.
    Adapted from https://stackoverflow.com/questions/13590749.

    :param filename: the filename
    :return: the encoding

    >>> from tempfile import mkstemp
    >>> from os import close as osclose
    >>> from os import remove as osremove
    >>> (h, tf) = mkstemp()
    >>> osclose(h)
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\xef\xbb\xbf')
    3
    >>> _get_text_encoding(tf)
    'utf-8-sig'
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\xff\xfe\x00\x00')
    4
    >>> _get_text_encoding(tf)
    'utf-32'
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\x00\x00\xfe\xff')
    4
    >>> _get_text_encoding(tf)
    'utf-32'
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\xff\xfe')
    2
    >>> _get_text_encoding(tf)
    'utf-16'
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\xfe\xff')
    2
    >>> _get_text_encoding(tf)
    'utf-16'
    >>> with open(tf, "wb") as out:
    ...     out.write(b'\xaa\xf3')
    2
    >>> _get_text_encoding(tf)
    'utf-8-sig'
    >>> osremove(tf)
    """
    with open(filename, "rb") as f:
        header = f.read(4)  # Read just the first four bytes.
    for boms, encoding in __ENCODINGS:
        for bom in boms:
            if header.find(bom) == 0:
                return encoding
    return UTF8


#: a pattern used to clean up training white space
_PATTERN_TRAILING_WHITESPACE: Final[Pattern] = \
    _compile(r"[ \t]+\n", flags=MULTILINE)


class Path(str):
    """
    An immutable representation of a canonical path.

    All instances of this class identify a fully-qualified path which does not
    contain any relative parts (`"."` or `".."`), is fully expanded, and, if
    the file system is case-insensitive, has the case normalized. A path is
    also an instance of `str`, so it can be used wherever strings are required
    and functions can be designed to accept `str` and receive `Path` instances
    instead.
    """

    def __new__(cls, value: str):  # noqa
        """
        Construct the object.

        :param value: the string value

        >>> isinstance(Path("."), Path)
        True
        >>> isinstance(Path("."), str)
        True
        >>> isinstance(Path(".")[-2:], Path)
        False
        >>> isinstance(Path(".")[-2:], str)
        True
        >>> isinstance(Path(__file__).strip(), Path)
        False
        """
        return super().__new__(cls, _canonicalize_path(value))

    def is_file(self) -> bool:
        """
        Check if this path identifies an existing file.

        See also :meth:`~enforce_file`, which raises an error if the `is_file`
        is not `True`.

        :returns: `True` if this path identifies an existing file, `False`
            otherwise.

        >>> Path(__file__).is_file()
        True
        >>> from os.path import dirname
        >>> Path(dirname(__file__)).is_file()
        False
        """
        return isfile(self)

    def enforce_file(self) -> None:
        """
        Raise an error if the path does not reference an existing file.

        This function uses :meth:`is_file` internally and raises a
        `ValueError` if it returns `False`. It is therefore a shorthand
        for situations where you want to have an error if a path does
        not identify a file.

        :raises ValueError:  if this path does not reference an existing file

        >>> Path(__file__).enforce_file()   # nothing happens
        >>> from os import getcwd
        >>> try:
        ...     Path(getcwd()).enforce_file()
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        does not identify a file.
        """
        if not self.is_file():
            raise ValueError(f"Path {self!r} does not identify a file.")

    def is_dir(self) -> bool:
        """
        Check if this path identifies an existing directory.

        The method :meth:`~enforce_dir` also checks this, but raises an
        exception if it is not `True`.

        :returns: `True` if this path identifies an existing directory,
            `False` otherwise.

        >>> Path(__file__).is_dir()
        False
        >>> from os.path import dirname
        >>> Path(dirname(__file__)).is_dir()
        True
        """
        return isdir(self)

    def enforce_dir(self) -> None:
        """
        Raise an error if the path does not reference an existing directory.

        This function uses :meth:`is_dir` internally and raises a
        `ValueError` if it returns `False`. It is therefore a shorthand
        for situations where you want to have an error if a path does
        not identify a directory.

        :raises ValueError:  if this path does not reference an existing
            directory

        >>> try:
        ...     Path(__file__).enforce_dir()
        ... except ValueError as ve:
        ...     print(str(ve)[-30:])
        does not identify a directory.
        >>> from os import getcwd
        >>> Path(getcwd()).enforce_dir()   # nothing happens
        """
        if not self.is_dir():
            raise ValueError(f"Path {self!r} does not identify a directory.")

    def contains(self, other: str) -> bool:
        """
        Check whether this path is a directory and contains another path.

        A file can never contain anything else. A directory contains itself as
        well as any sub-directories, i.e., `a/b/` contains `a/b/` and `a/b/c`.
        The function :meth:`~enforce_contains` throws an exception if the
        path does not contain `other`.

        :param other: the other path
        :return: `True` is this path contains the other path, `False` of not

        >>> from os.path import dirname
        >>> Path(dirname(__file__)).contains(__file__)
        True
        >>> Path(__file__).contains(__file__)
        False
        >>> Path(dirname(__file__)).contains(dirname(__file__))
        True
        >>> Path(__file__).contains(dirname(__file__))
        False
        >>> Path(join(dirname(__file__), "a")).contains(\
join(dirname(__file__), "b"))
        False
        >>> try:
        ...     Path(dirname(__file__)).contains(1)
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is int, namely '1'.
        >>> try:
        ...     Path(dirname(__file__)).contains(None)
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is None.
        >>> try:
        ...     Path(dirname(__file__)).contains("")
        ... except ValueError as ve:
        ...     print(ve)
        Path must not be empty.
        """
        return self.is_dir() and (
            commonpath([self]) == commonpath([self, Path.path(other)]))

    def enforce_contains(self, other: str) -> None:
        """
        Raise an exception if this is not a directory containing another path.

        The method :meth:`contains` checks whether this path is a directory
        and contains the other path and returns the result of this check as a
        `bool`. This function here raises an exception if that check fails.

        :param other: the other path
        :raises ValueError: if `other` is not a sub-path of this path.

        >>> try:
        ...     Path(__file__).enforce_contains(__file__)
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        not identify a directory.
        >>> from os.path import dirname
        >>> Path(dirname(__file__)).enforce_contains(__file__)  # nothing
        >>> try:
        ...     Path(join(dirname(__file__), "a")).enforce_contains(\
Path(join(dirname(__file__), "b")))
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        not identify a directory.
        >>> Path(dirname(__file__)).enforce_contains(Path(join(dirname(\
__file__), "b")))  # nothing happens
        >>> try:
        ...     Path(dirname(__file__)).enforce_contains(dirname(\
dirname(__file__)))
        ... except ValueError as ve:
        ...     print(str(ve)[:4])
        ...     print("does not contain" in str(ve))
        Path
        True
        """
        self.enforce_dir()
        if not self.contains(other):
            raise ValueError(f"Path {self!r} does not contain {other!r}.")

    def resolve_inside(self, relative_path: str) -> "Path":
        """
        Resolve a relative path to an absolute path inside this path.

        Resolve the relative path inside this path. This path must identify
        a directory. The relative path cannot contain anything that makes it
        leave the directory, e.g., any `".."`. The paths are joined and then
        it is enforced that this path must contain the result via
        :meth:`enforce_contains` and otherwise an error is raised.

        :param relative_path: the path to resolve
        :return: the resolved child path
        :raises TypeError: If the `relative_path` is not a string.
        :raises ValueError: If the `relative_path` would resolve to something
            outside of this path and/or if it is empty.

        >>> from os.path import dirname
        >>> Path(dirname(__file__)).resolve_inside("a.txt")[-5:]
        'a.txt'
        >>> from os.path import basename
        >>> Path(dirname(__file__)).resolve_inside(basename(__file__)) \
== Path(__file__)
        True
        >>> try:
        ...     Path(dirname(__file__)).resolve_inside("..")
        ... except ValueError as ve:
        ...     print("does not contain" in str(ve))
        True
        >>> try:
        ...     Path(__file__).resolve_inside("..")
        ... except ValueError as ve:
        ...     print("does not identify a directory" in str(ve))
        True
        >>> try:
        ...     Path(dirname(__file__)).resolve_inside(None)
        ... except TypeError as te:
        ...     print(te)
        relative_path should be an instance of str but is None.
        >>> try:
        ...     Path(dirname(__file__)).resolve_inside(2)
        ... except TypeError as te:
        ...     print(te)
        relative_path should be an instance of str but is int, namely '2'.
        >>> try:
        ...     Path(__file__).resolve_inside("")
        ... except ValueError as ve:
        ...     print("Stripped relative path cannot become empty" in str(ve))
        True
        """
        if not isinstance(relative_path, str):
            raise type_error(relative_path, "relative_path", str)
        rp: Final[str] = relative_path.strip()
        if len(rp) == 0:
            raise ValueError("Stripped relative path cannot become empty, "
                             f"but {relative_path!r} does.")
        opath: Final[Path] = Path.path(join(self, relative_path))
        self.enforce_contains(opath)
        return opath

    def ensure_file_exists(self) -> bool:
        """
        Atomically ensure that the file exists and create it otherwise.

        While :meth:`is_file` checks if the path identifies an existing file
        and :meth:`enforce_file` raises an error if it does not, this method
        here creates the file if it does not exist. The method can only create
        the file if the directory already exists.

        :return: `True` if the file already existed and
            `False` if it was newly and atomically created.
        :raises: ValueError if anything goes wrong during the file creation

        >>> print(Path(__file__).ensure_file_exists())
        True
        >>> from os.path import dirname
        >>> try:
        ...     Path.path(dirname(__file__)).ensure_file_exists()
        ...     print("??")
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        >>> try:
        ...     Path.path(join(join(dirname(__file__), "a"), "b"))\
.ensure_file_exists()
        ...     print("??")
        ... except ValueError as ve:
        ...     print("Error when trying to create file" in str(ve))
        True
        """
        existed: bool = False
        try:
            osclose(osopen(self, O_CREAT | O_EXCL))
        except FileExistsError:
            existed = True
        except Exception as err:
            raise ValueError(
                f"Error when trying to create file {self!r}.") from err
        self.enforce_file()
        return existed

    def ensure_dir_exists(self) -> None:
        """
        Make sure that the directory exists, create it otherwise.

        Method :meth:`is_dir` checks whether the path identifies an
        existing directory, method :meth:`enforce_dir` raises an error if not,
        and this method creates the directory if it does not exist.

        :raises ValueError: if the directory did not exist and creation failed

        >>> from os.path import dirname
        >>> Path(dirname(__file__)).ensure_dir_exists()  # nothing happens
        >>> try:
        ...     Path(__file__).ensure_dir_exists()
        ... except ValueError as ve:
        ...     print("does not identify a directory" in str(ve))
        True
        >>> try:
        ...     Path(join(__file__, "a")).ensure_dir_exists()
        ... except ValueError as ve:
        ...     print("Error when trying to create directory" in str(ve))
        True
        >>> from tempfile import mkdtemp
        >>> from os import rmdir as osrmdirx
        >>> td = mkdtemp()
        >>> Path(td).ensure_dir_exists()
        >>> osrmdirx(td)
        >>> Path(td).ensure_dir_exists()
        >>> p = Path(td).resolve_inside("a")
        >>> p.ensure_dir_exists()
        >>> p2 = p.resolve_inside("b")
        >>> p2.ensure_dir_exists()
        >>> osrmdirx(p2)
        >>> osrmdirx(p)
        >>> osrmdirx(td)
        >>> p2.ensure_dir_exists()
        >>> osrmdirx(p2)
        >>> osrmdirx(p)
        >>> osrmdirx(td)
        """
        try:
            makedirs(name=self, exist_ok=True)
        except FileExistsError:
            pass
        except Exception as err:
            raise ValueError(
                f"Error when trying to create directory {self!r}.") from err
        self.enforce_dir()

    def open_for_read(self) -> TextIOBase:
        r"""
        Open this file for reading text.

        The resulting text stream will automatically use the right encoding
        and take any encoding error serious. If the path does not identify an
        existing file, an exception is thrown.

        :return: the file open for reading
        :raises ValueError: if the path does not identify a file

        >>> with Path(__file__).open_for_read() as rd:
        ...     print(f"{len(rd.readline())}")
        ...     print(f"{rd.readline()!r}")
        4
        'The class `Path` for handling paths to files and directories.\n'
        >>> from os.path import dirname
        >>> try:
        ...     with Path(dirname(__file__)).open_for_read():
        ...         pass
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        self.enforce_file()
        return cast(TextIOBase, open(  # noqa
            self, encoding=_get_text_encoding(self), errors="strict"))

    def read_all_list(self) -> list[str]:
        r"""
        Read all the lines in a file and return a list of them.

        Return a list of all lines in a file. The white space on the
        right-hand side of the lines is stripped. If the path does not
        identify a file, an error is thrown. If the file is empty, an error
        is thrown. In other words, if this routine returns successfully,
        the list it returns will not be empty. All strings in the list will
        be right-stripped. In other words, they will not contain any newline
        or other space characters on the right side.

        Different from :meth:`~read_all_str`, the contents of the file are
        packaged nicely into a list of strings line-by-line.

        :return: the list of strings of text
        :raises ValueError: if the path does not identify a file or if the
            file it identifies is empty

        >>> Path(__file__).read_all_list()[1]
        'The class `Path` for handling paths to files and directories.'
        >>> from os.path import dirname
        >>> try:
        ...     Path(dirname(__file__)).read_all_list()
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> try:
        ...     Path(p).read_all_list()
        ... except ValueError as ve:
        ...     print("contains no text." in str(ve))
        True
        >>> with open(p, "wt") as tx:
        ...     tx.write("aa\n")
        ...     tx.write(" bb   ")
        3
        6
        >>> Path(p).read_all_list()
        ['aa', ' bb']
        >>> osremovex(p)
        """
        with self.open_for_read() as reader:
            ret: list[str] = reader.readlines()
        if not isinstance(ret, list):  # this should never happen
            raise type_error(ret, f"return value of reading {self!r}", list)
        if len(ret) <= 0:  # if the file is empty, throw an error
            raise ValueError(f"File {self!r} contains no text.")
        for i, s in enumerate(ret):
            if not isinstance(s, str):  # this should never happen
                raise type_error(s, f"read[{i}]", str)
            ret[i] = s.rstrip()  # remove trailing white space and newlines
        return ret

    def read_all_str(self) -> str:
        r"""
        Read a file as a single string.

        Different from :meth:`read_all_list`, the text is not stripped of any
        white space. It is presented as a single string exactly in the way it
        was written to the file.

        :return: the single string of text
        :raises ValueError: if the path does not identify a file or if the
            file it identifies is empty

        >>> Path(__file__).read_all_str()[4:30]
        'The class `Path` for handl'
        >>> from os.path import dirname
        >>> try:
        ...     Path(dirname(__file__)).read_all_list()
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> try:
        ...     Path(p).read_all_str()
        ... except ValueError as ve:
        ...     print("contains no text." in str(ve))
        True
        >>> with open(p, "wt") as tx:
        ...     tx.write("aa\n")
        ...     tx.write(" bb   ")
        3
        6
        >>> Path(p).read_all_str()
        'aa\n bb   '
        >>> osremovex(p)
        """
        with self.open_for_read() as reader:
            ret: str = reader.read()
        if not isinstance(ret, str):  # this should never happen
            raise type_error(ret, f"return value of reading {self!r}", str)
        if len(ret) <= 0:  # if the file is empty, throw an error
            raise ValueError(f"File {self!r} contains no text.")
        return ret

    def open_for_write(self) -> TextIOBase:
        """
        Open the file for writing UTF-8 encoded text.

        If the path cannot be opened for writing, some error will be raised.

        :return: the text io wrapper for writing
        :raises ValueError: if the path does not identify a file or such a
            file cannot be created

        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> with Path(p).open_for_write() as wd:
        ...     wd.write("1234")
        4
        >>> Path(p).read_all_str()
        '1234'
        >>> osremovex(p)
        >>> from os.path import dirname
        >>> try:
        ...     with Path(dirname(__file__)).open_for_write() as wd:
        ...         pass
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        self.ensure_file_exists()
        return cast(TextIOBase, open(  # noqa
            self, mode="w", encoding="utf-8", errors="strict"))

    def write_all(self, contents: str | Iterable[str]) -> None:
        r"""
        Write all the lines to this file.

        :param contents: the contents to write
        :raises TypeError: if the contents are not a string or an `Iterable`
            of strings
        :raises ValueError: if the contents are empty or if the path is not a
            file or it cannot be opened as a file

        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> try:
        ...     Path(p).write_all(None)
        ... except TypeError as te:
        ...     print(str(te)[6:])
        ts should be an instance of any in {str, typing.Iterable} but is None.
        >>> try:
        ...     Path(p).write_all(["1", 3])
        ... except TypeError as te:
        ...     print(te)
        value should be an instance of str but is int, namely '3'.
        >>> try:
        ...     Path(p).write_all([""])
        ... except ValueError as ve:
        ...     print(ve)
        Writing empty text is not permitted.
        >>> try:
        ...     Path(p).write_all("")
        ... except ValueError as ve:
        ...     print(ve)
        Writing empty text is not permitted.
        >>> try:
        ...     Path(p).write_all(["", ""])
        ... except ValueError as ve:
        ...     print(ve)
        Text becomes empty after removing trailing whitespace?
        >>> Path(p).write_all(["", "a", "b  "])
        >>> print(Path(p).read_all_list())
        ['', 'a', 'b']
        >>> Path(p).write_all(" \na\n b ")
        >>> print(Path(p).read_all_list())
        ['', 'a', ' b']
        >>> osremovex(p)
        >>> from os.path import dirname
        >>> try:
        ...     Path(dirname(__file__)).write_all("a")
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        if not isinstance(contents, str):
            if not isinstance(contents, Iterable):
                raise type_error(contents, "contents", (str, Iterable))
            contents = "\n".join(map(str.rstrip, map(must_be_str, contents)))
        if len(contents) == 0:  # empty content is not OK
            raise ValueError("Writing empty text is not permitted.")
        # get rid of the white space trailing in lines
        contents = regex_sub(_PATTERN_TRAILING_WHITESPACE,
                             "\n", contents.rstrip())
        if len(contents) <= 0:  # empty after removing trailing white space
            raise ValueError(
                "Text becomes empty after removing trailing whitespace?")
        with self.open_for_write() as writer:
            writer.write(contents)
            if contents[-1] != "\n":  # that will always be the case...
                writer.write("\n")

    @staticmethod
    def path(path: str) -> "Path":
        """
        Get a canonical path from a string.

        :param path: the path to canonicalize
        :return: the `Path` instance
        :raises TypeError: if `path` is not a string
        :raises ValueError: if `path` is an empty string

        >>> isinstance(__file__, Path)
        False
        >>> isinstance(Path.path(__file__), Path)
        True
        >>> try:
        ...     Path.path(None)
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is None.
        >>> try:
        ...     Path.path(1)
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is int, namely '1'.
        >>> try:
        ...     Path.path("")
        ... except ValueError as ve:
        ...     print(ve)
        Path must not be empty.
        """
        if isinstance(path, Path):
            return cast(Path, path)
        return Path(path)

    @staticmethod
    def file(path: str) -> "Path":
        """
        Get a path identifying an existing file.

        This is a shorthand for creating a :class:`~Path` and then invoking
        :meth:`~enforce_file`.

        :param path: the path
        :return: the file

        >>> Path.file(__file__)[-20:]
        'pycommons/io/path.py'
        >>> from os.path import dirname
        >>> try:
        ...     Path.file(dirname(__file__))
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        fi: Final[Path] = Path.path(path)
        fi.enforce_file()
        return fi

    @staticmethod
    def directory(path: str) -> "Path":
        """
        Get a path identifying an existing directory.

        This is a shorthand for creating a :class:`~Path` and then invoking
        :meth:`~enforce_dir`.

        :param path: the path
        :return: the file

        >>> from os.path import dirname
        >>> Path.directory(dirname(__file__))[-12:]
        'pycommons/io'
        >>> try:
        ...     Path.directory(__file__)
        ... except ValueError as ve:
        ...     print("does not identify a directory." in str(ve))
        True
        """
        fi: Final[Path] = Path.path(path)
        fi.enforce_dir()
        return fi
