"""Get information about how this process was called."""
from contextlib import suppress
from os import environ, getppid
from os.path import basename
from traceback import extract_stack
from typing import Final, cast

from psutil import Process  # type: ignore


def is_ci_run() -> bool:
    """
    Check if the program runs in a continuous integration environment.

    Right now, only GitHub actions are recognized. Other CI tools are
    currently not supported.

    :returns: `True` if this process is executed as part of, e.g., a GitHub
        action, `False` otherwise.

    >>> isinstance(is_ci_run(), bool)
    True
    """
    return any(k in environ for k in (
        "GITHUB_ACTION", "GITHUB_ACTOR", "GITHUB_ENV", "GITHUB_JOB",
        "GITHUB_RUN_ID", "GITHUB_WORKFLOW", "GITHUB_WORKSPACE"))


def is_build() -> bool:
    """
    Check if the program was run inside a build.

    This function is `True` if the process is running inside a `make`  build
    or if :func:`is_ci_run` is `True`.

    :returns: `True` if this process is executed as part of a `make` build
        process, `False` otherwise.

    >>> isinstance(is_build(), bool)
    True
    >>> ns = lambda prc: False if prc is None else (  # noqa: E731
    ...     "make" in prc.name() or ns(prc.parent()))
    >>> is_build() == ns(Process(getppid()))
    True
    """
    obj: Final[object] = is_build
    key: Final[str] = "_value"
    if hasattr(obj, key):
        return cast(bool, getattr(obj, key))

    ret: bool = is_ci_run()

    if not ret:
        with suppress(Exception):
            process: Process = Process(getppid())
            while process is not None:
                name = process.cmdline()[0]
                if not isinstance(name, str):
                    break
                name = basename(name)
                if (str.__eq__(name, "make")) or (
                        str.startswith(name, "make.")):
                    ret = True
                    break
                process = process.parent()

    setattr(obj, key, ret)
    return ret


def is_doc_test() -> bool:
    """
    Check if this process was invoked by a unit doctest.

    :return: `True` if this function was called by a unit doctest,
        `False` otherwise

    >>> is_doc_test()
    True
    """
    return any(t.filename.endswith(("docrunner.py", "doctest.py"))
               for t in extract_stack())
