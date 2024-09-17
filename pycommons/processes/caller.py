"""Get information about how this process was called."""
from contextlib import suppress
from os import environ, getpid
from os.path import basename, isfile
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

    This function is `True` if the process is running inside a `make` build
    or if :func:`is_ci_run` is `True` or if the evironment variable
    `BUILD_SCRIPT` is set.

    Since we now need to use virtual environments to install `pip` packages,
    using `make` scripts has become too cumbersome to me. I simply cannot be
    bothered to figure out how to set up a virtual environment `make` script
    wide. Instead, I now use a `bash` script (`make.sh`) in my builds. To
    properly detect this, this script sets the environment variable
    `BUILD_SCRIPT`. In all my `pycommons`-based projects, I will do this from
    now on.

    Basically, if you want to signal that code runs inside a build, you can
    set an environment variable as `export BUILD_SCRIPT="${BASH_SOURCE[0]}"`
    inside your `bash` build script. This will be used as signal by this
    function that we are running inside a build.

    :returns: `True` if this process is executed as part of a build process,
        `False` otherwise.

    >>> isinstance(is_build(), bool)
    True
    """
    obj: Final[object] = is_build
    key: Final[str] = "_value"
    if hasattr(obj, key):
        return cast(bool, getattr(obj, key))

    ret: bool = ("BUILD_SCRIPT" in environ) or is_ci_run()

    if not ret:
        with suppress(Exception):
            process: Process = Process(getpid())
            while process is not None:
                process = process.parent()
                name: str = process.cmdline()[0]
                if not isinstance(name, str):
                    continue
                if not isfile(name):
                    continue
                name = basename(name)
                if (str.__eq__(name, "make")) or (
                        str.startswith(name, "make.")):
                    ret = True
                    break

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
