"""
Functionality to log the current system state.

Here we provide a small program that can be executed concurrently with other
activities and that logs information about the system state. This may be
useful when running some computationally heavy experiments to find potential
problems.
"""


from argparse import ArgumentParser
from contextlib import AbstractContextManager, nullcontext, suppress
from time import sleep
from typing import Any, Callable, Final, Iterable

from psutil import (  # type: ignore
    cpu_times,  # type: ignore
    cpu_times_percent,  # type: ignore
    disk_partitions,  # type: ignore
    disk_usage,  # type: ignore
    sensors_fans,  # type: ignore
    sensors_temperatures,  # type: ignore
    virtual_memory,  # type: ignore
)

from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.types import check_int_range, type_error


def __attrs_to_str(prefix: str, data: Any, fields: Iterable[str],
                   collector: Callable[[str], Any]) -> None:
    """
    Convert the fields of a named tuple to a string.

    :param prefix: the line prefix
    :param data: the named tuple
    :param fields: the fields
    :param collector: the collector receiving the final string, if any

    >>> __attrs_to_str("", None, (), print)

    >>> __attrs_to_str("", "a", ("__class__", ), print)
    __class__=<class 'str'>

    >>> __attrs_to_str("prefix", "a", ("__class__", ), print)
    prefix: __class__=<class 'str'>
    """
    if data is not None:
        text: str = str.strip(prefix)
        min_len: Final[int] = str.__len__(text)
        for attr in fields:
            if hasattr(data, attr):
                val: Any = getattr(data, attr)
                if val is not None:
                    sep: str = ", " if str.__len__(text) > min_len else (
                        "" if min_len <= 0 else ": ")
                    text = f"{text}{sep}{attr}={val!r}"
        if str.__len__(text) > min_len:
            collector(text)


def __struct_to_str(prefix: str, data: Any, fields: Iterable[str],
                    collector: Callable[[str], Any]) -> None:
    """
    Convert a structured system info record to strings.

    :param prefix: the prefix to use
    :param data: the data record
    :param fields: the fields on the per-row basis
    :param collector: the collector to receive the strings

    >>> __struct_to_str("", None, (), print)
    """
    if isinstance(data, dict):
        prefix = str.strip(prefix)
        for key in data:
            if isinstance(key, str):
                row: Any = data.get(key, None)
                if isinstance(row, Iterable):
                    for element in row:
                        if element is not None:
                            kname: Any = str.strip(key)
                            name: str = kname if str.__len__(prefix) <= 0 \
                                else f"{prefix} {kname}"
                            if hasattr(element, "label"):
                                label: Any = getattr(element, "label")
                                if isinstance(label, str) and (
                                        str.__len__(label) > 0):
                                    name = f"{name} {str.strip(label)}"
                            __attrs_to_str(name, element, fields, collector)


def system_state(skip_cpu_stats: bool = False) -> str:
    """
    Get a single string with the current state of the system.

    :param skip_cpu_stats: should we skip the CPU stats? This makes sense
        when this function is invoked for the first time
    :return: a string with the state of the system

    >>> s = system_state(True)
    >>> s.startswith("Current System State")
    True

    >>> s = system_state(False)
    >>> s.startswith("Current System State")
    True

    >>> try:
    ...     system_state(None)
    ... except TypeError as te:
    ...     print(te)
    skip_cpu_stats should be an instance of bool but is None.
    """
    if not isinstance(skip_cpu_stats, bool):
        raise type_error(skip_cpu_stats, "skip_cpu_stats", bool)

    lines: list[str] = ["Current System State"]
    add: Callable[[str], Any] = lines.append

    with suppress(BaseException):
        __attrs_to_str("cpu_times", cpu_times(), ("user", "system", "idle"),
                       add)

    if not skip_cpu_stats:
        with suppress(BaseException):
            cpup: Any = cpu_times_percent(percpu=True)
            if isinstance(cpup, Iterable):
                for i, z in enumerate(cpup):
                    __attrs_to_str(f"cpu_{i}_usage", z, (
                        "user", "system", "idle"), add)

    with suppress(BaseException):
        __attrs_to_str("memory", virtual_memory(), (
            "total", "available", "percent", "used", "free"), add)

    with suppress(BaseException):
        dps: Any = disk_partitions(False)
        if isinstance(dps, Iterable):
            for disk in dps:
                if not hasattr(disk, "mountpoint"):
                    continue
                mp = getattr(disk, "mountpoint")
                if not isinstance(mp, str):
                    continue
                if str.startswith(mp, ("/snap/", "/var/snap/")):
                    continue
                with suppress(BaseException):
                    __attrs_to_str(f"disk '{mp}'", disk_usage(mp), (
                        "total", "used", "free", "percent"), add)

    with suppress(BaseException):
        __struct_to_str("temperature", sensors_temperatures(False), (
            "current", "high", "critical"), add)

    with suppress(BaseException):
        __struct_to_str("fan speed", sensors_fans(), ("current", ), add)

    return "\n".join(lines)


