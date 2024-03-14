"""
Some utilities for dealing with python.

>>> PYTHON_INTERPRETER.is_file()
True

>>> PYTHON_INTERPRETER_SHORT
'python3'

>>> len(__BASE_PATHS) > 0
True
>>> all((isinstance(f, Path) for f in __BASE_PATHS))
True
>>> all((len(__BASE_PATHS[i]) >= len(__BASE_PATHS[i + 1])
...      for i in range(len(__BASE_PATHS) - 1)))
True
"""

import os.path
import subprocess  # nosec
import sys
from typing import Callable, Final, cast

from pycommons.io.path import Path, file_path

#: the Python interpreter used to launch this program
PYTHON_INTERPRETER: Final[Path] = file_path(sys.executable)


def __get_python_interpreter_short() -> str:
    """
    Get the python interpreter.

    :returns: the fully-qualified path
    """
    inter: Final[Path] = PYTHON_INTERPRETER
    inter_version: str
    try:
        # noqa # nosemgrep
        retval = subprocess.run(  # nosec # noqa
            args=(inter, "--version"), check=True,  # nosec # noqa
            text=True, timeout=10, capture_output=True)  # nosec # noqa
        inter_version = retval.stdout
        del retval
    except subprocess.SubprocessError as se:
        raise ValueError(f"Interpreter {inter!r} is invalid?") from se
    if (str.__len__(inter_version) <= 0) or (
            not inter_version.startswith("Python 3.")):
        raise ValueError(f"Interpreter {inter!r} has no version?")

    def __check_is_python(s: str, __c=inter_version) -> bool:
        """Check whether a command results in the same Python interpreter."""
        try:
            # noqa # nosemgrep
            rv = subprocess.run(  # nosec # noqa
                args=(s, "--version"), check=True, text=True,  # nosec # noqa
                timeout=10, capture_output=True)  # nosec # noqa
        except subprocess.SubprocessError:
            return False
        return rv.stdout == __c

    # check if we can just use the interpreter basename without the full path
    # this should usually work
    bn: Final[str] = inter.basename()
    if not __check_is_python(bn):
        return inter

    # if the interpreter is something like "python3.10", then maybe "python3"
    # works, too?
    if bn.startswith("python3."):
        bn2: Final[str] = bn[:7]
        interp2: Final[str] = os.path.join(inter.up(), bn2)
        if (os.path.exists(interp2) and os.path.isfile(interp2) and (
                file_path(interp2) == inter)) or __check_is_python(bn2):
            return bn2
    return bn


#: The python interpreter in short form.
PYTHON_INTERPRETER_SHORT: Final[str] = __get_python_interpreter_short()
del __get_python_interpreter_short


#: the base paths in which
__BASE_PATHS: Final[tuple[Path, ...]] = tuple(sorted((p for p in {
    Path(d) for d in sys.path} if p.is_dir()),
    key=cast(Callable[[Path], int], str.__len__), reverse=True))


def python_command(
        file: str, use_short_interpreter: bool = True) -> list[str]:
    """
    Get a python command that could be used to interpret the given file.

    This function tries to detect whether `file` identifies a Python module
    of an installed package, in which case it will issue a `-m` flag in the
    resulting command, or whether it is some other script, in which it will
    just return a normal interpreter invocation.

    :param file: the python script
    :param use_short_interpreter: use the short interpreter path, for
        reabability and maybe portablity, or the full path?
    :return: a list that can be passed to the shell to run that program, see,
        e.g., :class:`pycommons.processes.shell.Command`.

    >>> python_command(os.__file__)
    ['python3', '-m', 'os']
    >>> python_command(__file__)
    ['python3', '-m', 'pycommons.processes.python']
    >>> from tempfile import mkstemp
    >>> from os import remove as osremovex
    >>> from os import close as osclosex
    >>> h, p = mkstemp(text=True)
    >>> osclosex(h)
    >>> python_command(p) == [PYTHON_INTERPRETER_SHORT, p]
    True
    >>> python_command(p, False) == [PYTHON_INTERPRETER, p]
    True
    >>> osremovex(p)

    >>> h, p = mkstemp(dir=file_path(__file__).up(), text=True)
    >>> osclosex(h)
    >>> python_command(p) == [PYTHON_INTERPRETER_SHORT, p]
    True
    >>> python_command(p, False) == [PYTHON_INTERPRETER, p]
    True
    >>> osremovex(p)

    >>> the_pack = file_path(__file__).up()
    >>> h, p = mkstemp(dir=the_pack,
    ...                suffix=".py", text=True)
    >>> osclosex(h)
    >>> the_str = p[len(the_pack.up(2)) + 1:-3].replace(os.sep, '.')
    >>> python_command(p) == [PYTHON_INTERPRETER_SHORT, "-m", the_str]
    True
    >>> python_command(p, False) == [PYTHON_INTERPRETER, "-m", the_str]
    True
    >>> osremovex(p)
    """
    # first, get the real path to the module
    module: str = file_path(file)
    start: int = 0
    is_module: bool = False  # is this is a module of an installed package?

    for bp in __BASE_PATHS:
        if bp.contains(module):
            start += len(bp) + 1
            is_module = True
            break

    end: int = len(module)
    if is_module:
        if module.endswith(".py"):
            end -= 3
        else:
            is_module = False

    interpreter: Final[str] = PYTHON_INTERPRETER_SHORT \
        if use_short_interpreter else PYTHON_INTERPRETER
    if is_module:
        return [interpreter, "-m", module[start:end].replace(os.sep, ".")]
    return [interpreter, module]
