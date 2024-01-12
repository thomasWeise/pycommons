"""
Automatically deleted temporary files and directories.

This module provides two classes, :class:`~TempDir` for temporary directories
and :class:`~TempFile` for temporary files. Both of them implement the
`ContextManager` interface and will be deleted when going out of scope.
"""
import os
from contextlib import AbstractContextManager
from shutil import rmtree
from tempfile import mkdtemp, mkstemp
from typing import Final

from pycommons.io.path import Path
from pycommons.types import type_error


class TempDir(Path, AbstractContextManager):
    """
    A scoped temporary directory to be used in a 'with' block.

    The directory and everything in it will be deleted upon exiting the
    'with' block.
    """

    #: is the directory open?
    __is_open: bool

    def __new__(cls, value):  # noqa
        """
        Construct the object.

        :param value: the string value
        """
        ret = super().__new__(cls, value)
        ret.enforce_dir()
        ret.__is_open = True
        return ret

    @staticmethod
    def create(directory: str | None = None) -> "TempDir":
        """
        Create the temporary directory.

        :param directory: an optional root directory
        :raises TypeError: if `directory` is not `None` but also no `str`

        >>> with TempDir.create() as td:
        ...     pass
        >>> try:
        ...     with TempDir.create(1):
        ...         pass
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is int, namely '1'.
        >>> from os.path import dirname
        >>> with TempDir.create(dirname(__file__)) as td:
        ...     pass
        """
        return TempDir(mkdtemp(
            dir=None if directory is None else Path.directory(directory)))

    def __enter__(self) -> "TempDir":
        """
        Nothing, just exists for `with`.

        >>> te = TempDir.create()
        >>> with te:
        ...     pass
        >>> try:
        ...     with te:  # does not work, already closed
        ...         pass
        ... except ValueError as ve:
        ...     print(str(ve)[:19])
        Temporary directory
        """
        if not self.__is_open:
            raise ValueError(f"Temporary directory {self!r} already closed.")
        return self

    def __exit__(self, exception_type, _, __) -> bool:
        """
        Delete the temporary directory and everything in it.

        :param exception_type: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it

        >>> with TempDir.create() as td:
        ...     f = td.resolve_inside("a")
        ...     f.ensure_file_exists()  # False, file did not yet exist
        ...     f.enforce_file()
        ...     f.is_file()  # True, because it does now
        ...     d = td.resolve_inside("b")
        ...     d.is_dir()   # False, does not exist
        ...     d.ensure_dir_exists()
        ...     d.is_dir()  # True, now it does
        False
        True
        False
        True
        >>> f.is_file()  # False, because it no longer does
        False
        >>> d.is_dir()  # False, because it no longer exists
        False
        """
        opn: Final[bool] = self.__is_open
        self.__is_open = False
        if opn:
            rmtree(self, ignore_errors=True, onerror=None)
        return exception_type is None