def log_system_state(interval_seconds: int = 300,
                     should_stop: Callable[[], bool] = lambda: False,
                     lock: AbstractContextManager = nullcontext()) -> None:
    r"""
    Log the system state periodically to the stdout.

    This function allows for periodic logging of the system state to the
    standard output. This can be launched as a program running besides an
    experiment in order to help tracking potential problems. Let's say that
    your experiment or whatever program crashes for unclear reasons. Why did
    it crash? We don't know. Maybe it crashed because it ran out of memory.
    Maybe it ran out of disk space? Maybe not? Who knows. If you let this
    function here run concurrently to your program and pipe its output to a
    log file, then at least you will be able to see if the system slowly runs
    out of memory, disk space, or if the CPU gets too hot, or something. Or,
    at least, you can rule out that this is not the case.

    :param interval_seconds: the interval seconds
    :param should_stop: a function telling the logger when it should stop
    :param lock: a shared lock for the console access

    # Example:
    >>> from contextlib import redirect_stdout
    >>> from io import StringIO
    >>> sio = StringIO()

    >>> def __three(lst=[1, 2, 3, 4, 5, 6]) -> bool:
    ...     if list.__len__(lst) > 0:
    ...         del lst[-1]
    ...         return False
    ...     return True

    >>> with redirect_stdout(sio):
    ...     log_system_state(1, __three)
    >>> v = sio.getvalue()

    >>> i = v.index("Current System State")
    >>> i > 0
    True

    >>> i = v.index("Current System State", i + 1)
    >>> i > 0
    True

    >>> i = v.index("Current System State", i + 1)
    >>> i > 0
    True

    >>> i = v.find("Current System State", i + 1)
    >>> i == -1
    True

    >>> try:
    ...     log_system_state(1, lock=None)
    ... except TypeError as te:
    ...     print(str(te)[0:60])
    lock should be an instance of contextlib.AbstractContextMana

    >>> try:
    ...     log_system_state(1, should_stop=None)
    ... except TypeError as te:
    ...     print(te)
    should_stop should be a callable but is None.
    """
    interval_seconds = check_int_range(
        interval_seconds, "interval_seconds", 1, 1_000_000_000)
    if not callable(should_stop):
        raise type_error(should_stop, "should_stop", call=True)
    if not isinstance(lock, AbstractContextManager):
        raise type_error(lock, "lock", AbstractContextManager)

    with suppress(BaseException):
        cpu_times_percent(percpu=True)

    skip_cpu_stats: bool = True
    while not should_stop():
        logger(system_state(skip_cpu_stats), lock=lock, do_print=True)
        skip_cpu_stats = False
        if should_stop():
            return
        sleep(interval_seconds)


# Run documentation generation process if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Print the System State",
        "A program printing the state of the system in fixed intervals.")
    parser.add_argument(
        "--interval", nargs="?", type=int, default=300,
        help="the interval between printing the state in seconds")
    args = parser.parse_args()
    log_system_state(args.interval)
