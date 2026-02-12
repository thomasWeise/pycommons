"""
Fork a Python interpreter process multiple times.

The use case for this tool is when you have a main script in your Python
program and want to allow a user to launch it multiple times with the sme
parameters.
In this case, she would simply provide the argument `--fork NNN`, where
`NNN` is either the absolute number of times the program should be launched
or a fraction in (0, 1) of the available logical cores to use.

You would use the normal :class:`~argparse.ArgumentParser` in your main
code piece, i.e., do something like
`if __name__ == "__main__":` followed by
`    parser: Final[ArgumentParser] = ...`.

Then, you would invoke `args = fork(parser)`, where :func:`fork` is the
function provided here.
This function will return `None` if it has detected the `--fork` argument.
In that case, it will have launched the process again the appropriate
number of times and waited for its completion already.
If it did not detect the `--fork` argument, it will return the
:class:`~argparse.Namespace` instance with the normal arguments.
Actually, it will do exactly this in the launched copies of the process.

So from the outside, this looks pretty much like the good old `fork`
command on Unix systems.
However, it can do a little bit more.
For each process copy (except the original process), the `args.fork_id`
will hold a unique ID of the forked process.

Also, you can provide the command `--fork-log-dir YYY` to the original
process. In this case, each of the forked processes will not be launched
normally. Instead, its stdout and stderr will be piped into two different
files inside the directory `YYY`. This makes working with experiments, like
in the *moptipy* framework (see <https://thomasweise.github.io/moptipy>)
easier.

The gist is this: Under the hood, this looks as if you can do Unix-style
forks of the Python interpreter. Actually, it launches separate interpreter
processes with the same arguments (plus the `fork_id` parameter and minus
the forking-arguments).

Side note: If you do not provide a logging directory and the number of
processes to launch would be 1, then no forking takes place. This then
just returns the normal arguments as if no forking parameters were provided
at all.
"""
import sys
from argparse import ArgumentParser, Namespace
from math import isfinite
from os import cpu_count, environ, getpid
from platform import node
from typing import Final

from pycommons.io.console import logger
from pycommons.io.path import Path
from pycommons.processes.multishell import multi_execute
from pycommons.processes.python import PYTHON_ENV, PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_FORWARD, Command
from pycommons.processes.shell_to_file import to_files
from pycommons.strings.string_tools import replace_str
from pycommons.types import type_error


def get_cores(use: int | float, n_cpu: int | None = None) -> int | None:
    """
    Compute the number of CPU cores to be used (for forking).

    :param use: the usage number, either a float between 0 and 1 denoting a
        fraction of cores to be used, or the absolute number.
    :param n_cpu: the number of CPU cores available, or `None` if we should
        determine it automatically.
    :return: the number of cores

    >>> get_cores(1)
    1
    >>> get_cores(2)
    2
    >>> get_cores(2.3)
    2
    >>> get_cores(2.6)
    3
    >>> get_cores(0.5, 10)
    5
    >>> get_cores(0.3, 10)
    3
    >>> get_cores(0.5, 16)
    8
    >>> get_cores(0.5, 1)
    1

    >>> 0 < get_cores(0.5) < 10000
    True

    >>> try:
    ...     get_cores("a")
    ... except TypeError as te:
    ...     print(te)
    use should be an instance of any in {float, int} but is str, namely 'a'.

    >>> try:
    ...     get_cores(0.3, "a")
    ... except TypeError as te:
    ...     print(te)
    n_cpu should be an instance of int but is str, namely 'a'.

    >>> try:
    ...     get_cores(-1)
    ... except ValueError as v:
    ...     print(v)
    Invalid value -1 for number of cores to use.
    """
    if not isinstance(use, int | float):
        raise type_error(use, "use", (int, float))
    if (not isfinite(use)) or (use <= 0) or (use > 1000):
        raise ValueError(f"Invalid value {use!r} for number of cores to use.")
    if use < 1:
        if n_cpu is None:
            n_cpu = cpu_count()
            if n_cpu is None:
                return 1
        if not isinstance(n_cpu, int):
            raise type_error(n_cpu, "n_cpu", int)
        if n_cpu < 1:
            raise ValueError(f"Invalid value {n_cpu!r} for n_cpu.")
        return max(1, min(n_cpu - 1, round(use * n_cpu)))
    return round(use)