class TempFile(Path, AbstractContextManager):
    """
    A scoped temporary file to be used in a 'with' block.

    This file will be deleted upon exiting the 'with' block.
    """

    #: is the directory open?
    __is_open: bool

    def __new__(cls, value):  # noqa
        """
        Construct the object.

        :param value: the string value
        """
        ret = super().__new__(cls, value)
        ret.enforce_file()
        ret.__is_open = True
        return ret

    @staticmethod
    def create(directory: str | None = None,
               prefix: str | None = None,
               suffix: str | None = None) -> "TempFile":
        """
        Create a temporary file that will be deleted when going out of scope.

        :param directory: a root directory or `TempDir` instance
        :param prefix: an optional prefix
        :param suffix: an optional suffix, e.g., `.txt`
        :raises TypeError: if any of the parameters does not fulfill the type
            contract
        :raises ValueError: if the `prefix` or `suffix` are specified, but are
            empty strings, or if `directory` does not identify an existing
            directory although not being `None`

        >>> with TempFile.create() as tf:
        ...     tf.is_file()
        ...     p = Path(tf)
        ...     p.is_file()
        True
        True
        >>> p.is_file()
        False
        >>> try:
        ...     TempFile.create(1)
        ... except TypeError as te:
        ...     print(te)
        path should be an instance of str but is int, namely '1'.
        >>> try:
        ...     TempFile.create("")
        ... except ValueError as ve:
        ...     print(ve)
        Path must not be empty.
        >>> try:
        ...     TempFile.create(None, 1)
        ... except TypeError as te:
        ...     print(te)
        prefix should be an instance of str but is int, namely '1'.
        >>> try:
        ...     TempFile.create(None, None, 1)
        ... except TypeError as te:
        ...     print(te)
        suffix should be an instance of str but is int, namely '1'.
        >>> try:
        ...     TempFile.create(None, "")
        ... except ValueError as ve:
        ...     print(ve)
        Prefix cannot be empty if specified.
        >>> try:
        ...     TempFile.create(None, None, "")
        ... except ValueError as ve:
        ...     print(ve)
        Suffix cannot be empty if specified.
        >>> from os.path import dirname
        >>> bd = Path.directory(dirname(__file__))
        >>> with TempFile.create(bd) as tf:
        ...     bd.enforce_contains(tf)
        ...     bd in tf
        ...     p = Path.file(tf)
        True
        >>> p.is_file()
        False
        >>> from os.path import basename
        >>> with TempFile.create(None, "pre") as tf:
        ...     "pre" in tf
        ...     bd.contains(tf)
        ...     basename(tf).startswith("pre")
        ...     p = Path.file(tf)
        True
        False
        True
        >>> p.is_file()
        False
        >>> with TempFile.create(bd, "pre") as tf:
        ...     "pre" in tf
        ...     bd.contains(tf)
        ...     basename(tf).startswith("pre")
        ...     p = Path.file(tf)
        True
        True
        True
        >>> p.is_file()
        False
        >>> with TempFile.create(bd, None, "suf") as tf:
        ...     "suf" in tf
        ...     bd.contains(tf)
        ...     tf.endswith("suf")
        ...     p = Path.file(tf)
        True
        True
        True
        >>> p.is_file()
        False
        >>> with TempFile.create(None, None, "suf") as tf:
        ...     "suf" in tf
        ...     tf.endswith("suf")
        ...     bd.contains(tf)
        ...     p = Path.file(tf)
        True
        True
        False
        >>> p.is_file()
        False
        >>> with TempFile.create(None, "pref", "suf") as tf:
        ...     tf.index("pref") < tf.index("suf")
        ...     tf.endswith("suf")
        ...     basename(tf).startswith("pref")
        ...     bd.contains(tf)
        ...     p = Path.file(tf)
        True
        True
        True
        False
        >>> p.is_file()
        False
        >>> with TempFile.create(bd, "pref", "suf") as tf:
        ...     tf.index("pref") < tf.index("suf")
        ...     tf.endswith("suf")
        ...     basename(tf).startswith("pref")
        ...     bd.contains(tf)
        ...     p = Path.file(tf)
        True
        True
        True
        True
        >>> p.is_file()
        False
        """
        if prefix is not None:
            if not isinstance(prefix, str):
                raise type_error(prefix, "prefix", str)
            prefix = prefix.strip()
            if len(prefix) == 0:
                raise ValueError("Prefix cannot be empty if specified.")

        if suffix is not None:
            if not isinstance(suffix, str):
                raise type_error(suffix, "suffix", str)
            suffix = suffix.strip()
            if len(suffix) == 0:
                raise ValueError("Suffix cannot be empty if specified.")

        if directory is not None:
            base_dir = Path.path(directory)
            base_dir.enforce_dir()
        else:
            base_dir = None

        (handle, path) = mkstemp(
            suffix=suffix, prefix=prefix,
            dir=None if base_dir is None else Path.directory(base_dir))
        os.close(handle)
        return TempFile(path)

    def __enter__(self) -> "TempFile":
        """
        Nothing, just exists for `with`.

        >>> tf = TempFile.create()
        >>> with tf:
        ...     pass
        >>> try:
        ...     with tf:  # fails, because already closed
        ...         pass
        ... except ValueError as ve:
        ...     print(str(ve)[:16])
        Temporary file '
        """
        if not self.__is_open:
            raise ValueError(f"Temporary file {self!r} already deleted.")
        return self

    def __exit__(self, exception_type, _, __) -> bool:
        """
        Delete the temporary file.

        :param exception_type: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it

        >>> with TempFile.create() as tf:
        ...     p = Path.file(tf)
        ...     p.is_file()
        True
        >>> p.is_file()
        False
        """
        opn: Final[bool] = self.__is_open
        self.__is_open = False
        if opn:
            os.remove(self)
        return exception_type is None
