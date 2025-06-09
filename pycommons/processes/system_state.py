"""
Functionality to log the current system state.

Here we provide a small program that can be executed concurrently with other
activities and that logs information about the system state. This may be
useful when running some computationally heavy experiments to find potential
problems.
"""


import datetime
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
from pycommons.io.csv import CSV_SEPARATOR, SCOPE_SEPARATOR
from pycommons.math.int_math import try_int
from pycommons.strings.chars import WHITESPACE_OR_NEWLINE
from pycommons.strings.tools import replace_str
from pycommons.types import check_int_range, type_error

#: the "now" function
__DTN: Final[Callable[[], datetime.datetime]] = datetime.datetime.now

#: the characters to replace with the `SCOPE_SEPARATOR`
__REPL: Final[tuple[str, ...]] = tuple(
    f"/\\{{}}{WHITESPACE_OR_NEWLINE}{CSV_SEPARATOR}")

#: the double scope
__DOUBLE_SCOPE: Final[str] = f"{SCOPE_SEPARATOR}{SCOPE_SEPARATOR}"


def __fix_key(key: Any) -> str | None:
    """
    Fix a key for usage.

    :param key: the key
    :returns: the key string

    >>> print(__fix_key(None))
    None
    >>> print(__fix_key(1))
    None
    >>> print(__fix_key(""))
    None
    >>> print(__fix_key(" "))
    None
    >>> print(__fix_key("."))
    None
    >>> print(__fix_key(". ."))
    None
    >>> print(__fix_key("...."))
    None
    >>> __fix_key(".d x")
    'd.x'
    >>> __fix_key(".d ..x")
    'd.x'
    >>> __fix_key(".v yd ..x yxc .")
    'v.yd.x.yxc'
    """
    if not isinstance(key, str):
        return None
    key = str.strip(key)
    if str.__len__(key) <= 0:
        return None
    for ch in __REPL:
        key = str.replace(key, ch, SCOPE_SEPARATOR)
    key = str.strip(replace_str(__DOUBLE_SCOPE, SCOPE_SEPARATOR, key))
    while str.startswith(key, SCOPE_SEPARATOR):
        key = str.strip(key[1:])
    while str.endswith(key, SCOPE_SEPARATOR):
        key = str.strip(key[:-1])
    return None if str.__len__(key) <= 0 else key


def __collect_attrs(prefix: str, data: Any, fields: Iterable[str],
                    collector: Callable[[str, str], Any]) -> None:
    """
    Pass the attributes to a collector.

    :param prefix: the attribute prefix
    :param data: the named tuple
    :param fields: the fields
    :param collector: the collector receiving the attributes

    >>> def __ptr(a: str, b: str) -> None:
    ...     print(f"{a}: {b}")

    >>> __collect_attrs("", None, (), __ptr)

    >>> __collect_attrs("", "a", ("__class__", ), __ptr)
    __class__: <class 'str'>

    >>> __collect_attrs("prefix.", "a", ("__class__", ), __ptr)
    prefix.__class__: <class 'str'>

    >>> __collect_attrs("prefix.", "a", ("__class__", ), __ptr)
    prefix.__class__: <class 'str'>

    >>> __collect_attrs("prefix.", "a", ("__class__", "__class__"), __ptr)
    prefix.__class__: <class 'str'>
    prefix.__class__: <class 'str'>
    """
    if data is None:
        return
    for attr in fields:
        if hasattr(data, attr):
            val: Any = getattr(data, attr)
            if val is not None:
                k: str | None = __fix_key(f"{prefix}{attr}")
                if k is not None:
                    collector(k, repr(val))


def __collect_struct(prefix: str, data: Any, fields: Iterable[str],
                     collector: Callable[[str, str], Any]) -> None:
    """
    Pass a structured info system to a collector.

    :param prefix: the prefix to use
    :param data: the data record
    :param fields: the fields on the per-row basis
    :param collector: the collector to receive the strings

    >>> def __ptr(a: str, b: str) -> None:
    ...     print(f"{a}: {b}")

    >>> __collect_struct("", None, (), __ptr)
    """
    if isinstance(data, dict):
        prefix = str.strip(prefix)
        for key in data:
            if isinstance(key, str):
                row: Any = data.get(key, None)
                if isinstance(row, Iterable):
                    for element in row:
                        if element is not None:
                            name: str = f"{str.strip(key)}."
                            if hasattr(element, "label"):
                                label: Any = getattr(element, "label")
                                if isinstance(label, str):
                                    label = str.strip(label)
                                    if str.__len__(label) > 0:
                                        name = f"{prefix}{name}.{label}."
                            __collect_attrs(name, element, fields, collector)


def collect_system_state(
        collector: Callable[[str, str], Any]) -> None:
    """
    Get a single string with the current state of the system.

    :param collector: the collector to receive the key-value tuples

    >>> def __ptr(a: str, b: str) -> None:
    ...     pass

    >>> s = collect_system_state(__ptr)

    >>> try:
    ...     collect_system_state(None)
    ... except TypeError as te:
    ...     print(te)
    collector should be a callable but is None.
    """
    if not callable(collector):
        raise type_error(collector, "collector", call=True)

    now: Final = __DTN()
    collector("now", repr(try_int(now.timestamp())))
    __collect_attrs("now.", now, (
        "year", "month", "day", "hour", "minute", "second", "microsecond"),
        collector)

    with suppress(BaseException):
        __collect_attrs("cpu_times.", cpu_times(), ("user", "system", "idle"),
                        collector)

    with suppress(BaseException):
        cpup: Any = cpu_times_percent(percpu=True)
        if isinstance(cpup, Iterable):
            for i, z in enumerate(cpup):
                __collect_attrs(f"cpu_{i}_usage.", z, (
                    "user", "system", "idle"), collector)

    with suppress(BaseException):
        __collect_attrs("memory.", virtual_memory(), (
            "total", "available", "percent", "used", "free"), collector)

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
                    __collect_attrs(f"disk.{mp}.", disk_usage(mp), (
                        "total", "used", "free", "percent"), collector)

    with suppress(BaseException):
        __collect_struct("temperature.", sensors_temperatures(False), (
            "current", "high", "critical"), collector)

    with suppress(BaseException):
        __collect_struct("fan speed", sensors_fans(), ("current", ),
                         collector)


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

    The output is presented in CSV format. Therefore, you can pipe it to a
    file and later open it in Excel or whatever. This allows you to draw
    diagrams of the usage of CPUs and memory or the temperature of the CPU
    over time.

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
    >>> v = sio.getvalue().splitlines()
    >>> len(v)
    4
    >>> v[0][:20]
    'now;now.year;now.mon'
    >>> i = list.__len__(v[0].split(CSV_SEPARATOR))
    >>> all(list.__len__(vv.split(CSV_SEPARATOR)) == i for vv in v)
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

    keys: Final[list[str]] = []
    collect_system_state(lambda a, _, x=keys.append: x(a))  # type: ignore
    print(CSV_SEPARATOR.join(keys))  # noqa: T201
    current: dict[str, str] = {}

    while not should_stop():
        collect_system_state(current.__setitem__)
        print(CSV_SEPARATOR.join(  # noqa: T201
            current[k] for k in keys if k in current))
        current.clear()
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
