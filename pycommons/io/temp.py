"""
Automatically deleted temporary files and directories.

This module provides two classes, :func:`temp_dir` for temporary directories
and :func:`temp_file` for temporary files. Both of them implement the
:class:`typing.ContextManager` protocol and will be deleted when going out
of scope.
"""
from os import close as osclose
from tempfile import mkdtemp, mkstemp
from typing import Final

from pycommons.io.path import Path, delete_path, directory_path


class TempPath(Path):
    """A path to a temp file or directory for use in a `with` statement."""

    #: is the directory or file open?
    __is_open: bool

    def __new__(cls, value: str):  # noqa
        """
        Construct the temporary path.

        :param value: the string value of the path
        """
        ret = super().__new__(cls, value)
        ret.__is_open = True
        return ret

    def __enter__(self) -> "TempPath":
        """
        Nothing, just exists for `with`.

        >>> te = temp_dir()
        >>> with te:
        ...     pass
        >>> try:
        ...     with te:  # does not work, already closed
        ...         pass
        ... except ValueError as ve:
        ...     print(str(ve)[:14])
        Temporary path
        """
        if not self.__is_open:
            raise ValueError(f"Temporary path {self!r} already closed.")
        return self

    def __exit__(self, exception_type, _, __) -> bool:
        """
        Delete the temporary directory and everything in it.

        :param exception_type: ignored
        :returns: `True` to suppress an exception, `False` to rethrow it

        >>> with temp_dir() as td:
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
            delete_path(self)
        return exception_type is None


def temp_dir(directory: str | None = None) -> TempPath:
    """
    Create the temporary directory.

    :param directory: an optional root directory
    :raises TypeError: if `directory` is not `None` but also no `str`

    >>> with temp_dir() as td:
    ...     pass
    >>> try:
    ...     with temp_dir(1):
    ...         pass
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'
    >>> from os.path import dirname
    >>> with temp_dir(dirname(__file__)) as td:
    ...     pass
    """
    return TempPath(mkdtemp(
        dir=None if directory is None else directory_path(directory)))


def temp_file(directory: str | None = None,
              prefix: str | None = None,
              suffix: str | None = None) -> TempPath:
    r"""
    Create a temporary file that will be deleted when going out of scope.

    :param directory: a root directory or `TempDir` instance
    :param prefix: an optional prefix
    :param suffix: an optional suffix, e.g., `.txt`
    :raises TypeError: if any of the parameters does not fulfill the type
        contract
    :raises ValueError: if the `prefix` or `suffix` are specified, but are
        empty strings, or if `directory` does not identify an existing
        directory although not being `None`

    >>> with temp_file() as tf:
    ...     tf.is_file()
    ...     p = Path(tf)
    ...     p.is_file()
    True
    True
    >>> p.is_file()
    False

    >>> try:
    ...     temp_file(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     temp_file("")
    ... except ValueError as ve:
    ...     print(ve)
    Path must not be empty.

    >>> try:
    ...     temp_file(None, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     temp_file(None, None, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     temp_file(None, "")
    ... except ValueError as ve:
    ...     print(ve)
    Stripped prefix cannot be empty if specified.

    >>> try:
    ...     temp_file(None, None, "")
    ... except ValueError as ve:
    ...     print(ve)
    Stripped suffix cannot be empty if specified.

    >>> try:
    ...     temp_file(None, None, "bla.")
    ... except ValueError as ve:
    ...     print(ve)
    Stripped suffix must not end with '.', but 'bla.' does.

    >>> try:
    ...     temp_file(None, None, "bl/a")
    ... except ValueError as ve:
    ...     print(ve)
    Suffix must contain neither '/' nor '\', but 'bl/a' does.

    >>> try:
    ...     temp_file(None, None, "b\\la")
    ... except ValueError as ve:
    ...     print(ve)
    Suffix must contain neither '/' nor '\', but 'b\\la' does.

    >>> try:
    ...     temp_file(None, "bl/a", None)
    ... except ValueError as ve:
    ...     print(ve)
    Prefix must contain neither '/' nor '\', but 'bl/a' does.

    >>> try:
    ...     temp_file(None, "b\\la", None)
    ... except ValueError as ve:
    ...     print(ve)
    Prefix must contain neither '/' nor '\', but 'b\\la' does.

    >>> from os.path import dirname
    >>> from pycommons.io.path import file_path
    >>> bd = directory_path(dirname(__file__))
    >>> with temp_file(bd) as tf:
    ...     bd.enforce_contains(tf)
    ...     bd in tf
    ...     p = file_path(str(f"{tf}"))
    True
    >>> p.is_file()
    False

    >>> from os.path import basename
    >>> with temp_file(None, "pre") as tf:
    ...     "pre" in tf
    ...     bd.contains(tf)
    ...     basename(tf).startswith("pre")
    ...     p = file_path(str(f"{tf}"))
    True
    False
    True
    >>> p.is_file()
    False

    >>> with temp_file(bd, "pre") as tf:
    ...     "pre" in tf
    ...     bd.contains(tf)
    ...     basename(tf).startswith("pre")
    ...     p = file_path(str(f"{tf}"))
    True
    True
    True
    >>> p.is_file()
    False

    >>> with temp_file(bd, None, "suf") as tf:
    ...     "suf" in tf
    ...     bd.contains(tf)
    ...     tf.endswith("suf")
    ...     p = file_path(str(f"{tf}"))
    True
    True
    True
    >>> p.is_file()
    False

    >>> with temp_file(None, None, "suf") as tf:
    ...     "suf" in tf
    ...     tf.endswith("suf")
    ...     bd.contains(tf)
    ...     p = file_path(str(f"{tf}"))
    True
    True
    False
    >>> p.is_file()
    False

    >>> with temp_file(None, "pref", "suf") as tf:
    ...     tf.index("pref") < tf.index("suf")
    ...     tf.endswith("suf")
    ...     basename(tf).startswith("pref")
    ...     bd.contains(tf)
    ...     p = file_path(str(f"{tf}"))
    True
    True
    True
    False
    >>> p.is_file()
    False

    >>> with temp_file(bd, "pref", "suf") as tf:
    ...     tf.index("pref") < tf.index("suf")
    ...     tf.endswith("suf")
    ...     basename(tf).startswith("pref")
    ...     bd.contains(tf)
    ...     p = file_path(str(f"{tf}"))
    True
    True
    True
    True
    >>> p.is_file()
    False
    """
    if prefix is not None:
        prefix = str.strip(prefix)
        if str.__len__(prefix) == 0:
            raise ValueError(
                "Stripped prefix cannot be empty if specified.")
        if ("/" in prefix) or ("\\" in prefix):
            raise ValueError("Prefix must contain neither '/' nor"
                             f" '\\', but {prefix!r} does.")

    if suffix is not None:
        suffix = str.strip(suffix)
        if str.__len__(suffix) == 0:
            raise ValueError(
                "Stripped suffix cannot be empty if specified.")
        if suffix.endswith("."):
            raise ValueError("Stripped suffix must not end "
                             f"with '.', but {suffix!r} does.")
        if ("/" in suffix) or ("\\" in suffix):
            raise ValueError("Suffix must contain neither '/' nor"
                             f" '\\', but {suffix!r} does.")

    if directory is not None:
        base_dir = directory_path(directory)
        base_dir.enforce_dir()
    else:
        base_dir = None

    (handle, path) = mkstemp(
        suffix=suffix, prefix=prefix,
        dir=None if base_dir is None else directory_path(base_dir))
    osclose(handle)
    return TempPath(path)