def fork(parser: ArgumentParser) -> Namespace | None:
    """
    Launch this Python process multiple times if requested to.

    If the user provided an argument `--fork NNN`, where `NNN` is either an
    absolute number of processes to launch or a fraction in (0, 1) of logical
    CPU cores to use, then this function will invoke the interpreter the
    corresponding number of times with exactly the same command line arguments
    except the forking parameters.

    You can provide an argument `--fork-log-dir DDD`, where `DDD` is a
    directory. If you do this, then the stdout and stderr of each launched
    process are piped into files inside this directory.

    If forking is done, then each forked process gets an additional argument
    `fork_id` with a unique identifier.

    If no forking arguments are provided, of if we would fork just 1 process
    without logging directory, then no forking is done.
    In this case, this routine just returns the :class:`~argparse.Namespace`
    instance with the command line arguments.
    If this actually already is a forked process, then, too, the
    :class:`~argparse.Namespace` instance with the arguments (plus the
    `fork_id`) is returned.
    If this is the root process from which the forks were started, then `None`
    is returned. In that case, the function returns after all sub-processes
    are completed.

    :param parser: the root argument parser
    :return: `None` if the argument parser contained forking arguments and
        the same process was forked multiple times, otherwise the
        :class:`~argparse.Namespace` with the arguments.
    """
    if not isinstance(parser, ArgumentParser):
        raise type_error(parser, "parser", ArgumentParser)
    arg_fork: Final[str] = "--fork"
    arg_log_dir: Final[str] = f"{arg_fork}-log-dir"
    arg_fork_id: Final[str] = f"{arg_fork}-id"
    parser.add_argument(
        arg_fork, nargs="?", type=float,
        help=("invoke this process multiple times in parallel. --fork can "
              "either be an absolute number of processes to launch or a "
              "fraction in (0, 1) of the available logical CPU cores."))
    parser.add_argument(arg_log_dir, nargs="?", type=Path)
    parser.add_argument(arg_fork_id, nargs="?", type=int)
    args: Namespace = parser.parse_args()

    if args.fork is None:
        return args
    if args.fork_id is not None:
        raise ValueError("Cannot recursively fork.")

    # Get number of processes.
    try:
        nfork: int = get_cores(args.fork)
    except ValueError as ve:
        raise ValueError(f"Invalid value {args.fork} for {arg_fork}.") from ve

    ld: Path | None = args.fork_log_dir
    if nfork <= 1:
        if ld is None:
            logger("No need to fork: There would be just 1 process "
                   "and no log directory.")
            return args
        nfork = 1

    msg: str = f"Forking {nfork} processes"
    if ld is None:
        msg = f"{msg} without specific log directory."
    else:
        msg = f"{msg} with log directory {ld!r}."
    logger(msg)

    # creating and cleaning up arguments
    fork_args: list[str] = list(sys.argv)
    i: int = fork_args.index(arg_fork)
    del fork_args[i]
    del fork_args[i]
    if ld is not None:
        i = fork_args.index(arg_log_dir)
        del fork_args[i]
        del fork_args[i]
    fork_args.insert(0, PYTHON_INTERPRETER)
    fork_args.append(arg_fork_id)

    use_env: Final[dict[str, str]] = dict(environ)
    use_env.update(PYTHON_ENV)

    commands: Final[list[Command]] = []

    for i in range(nfork):
        fork_args.append(str(i))
        commands.append(Command(
            command=fork_args,
            stdout=STREAM_FORWARD,
            stderr=STREAM_FORWARD,
            env=use_env))
        del fork_args[-1]

    if ld is not None:
        ld.ensure_dir_exists()
        prefix = str.lower(f"{node()}_{getpid()}_fork_")
        for ch in "- \\/\t.+*%!#":
            prefix = str.replace(prefix, ch, "_")
        prefix = replace_str("__", "_", prefix)
        for i, cmd in enumerate(commands):
            commands[i] = to_files(
                command=cmd,
                stdout=ld.resolve_inside(f"{prefix}{i}_stdout.txt"),
                stderr=ld.resolve_inside(f"{prefix}{i}_stderr.txt"))

    multi_execute(commands, True)
    return None
