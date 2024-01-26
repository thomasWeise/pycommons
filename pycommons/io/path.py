"""
The class `Path` for handling paths to files and directories.

The instances of :class:`Path` identify file system paths.
They are always fully canonicalized with all relative components resolved.
They thus allow the clear identification of files and directories.
They also offer support for opening streams, creating paths to sub-folders,
and so on.
"""

import codecs
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
    relpath,
)
from typing import Callable, Final, Iterator, TextIO, cast

from pycommons.io.streams import as_input_stream, as_output_stream


def _canonicalize_path(path: str) -> str:
    """
    Check and canonicalize a path.

    A canonicalized path does not contain any relative components, is fully
    expanded, and, in case-insensitive file systems, using the normal case.

    :param path: the path
    :return: the canonicalized path

    >>> try:
    ...     _canonicalize_path(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     _canonicalize_path(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     _canonicalize_path("")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not be empty.

    >>> try:
    ...     _canonicalize_path(" ")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not start or end with white space, but ' ' does.

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
    """
    if str.__len__(path) <= 0:
        raise ValueError("Path must not be empty.")
    if str.strip(path) != path:
        raise ValueError("Path must not start or end with white space, "
                         f"but {path!r} does.")
    path = normcase(abspath(realpath(expanduser(expandvars(path)))))
    if (str.__len__(path) <= 0) or (path in [".", ".."]):
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
        descriptor '__len__' requires a 'str' object but received a 'int'
        >>> try:
        ...     Path(dirname(__file__)).contains(None)
        ... except TypeError as te:
        ...     print(te)
        descriptor '__len__' requires a 'str' object but received a 'NoneType'
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
        descriptor '__len__' requires a 'str' object but received a 'NoneType'
        >>> try:
        ...     Path(dirname(__file__)).resolve_inside(2)
        ... except TypeError as te:
        ...     print(te)
        descriptor '__len__' requires a 'str' object but received a 'int'
        >>> try:
        ...     Path(__file__).resolve_inside("")
        ... except ValueError as ve:
        ...     print(ve)
        Relative path must not be empty.
        >>> try:
        ...     Path(__file__).resolve_inside(" ")
        ... except ValueError as ve:
        ...     print(ve)
        Relative path must not start or end with white space, but ' ' does.
        """
        if str.__len__(relative_path) == 0:
            raise ValueError("Relative path must not be empty.")
        if str.strip(relative_path) != relative_path:
            raise ValueError("Relative path must not start or end with white "
                             f"space, but {relative_path!r} does.")
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

    def __open_for_read(self) -> TextIO:
        r"""
        Open this file for reading text.

        The resulting text stream will automatically use the right encoding
        and take any encoding error serious. If the path does not identify an
        existing file, an exception is thrown.

        :return: the file open for reading
        :raises ValueError: if the path does not identify a file

        >>> with Path(__file__)._Path__open_for_read() as rd:
        ...     print(f"{len(rd.readline())}")
        ...     print(f"{rd.readline()!r}")
        4
        'The class `Path` for handling paths to files and directories.\n'
        >>> from os.path import dirname
        >>> try:
        ...     with Path(dirname(__file__))._Path__open_for_read():
        ...         pass
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        does not identify a file.
        """
        self.enforce_file()
        return open(  # noqa: SIM115
            self, encoding=_get_text_encoding(self), errors="strict")

    def open_for_read(self) -> Iterator[str]:
        r"""
        Open this file for reading text.

        The resulting text stream will automatically use the right encoding
        and take any encoding error serious. If the path does not identify an
        existing file, an exception is thrown. The text stream is returned in
        form of an `Iterator` of strings. To each line returned by this
        iterator, :meth:`str.rstrip` is applied. The underlying stream is
        closed once the iteration is finished or the iterator leaves the scope.

        :return: the file open for reading
        :raises ValueError: if the path does not identify a file

        >>> siter = Path(__file__).open_for_read()
        >>> print(f"{len(next(siter))}")
        3
        >>> next(siter)
        'The class `Path` for handling paths to files and directories.'
        >>> del siter
        >>> from os.path import dirname
        >>> try:
        ...     for s in Path(dirname(__file__)).open_for_read():
        ...         pass
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        does not identify a file.
        """
        return as_input_stream(self.__open_for_read())

    def read_all_str(self) -> str:
        r"""
        Read a file as a single string.

        Read the complete contents of a file as a single string. If the file
        is empty, an exception will be raised. No modification is applied to
        the text that is read.

        :return: the single string of text
        :raises ValueError: if the path does not identify a file or if the
            file it identifies is empty

        >>> Path(__file__).read_all_str()[4:30]
        'The class `Path` for handl'
        >>> from os.path import dirname
        >>> try:
        ...     Path(dirname(__file__)).read_all_str()
        ... except ValueError as ve:
        ...     print(str(ve)[-25:])
        does not identify a file.
        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> try:
        ...     Path(p).read_all_str()
        ... except ValueError as ve:
        ...     print(str(ve)[-19:])
        ' contains no text.
        >>> with open(p, "wt") as tx:
        ...     tx.write("aa\n")
        ...     tx.write(" bb   ")
        3
        6
        >>> Path(p).read_all_str()
        'aa\n bb   '
        >>> osremovex(p)
        """
        with self.__open_for_read() as reader:
            res: Final[str] = reader.read()
        if str.__len__(res) <= 0:
            raise ValueError(f"File {self!r} contains no text.")
        return res

    def __open_for_write(self) -> TextIO:
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
        >>> with Path(p)._Path__open_for_write() as wd:
        ...     wd.write("1234")
        4
        >>> Path(p).read_all_str()
        '1234'
        >>> osremovex(p)
        >>> from os.path import dirname
        >>> try:
        ...     with Path(dirname(__file__))._Path__open_for_write() as wd:
        ...         pass
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        self.ensure_file_exists()
        return open(  # noqa: SIM115
            self, mode="w", encoding="utf-8", errors="strict")

    def open_for_write(self) -> Callable[[str], None]:
        r"""
        Open the file for writing UTF-8 encoded text.

        If the path cannot be opened for writing, some error will be raised.

        :return: a function which accepts line strings (no `\n` termination is
            needed). You can pass the text to this function line-by-line. As
            soon as it leaves the scope, the text stream will be closed.
        :raises ValueError: if the path does not identify a file or such a
            file cannot be created

        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> with Path(p).open_for_write() as wd:
        ...     wd("1234")
        >>> Path(p).read_all_str()
        '1234\n'
        >>> osremovex(p)
        >>> from os.path import dirname
        >>> try:
        ...     with Path(dirname(__file__)).open_for_write() as wd:
        ...         pass
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        return as_output_stream(self.__open_for_write())

    def write_all_str(self, contents: str) -> None:
        r"""
        Write the given string to the file.

        The string `contents` is written to a file. If it does not end
        with `\n`, then `\n` will automatically be appended. No other changes
        are applied to `contents`. `contents` must be a `str` and it must not
        be empty.

        :param contents: the contents to write
        :raises TypeError: if the contents are not a string or an `Iterable`
            of strings
        :raises ValueError: if the path is not a file or it cannot be opened
            as a file or the `contents` are an empty string

        >>> from tempfile import mkstemp
        >>> from os import remove as osremovex
        >>> h, p = mkstemp(text=True)
        >>> osclose(h)
        >>> try:
        ...     Path(p).write_all_str(None)
        ... except TypeError as te:
        ...     print(str(te))
        descriptor '__len__' requires a 'str' object but received a 'NoneType'
        >>> try:
        ...     Path(p).write_all_str(["a"])
        ... except TypeError as te:
        ...     print(str(te))
        descriptor '__len__' requires a 'str' object but received a 'list'
        >>> Path(p).write_all_str("\na\nb")
        >>> Path(p).read_all_str()
        '\na\nb\n'
        >>> Path(p).write_all_str(" \na\n b ")
        >>> Path(p).read_all_str()
        ' \na\n b \n'
        >>> try:
        ...     Path(p).write_all_str("")
        ... except ValueError as ve:
        ...     print(str(ve)[:34])
        Cannot write empty content to file
        >>> osremovex(p)
        >>> from os.path import dirname
        >>> try:
        ...     Path(dirname(__file__)).write_all_str("a")
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True
        """
        ll: Final[int] = str.__len__(contents)
        if ll <= 0:
            raise ValueError(f"Cannot write empty content to file {self!r}.")
        with self.__open_for_write() as writer:
            writer.write(contents)
            if contents[ll - 1] != "\n":
                writer.write("\n")

    def relative_to(self, base_path: str) -> str:
        """
        Compute a relative path of this path towards the given base path.

        :param base_path: the string
        :return: a relative path
        :raises ValueError: if this path is not inside `base_path` or the
            relativization result is otherwise invalid

        >>> from os.path import dirname
        >>> f = Path.file(__file__)
        >>> d1 = Path.directory(dirname(f))
        >>> d2 = Path.directory(dirname(d1))
        >>> d3 = Path.directory(dirname(d2))
        >>> f.relative_to(d1)
        'path.py'
        >>> f.relative_to(d2)
        'io/path.py'
        >>> f.relative_to(d3)
        'pycommons/io/path.py'
        >>> d1.relative_to(d3)
        'pycommons/io'
        >>> d1.relative_to(d1)
        '.'
        >>> try:
        ...     d1.relative_to(f)
        ... except ValueError as ve:
        ...     print(str(ve)[-30:])
        does not identify a directory.
        >>> try:
        ...     d2.relative_to(d1)
        ... except ValueError as ve:
        ...     print(str(ve)[-21:])
        pycommons/pycommons'.
        """
        opath: Final[Path] = Path.path(base_path)
        opath.enforce_contains(self)
        rv: Final[str] = relpath(self, opath)
        if (str.__len__(rv) == 0) or (str.strip(rv) is not rv):
            raise ValueError(
                f"Invalid relative path {rv!r} resulting from relativizing "
                f"{self!r} to {base_path!r}={opath!r}.")
        return rv

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
        descriptor '__len__' requires a 'str' object but received a 'NoneType'
        >>> try:
        ...     Path.path(1)
        ... except TypeError as te:
        ...     print(te)
        descriptor '__len__' requires a 'str' object but received a 'int'
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
