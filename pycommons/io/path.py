"""
The class `Path` for handling paths to files and directories.

The instances of :class:`Path` identify file system paths.
They are always fully canonicalized with all relative components resolved.
They thus allow the clear and unique identification of files and directories.
They also offer support for opening streams, creating paths to sub-folders,
and so on.

The first goal is to encapsulate the functionality of the :mod:`os.path`
module into a single class.
The second goal is to make sure that we do not run into any dodgy situation
with paths pointing to security-sensitive locations or something due to
strange `.` and `..` trickery.
If you try to resolve a path inside a directory and the resulting canonical
path is outside that directory, you get an error raised, for example.
"""

import codecs
from io import TextIOBase
from os import O_CREAT, O_EXCL, O_TRUNC, makedirs, scandir
from os import close as osclose
from os import open as osopen
from os import remove as osremove
from os.path import (
    abspath,
    commonpath,
    dirname,
    expanduser,
    expandvars,
    isdir,
    isfile,
    join,
    normcase,
    realpath,
    relpath,
)
from os.path import basename as osbasename
from os.path import exists as osexists
from shutil import rmtree
from typing import Any, Callable, Final, Iterable, Iterator, TextIO, cast

from pycommons.types import check_int_range, type_error

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
    >>> from os import close as osxclose
    >>> from os import remove as osremove
    >>> (h, tf) = mkstemp()
    >>> osxclose(h)
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

    >>> try:
    ...     Path(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     Path(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     Path("")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not be empty.

    >>> try:
    ...     Path(" ")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not start or end with white space, but ' ' does.

    >>> from os.path import dirname
    >>> Path(dirname(realpath(__file__)) + '/..') == \
dirname(dirname(realpath(__file__)))
    True

    >>> Path(dirname(realpath(__file__)) + "/.") == \
dirname(realpath(__file__))
    True

    >>> Path(__file__) == realpath(__file__)
    True

    >>> from os import getcwd
    >>> Path(".") == realpath(getcwd())
    True

    >>> from os import getcwd
    >>> Path("..") == dirname(realpath(getcwd()))
    True

    >>> from os import getcwd
    >>> Path("../.") == dirname(realpath(getcwd()))
    True

    >>> from os import getcwd
    >>> Path("../1.txt") == \
join(dirname(realpath(getcwd())), "1.txt")
    True

    >>> from os import getcwd
    >>> Path("./1.txt") == join(realpath(getcwd()), "1.txt")
    True

    >>> from os.path import isabs
    >>> isabs(Path(".."))
    True
    """

    def __new__(cls, value: Any):  # noqa
        """
        Construct the path object by normalizing the path string.

        :param value: the string value
        :raises TypeError: if `value` is not a string
        :raises ValueError: if `value` is not a proper path

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

        >>> isinstance(__file__, Path)
        False
        >>> isinstance(Path(__file__), Path)
        True
        >>> p = Path(__file__)
        >>> Path(p) is p
        True

        >>> try:
        ...     Path(None)
        ... except TypeError as te:
        ...     print(te)
        descriptor '__len__' requires a 'str' object but received a 'NoneType'

        >>> try:
        ...     Path(1)
        ... except TypeError as te:
        ...     print(te)
        descriptor '__len__' requires a 'str' object but received a 'int'

        >>> try:
        ...     Path("")
        ... except ValueError as ve:
        ...     print(ve)
        Path must not be empty.
        """
        if isinstance(value, Path):
            return cast(Path, value)

        if str.__len__(value) <= 0:
            raise ValueError("Path must not be empty.")
        if str.strip(value) != value:
            raise ValueError("Path must not start or end with white space, "
                             f"but {value!r} does.")
        value = normcase(abspath(realpath(expanduser(expandvars(value)))))
        if (str.__len__(value) <= 0) or (value in [".", ".."]):
            raise ValueError(f"Canonicalization cannot yield {value!r}.")

        return super().__new__(cls, value)

    def exists(self) -> bool:
        """
        Check if this path identifies an existing file or directory.

        See also :meth:`~Path.is_file` and :meth:`~Path.is_dir`.

        :returns: `True` if this path identifies an existing file, `False`
            otherwise.

        >>> Path(__file__).exists()
        True
        >>> from os.path import dirname
        >>> Path(dirname(__file__)).exists()
        True
        >>> from tempfile import mkstemp
        >>> from os import close as osxclose
        >>> from os import remove as osremove
        >>> (h, tf) = mkstemp()
        >>> osxclose(h)
        >>> p = Path(tf)
        >>> p.exists()
        True
        >>> osremove(p)
        >>> p.exists()
        False
        """
        return osexists(self)

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
            commonpath([self]) == commonpath([self, Path(other)]))

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
        opath: Final[Path] = Path(join(self, relative_path))
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
        ...     Path(dirname(__file__)).ensure_file_exists()
        ...     print("??")
        ... except ValueError as ve:
        ...     print("does not identify a file." in str(ve))
        True

        >>> try:
        ...     Path(join(join(dirname(__file__), "a"), "b"))\
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

    def create_file_or_truncate(self) -> None:
        """
        Create the file identified by this path and truncate it if it exists.

        :raises: ValueError if anything goes wrong during the file creation

        >>> from tempfile import mkstemp
        >>> from os import close as osxclose
        >>> from os import remove as osremove
        >>> (h, tf) = mkstemp()
        >>> osxclose(h)

        >>> pth = Path(tf)
        >>> pth.write_all_str("test")
        >>> print(pth.read_all_str())
        test
        <BLANKLINE>

        >>> pth.create_file_or_truncate()
        >>> pth.is_file()
        True

        >>> try:
        ...     pth.read_all_str()
        ... except ValueError as ve:
        ...     print(str(ve)[-17:])
        contains no text.

        >>> osremove(pth)
        >>> pth.is_file()
        False

        >>> pth.create_file_or_truncate()
        >>> pth.is_file()
        True

        >>> osremove(pth)

        >>> from os import makedirs as osmkdir
        >>> from os import rmdir as osrmdir
        >>> osmkdir(pth)

        >>> try:
        ...     pth.create_file_or_truncate()
        ... except ValueError as ve:
        ...     print(str(ve)[:35])
        Error when truncating/creating file

        >>> osrmdir(pth)
        """
        try:
            osclose(osopen(self, O_CREAT | O_TRUNC))
        except BaseException as err:  # noqa: B036
            raise ValueError(
                f"Error when truncating/creating file {self!r}.") from err
        self.enforce_file()

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

    def ensure_parent_dir_exists(self) -> "Path":
        """
        Make sure that the parent directory exists, create it otherwise.

        This path may identify a file or directory to be created that does not
        yet exist. The parent directory of this path is ensured to exist,
        i.e., if it already exists, nothing happens, but if it does not yet
        exist, it is created. If the parent directory cannot be created, a
        :class:`ValueError` is raised.

        :returns: the parent dir
        :raises ValueError: if the directory did not exist and creation failed

        >>> from os.path import dirname
        >>> _ = Path(__file__).ensure_parent_dir_exists()  # nothing happens

        >>> try:
        ...     _ = Path(join(__file__, "a")).ensure_parent_dir_exists()
        ... except ValueError as ve:
        ...     print("does not identify a directory" in str(ve))
        True

        >>> from tempfile import mkdtemp
        >>> from os import rmdir as osrmdirx
        >>> td = mkdtemp()
        >>> tf = Path(join(td, "xxx"))
        >>> _ = tf.ensure_parent_dir_exists()
        >>> osrmdirx(td)
        >>> isdir(dirname(tf))
        False
        >>> _ = tf.ensure_parent_dir_exists()
        >>> isdir(dirname(tf))
        True
        >>> osrmdirx(td)

        >>> td = mkdtemp()
        >>> isdir(td)
        True
        >>> td2 = join(td, "xxx")
        >>> isdir(td2)
        False
        >>> tf = join(td2, "xxx")
        >>> _ = Path(tf).ensure_parent_dir_exists()
        >>> isdir(td2)
        True
        >>> osrmdirx(td2)
        >>> osrmdirx(td)

        >>> td = mkdtemp()
        >>> isdir(td)
        True
        >>> td2 = join(td, "xxx")
        >>> isdir(td2)
        False
        >>> td3 = join(td2, "xxx")
        >>> isdir(td3)
        False
        >>> tf = join(td3, "xxx")
        >>> _ = Path(tf).ensure_parent_dir_exists()
        >>> isdir(td3)
        True
        >>> isdir(td2)
        True
        >>> osrmdirx(td3)
        >>> osrmdirx(td2)
        >>> osrmdirx(td)
        """
        pd: Final[Path] = Path(dirname(self))
        Path.ensure_dir_exists(pd)
        return pd

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
        ...     print(str(ve)[-25:])
        does not identify a file.
        """
        self.enforce_file()
        return cast(TextIOBase, open(  # noqa: SIM115
            self, encoding=_get_text_encoding(self), errors="strict"))

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
        with self.open_for_read() as reader:
            res: Final[str] = reader.read()
        if str.__len__(res) <= 0:
            raise ValueError(f"File {self!r} contains no text.")
        return res

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
        return cast(TextIOBase, open(  # noqa: SIM115
            self, mode="w", encoding="utf-8", errors="strict"))

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
        if str.__len__(contents) <= 0:
            raise ValueError(f"Cannot write empty content to file {self!r}.")
        with self.open_for_write() as writer:
            writer.write(contents)
            if contents[-1] != "\n":
                writer.write("\n")

    def relative_to(self, base_path: str) -> str:
        """
        Compute a relative path of this path towards the given base path.

        :param base_path: the string
        :return: a relative path
        :raises ValueError: if this path is not inside `base_path` or the
            relativization result is otherwise invalid

        >>> from os.path import dirname
        >>> f = file_path(__file__)
        >>> d1 = directory_path(dirname(f))
        >>> d2 = directory_path(dirname(d1))
        >>> d3 = directory_path(dirname(d2))
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
        opath: Final[Path] = Path(base_path)
        opath.enforce_contains(self)
        rv: Final[str] = relpath(self, opath)
        if (str.__len__(rv) == 0) or (str.strip(rv) is not rv):
            raise ValueError(
                f"Invalid relative path {rv!r} resulting from relativizing "
                f"{self!r} to {base_path!r}={opath!r}.")
        return rv

    def up(self, levels: int = 1) -> "Path":
        """
        Go up the directory tree for a given number of times.

        Get a `Path` identifying the containing directory, or its containing
        directory, depending on the number of `levels` specified.

        :param levels: the number levels to go up: `1` for getting the
            directly containing directory, `2` for the next higher directory,
            and so on.
        :return: the resulting path

        >>> f = file_path(__file__)
        >>> print(f.up()[-13:])
        /pycommons/io
        >>> print(f.up(1)[-13:])
        /pycommons/io
        >>> print(f.up(2)[-10:])
        /pycommons

        >>> try:
        ...     f.up(0)
        ... except ValueError as ve:
        ...     print(ve)
        levels=0 is invalid, must be in 1..255.

        >>> try:
        ...     f.up(None)
        ... except TypeError as te:
        ...     print(te)
        levels should be an instance of int but is None.

        >>> try:
        ...     f.up('x')
        ... except TypeError as te:
        ...     print(te)
        levels should be an instance of int but is str, namely 'x'.

        >>> try:
        ...     f.up(255)
        ... except ValueError as ve:
        ...     print(str(ve)[:70])
        Cannot go up from directory '/' anymore when going up for 255 levels f
        """
        s: str = self
        for _ in range(check_int_range(levels, "levels", 1, 255)):
            old: str = s
            s = dirname(s)
            if (str.__len__(s) == 0) or (s == old):
                raise ValueError(
                    f"Cannot go up from directory {old!r} anymore when going "
                    f"up for {levels} levels from {self!r}.")
        return directory_path(s)

    def basename(self) -> str:
        """
        Get the name of the file or directory identified by this path.

        :return: the name of the file or directory

        >>> file_path(__file__).basename()
        'path.py'
        >>> file_path(__file__).up(2).basename()
        'pycommons'

        >>> try:
        ...     Path("/").basename()
        ... except ValueError as ve:
        ...     print(ve)
        Invalid basename '' of path '/'.
        """
        s: Final[str] = osbasename(self)
        if str.__len__(s) <= 0:
            raise ValueError(f"Invalid basename {s!r} of path {self!r}.")
        return s

    def list_dir(self, files: bool = True,
                 directories: bool = True) -> Iterator["Path"]:
        """
        List the files and/or sub-directories in this directory.

        :return: an iterable with the fully-qualified paths

        >>> from tempfile import mkstemp, mkdtemp
        >>> from os import close as osxclose

        >>> dir1 = Path(mkdtemp())
        >>> dir2 = Path(mkdtemp(dir=dir1))
        >>> dir3 = Path(mkdtemp(dir=dir1))
        >>> (h, tf1) = mkstemp(dir=dir1)
        >>> osclose(h)
        >>> (h, tf2) = mkstemp(dir=dir1)
        >>> osclose(h)
        >>> file1 = Path(tf1)
        >>> file2 = Path(tf2)

        >>> set(dir1.list_dir()) == {dir2, dir3, file1, file2}
        True

        >>> set(dir1.list_dir(files=False)) == {dir2, dir3}
        True

        >>> set(dir1.list_dir(directories=False)) == {file1, file2}
        True

        >>> try:
        ...     dir1.list_dir(None)
        ... except TypeError as te:
        ...     print(te)
        files should be an instance of bool but is None.

        >>> try:
        ...     dir1.list_dir(1)
        ... except TypeError as te:
        ...     print(te)
        files should be an instance of bool but is int, namely '1'.

        >>> try:
        ...     dir1.list_dir(True, None)
        ... except TypeError as te:
        ...     print(te)
        directories should be an instance of bool but is None.

        >>> try:
        ...     dir1.list_dir(True, 1)
        ... except TypeError as te:
        ...     print(te)
        directories should be an instance of bool but is int, namely '1'.

        >>> try:
        ...     dir1.list_dir(False, False)
        ... except ValueError as ve:
        ...     print(ve)
        files and directories cannot both be False.

        >>> delete_path(dir1)
        """
        if not isinstance(files, bool):
            raise type_error(files, "files", bool)
        if not isinstance(directories, bool):
            raise type_error(directories, "directories", bool)
        if not (files or directories):
            raise ValueError("files and directories cannot both be False.")
        self.enforce_dir()
        return map(self.resolve_inside, (
            f.name for f in scandir(self) if (
                directories and f.is_dir(follow_symlinks=False)) or (
                files and f.is_file(follow_symlinks=False))))


def file_path(pathstr: str) -> "Path":
    """
    Get a path identifying an existing file.

    This is a shorthand for creating a :class:`~Path` and then invoking
    :meth:`~Path.enforce_file`.

    :param pathstr: the path
    :return: the file

    >>> file_path(__file__)[-20:]
    'pycommons/io/path.py'

    >>> from os.path import dirname
    >>> try:
    ...     file_path(dirname(__file__))
    ... except ValueError as ve:
    ...     print("does not identify a file." in str(ve))
    True
    """
    fi: Final[Path] = Path(pathstr)
    fi.enforce_file()
    return fi


def directory_path(pathstr: str) -> "Path":
    """
    Get a path identifying an existing directory.

    This is a shorthand for creating a :class:`~Path` and then invoking
    :meth:`~Path.enforce_dir`.

    :param pathstr: the path
    :return: the file

    >>> from os.path import dirname
    >>> directory_path(dirname(__file__))[-12:]
    'pycommons/io'

    >>> try:
    ...     directory_path(__file__)
    ... except ValueError as ve:
    ...     print("does not identify a directory." in str(ve))
    True
    """
    fi: Final[Path] = Path(pathstr)
    fi.enforce_dir()
    return fi


#: the ends-with check
__ENDSWITH: Final[Callable[[str, str], bool]] = cast(
    Callable[[str, str], bool], str.endswith)


def line_writer(output: TextIO | TextIOBase) -> Callable[[str], None]:
    r"""
    Create a line-writing :class:`typing.Callable` from an output stream.

    This function takes any string passed to it and writes it to the
    :class:`typing.TextIO` instance. If the string does not end in `"\n"`,
    it then writes `"\n"` as well to terminate the line. If something that
    is not a :class:`str` is passed in, it will throw a :class:`TypeError`.

    Notice that :meth:`~io.TextIOBase.write` and
    :meth:`~io.IOBase.writelines` of class :class:`io.TextIOBase` do not
    terminate lines that are written
    with a `"\n"`. This means that, unless you manually make sure that all
    lines are terminated by `"\n"`, they get written as a single line instead
    of multiple lines. To solve this issue conveniently, we provide the
    functions :func:`line_writer`, which wraps the
    :meth:`~io.TextIOBase.write` into another function, which automatically
    terminates all strings passed to it with `"\n"` unless they already end in
    `"\n"`, and :func:`write_lines`, which iterates over a sequence of strings
    and writes each of them to a given :class:`typing.TextIO` and automatically
    adds the `"\n"` terminator to each of them if necessary.

    :param output: the output stream
    :return: an instance of :class:`typing.Callable` that will write each
        string it receives as a properly terminated line to the output
        stream.
    :raises TypeError: if `output` is not an instance of
        :class:`io.TextIOBase`.

    >>> from tempfile import mkstemp
    >>> from os import close as osclose
    >>> from os import remove as osremove
    >>> (h, tf) = mkstemp()
    >>> osclose(h)

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("123")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("123\n")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("\n")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("123")
    ...     w("456")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123\n', '456\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("123  ")
    ...     w("")
    ...     w("  456")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123  \n', '\n', '  456\n']

    >>> with open(tf, "wt") as out:
    ...     w = line_writer(out)
    ...     w("123  \n")
    ...     w("\n")
    ...     w("  456")
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123  \n', '\n', '  456\n']

    >>> try:
    ...     with open(tf, "wt") as out:
    ...         w = line_writer(out)
    ...         w("123  ")
    ...         w(None)
    ... except TypeError as te:
    ...     print(str(te)[:-10])
    descriptor 'endswith' for 'str' objects doesn't apply to a 'NoneTy

    >>> try:
    ...     with open(tf, "wt") as out:
    ...         w = line_writer(out)
    ...         w("123  ")
    ...         w(2)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'endswith' for 'str' objects doesn't apply to a 'int' object

    >>> osremove(tf)

    >>> try:
    ...     line_writer(1)
    ... except TypeError as te:
    ...     print(te)
    output should be an instance of io.TextIOBase but is int, namely '1'.

    >>> try:
    ...     line_writer(None)
    ... except TypeError as te:
    ...     print(te)
    output should be an instance of io.TextIOBase but is None.
    """
    if not isinstance(output, TextIOBase):
        raise type_error(output, "output", TextIOBase)

    def __call(s: str, __w: Callable[[str], Any] = output.write) -> None:
        b: Final[bool] = __ENDSWITH(s, "\n")
        __w(s)
        if not b:
            __w("\n")

    return cast(Callable[[str], None], __call)


def write_lines(lines: Iterable[str], output: TextIO | TextIOBase) -> None:
    r"""
    Write all the lines in the given :class:`typing.Iterable` to the output.

    This function takes care of properly terminating lines using `"\n"` when
    writing them to an output and also performs type-checking.

    Notice that :meth:`~io.TextIOBase.write` and
    :meth:`~io.IOBase.writelines` of class :class:`io.TextIOBase` do not
    terminate lines that are written
    with a `"\n"`. This means that, unless you manually make sure that all
    lines are terminated by `"\n"`, they get written as a single line instead
    of multiple lines. To solve this issue conveniently, we provide the
    functions :func:`line_writer`, which wraps the
    :meth:`~io.TextIOBase.write` into another function, which automatically
    terminates all strings passed to it with `"\n"` unless they already end in
    `"\n"`, and :func:`write_lines`, which iterates over a sequence of strings
    and writes each of them to a given :class:`typing.TextIO` and automatically
    adds the `"\n"` terminator to each of them if necessary.

    :param lines: the lines
    :param output: the output
    :raises TypeError: If anything is of the wrong type.

    >>> from io import StringIO

    >>> with StringIO() as sio:
    ...     write_lines(("123", "456"), sio)
    ...     print(sio.getvalue())
    123
    456
    <BLANKLINE>

    >>> from io import StringIO
    >>> with StringIO() as sio:
    ...     write_lines(("123\n", "456"), sio)
    ...     print(sio.getvalue())
    123
    456
    <BLANKLINE>

    >>> from io import StringIO
    >>> with StringIO() as sio:
    ...     write_lines(("123\n", "456\n"), sio)
    ...     print(sio.getvalue())
    123
    456
    <BLANKLINE>

    >>> with StringIO() as sio:
    ...     write_lines(["123"], sio)
    ...     print(sio.getvalue())
    123
    <BLANKLINE>

    >>> with StringIO() as sio:
    ...     write_lines(["123\n"], sio)
    ...     print(sio.getvalue())
    123
    <BLANKLINE>

    >>> with StringIO() as sio:
    ...     write_lines("123", sio)
    ...     print(sio.getvalue())
    1
    2
    3
    <BLANKLINE>

    >>> with StringIO() as sio:
    ...     write_lines((sss for sss in ["123", "abc"]), sio)
    ...     print(sio.getvalue())
    123
    abc
    <BLANKLINE>

    >>> with StringIO() as sio:
    ...     write_lines("", sio)
    ...     print(sio.getvalue())
    <BLANKLINE>

    >>> from tempfile import mkstemp
    >>> from os import close as osclose
    >>> from os import remove as osremove
    >>> (h, tf) = mkstemp()
    >>> osclose(h)

    >>> with open(tf, "wt") as out:
    ...     write_lines(["123"], out)
    >>> with open(tf, "rt") as inp:
    ...     print(list(inp))
    ['123\n']

    >>> with open(tf, "wt") as out:
    ...     write_lines([""], out)
    >>> with open(tf, "rt") as inp:
    ...     print(repr(inp.read()))
    '\n'

    >>> with open(tf, "wt") as out:
    ...     write_lines(["\n"], out)
    >>> with open(tf, "rt") as inp:
    ...     print(repr(inp.read()))
    '\n'

    >>> with open(tf, "wt") as out:
    ...     write_lines([" \n"], out)
    >>> with open(tf, "rt") as inp:
    ...     print(repr(inp.read()))
    ' \n'

    >>> osremove(tf)

    >>> with StringIO() as sio:
    ...     write_lines(["\n"], sio)
    ...     print(repr(sio.getvalue()))
    '\n'

    >>> with StringIO() as sio:
    ...     write_lines([""], sio)
    ...     print(repr(sio.getvalue()))
    '\n'

    >>> sio = StringIO()
    >>> try:
    ...     write_lines(None, sio)
    ... except TypeError as te:
    ...     print(te)
    lines should be an instance of typing.Iterable but is None.

    >>> sio = StringIO()
    >>> try:
    ...     write_lines(123, sio)
    ... except TypeError as te:
    ...     print(te)
    lines should be an instance of typing.Iterable but is int, namely '123'.

    >>> sio = StringIO()
    >>> try:
    ...     write_lines([1, "sdf"], sio)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'endswith' for 'str' objects doesn't apply to a 'int' object

    >>> sio = StringIO()
    >>> try:
    ...     write_lines(["sdf", 1], sio)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'endswith' for 'str' objects doesn't apply to a 'int' object
    >>> print(repr(sio.getvalue()))
    'sdf\n'

    >>> try:
    ...     write_lines("x", None)
    ... except TypeError as te:
    ...     print(te)
    output should be an instance of io.TextIOBase but is None.

    >>> try:
    ...     write_lines("x", 1)
    ... except TypeError as te:
    ...     print(te)
    output should be an instance of io.TextIOBase but is int, namely '1'.

    >>> try:
    ...     write_lines(2, 1)
    ... except TypeError as te:
    ...     print(te)
    lines should be an instance of typing.Iterable but is int, namely '2'.
    """
    if not isinstance(lines, Iterable):
        raise type_error(lines, "lines", Iterable)
    if not isinstance(output, TextIOBase):
        raise type_error(output, "output", TextIOBase)

    wd: Final[Callable[[str], Any]] = output.write
    for line in lines:
        b: bool = __ENDSWITH(line, "\n")
        wd(line)
        if not b:
            wd("\n")


def delete_path(path: str) -> None:
    """
    Delete a path, completely, and recursively.

    This is intentionally inserted as an additional function and not a member
    of the :class:`Path` in order make the deletion more explicit and to avoid
    any form of accidental deleting. This function will not raise an error if
    the file deletion fails.

    :param path: The path to be deleted
    :raises ValueError: if `path` does not refer to an existing file or
        directory
    :raises TypeError: if `path` is not a string

    >>> from tempfile import mkstemp, mkdtemp
    >>> from os import close as osxclose

    >>> (h, tf) = mkstemp()
    >>> isfile(tf)
    True
    >>> delete_path(tf)
    >>> isfile(tf)
    False

    >>> try:
    ...     delete_path(tf)
    ... except ValueError as ve:
    ...     print(str(ve).endswith("is neither file nor directory."))
    True

    >>> td = mkdtemp()
    >>> isdir(td)
    True
    >>> delete_path(td)
    >>> isdir(td)
    False

    >>> try:
    ...     delete_path(tf)
    ... except ValueError as ve:
    ...     print(str(ve).endswith("is neither file nor directory."))
    True
    """
    p: Final[Path] = Path(path)
    if isfile(p):
        osremove(p)
    elif isdir(p):
        rmtree(p, ignore_errors=True)
    else:
        raise ValueError(f"{path!r} is neither file nor directory.")
