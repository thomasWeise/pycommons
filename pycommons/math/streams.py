"""
Tools for numerical data aggregation over streams.

This module provides tools that can be used to aggregate data over streams of
numerical data.
Such tools should extend the class
:class:`~pycommons.math.streams.StreamAggregate`, which provides the tools to
:meth:`~pycommons.math.streams.StreamAggregate.add` data to the aggregation
procedure as well as to include whole sequence of data (via
:meth:`~pycommons.math.streams.StreamAggregate.update`) or to
:meth:`~pycommons.math.streams.StreamAggregate.reset` the computation.
It is recommended that subclasses should implement a method `result`
returning the current result.

The class :class:`~pycommons.math.streams.StreamSum` is such a subclass of
:class:`~pycommons.math.streams.StreamAggregate`. It provides a running sum of
values over a stream of data, using a Kahan summation algorithm of the second
order. Its method
:meth:`~pycommons.math.streams.StreamSum.result` returns the current running
sum value.
"""

from math import isfinite
from typing import Callable, Final, Iterable

from pycommons.math.int_math import __DBL_INT_LIMIT_N_F as _DILNF
from pycommons.math.int_math import __DBL_INT_LIMIT_P_F as _DILPF
from pycommons.math.int_math import try_int_add
from pycommons.types import type_error


class StreamAggregate:
    """
    The base class for stream aggregates.

    This class provides a basic API for stream data aggregation.
    It is implemented by :class:`StreamSum`.
    """

    def reset(self) -> None:
        """
        Reset this stream aggregate.

        :raises NotImplementedError: because it is an abstract method

        >>> ag = StreamAggregate()
        >>> try:
        ...     ag.reset()
        ... except NotImplementedError:
        ...     print("not implemented")
        not implemented
        """
        raise NotImplementedError

    def add(self, value: int | float) -> None:
        """
        Add a value to the aggregate.

        :param value: the value to aggregate

        :raises NotImplementedError: because it is an abstract method

        >>> ag = StreamAggregate()
        >>> try:
        ...     ag.add(1)
        ... except NotImplementedError:
        ...     print("not implemented")
        not implemented
        """
        raise NotImplementedError

    def update(self, data: Iterable[int | float | None]) -> None:
        """
        Perform a stream update.

        This function adds all the data to the stream while skipping `None`
        values.

        :param data: the data, i.e., a stream of values. `None` values are
            skipped

        >>> ag = StreamAggregate()
        >>> ag.add = lambda d: print(str(d))
        >>> ag.update((1, 2, 3))
        1
        2
        3
        >>> ag.update((1, None, 3))
        1
        3
        """
        ad: Final[Callable[[int | float], None]] = self.add  # fast calls!
        for v in data:
            if v is not None:
                ad(v)


class StreamSum(StreamAggregate):
    """
    The second-order Kahan-Babuška-Neumaier-Summation by Klein.

    [1] A. Klein. A Generalized Kahan-Babuška-Summation-Algorithm.
        Computing 76:279-293. 2006. doi:10.1007/s00607-005-0139-x

    >>> stream_sum = StreamSum()
    >>> stream_sum.update([1e18, 1, 1e36, -1e36, -1e18])
    >>> stream_sum.result()
    1
    >>> stream_sum.reset()
    >>> stream_sum.update([1e18, 1, 1e36, -1e36, -1e18])
    >>> stream_sum.result()
    1
    >>> stream_sum.reset()
    >>> stream_sum.update([1e18, 1, 1e36, None, -1e36, -1e18])
    >>> stream_sum.result()
    1
    """

    def __init__(self) -> None:
        """Create the summation object."""
        #: the running integer sum
        self.__i_sum: int = 0
        #: the running sum, an internal variable invisible from outside
        self.__sum: float | int = 0
        #: the first correction term, another internal variable
        self.__cs: float | int = 0
        #: the second correction term, another internal variable
        self.__ccs: float | int = 0
        #: did we record a value?
        self.__has_value: bool = False

    def reset(self) -> None:
        """Reset this sum."""
        self.__sum = 0
        self.__cs = 0
        self.__ccs = 0
        self.__i_sum = 0
        self.__has_value = False

    def add(self, value: int | float) -> None:
        """
        Add a value to the sum.

        :param value: the value to add

        >>> ss = StreamSum()
        >>> print(ss.result())
        None
        >>> ss.add(1)
        >>> ss.result()
        1
        >>> ss.add(2.0)
        >>> ss.result()
        3
        >>> ss.add(1e43)
        >>> ss.result()
        1e+43
        >>> ss.add(-1e43)
        >>> ss.result()
        3
        >>> ss.reset()
        >>> print(ss.result())
        None

        >>> try:
        ...     ss.add("x")
        ... except TypeError as te:
        ...     print(te)
        value should be an instance of any in {float, int} but is str, \
namely 'x'.

        >>> from math import inf
        >>> try:
        ...     ss.add(inf)
        ... except ValueError as ve:
        ...     print(ve)
        Value must be finite, but is inf.
        """
        self.__has_value = True
        if isinstance(value, int):
            self.__i_sum += value
            return
        if not isinstance(value, float):
            raise type_error(value, "value", (float, int))
        if not isfinite(value):
            raise ValueError(f"Value must be finite, but is {value}.")
        if _DILNF <= value <= _DILPF:
            iv: Final[int] = int(value)
            if value == iv:
                self.__i_sum += iv
                return
        s: int | float = self.__sum  # Get the current running sum.
        t: int | float = s + value   # Compute the new sum value.
        c: int | float = (((s - t) + value) if abs(s) >= abs(value)
                          else ((value - t) + s))  # The Neumaier tweak.
        self.__sum = t  # Store the new sum value.
        cs: int | float = self.__cs  # the current 1st-order correction
        t = cs + c  # Compute the new first-order correction term.
        cc: int | float = (((cs - t) + c) if abs(cs) >= abs(c)
                           else ((c - t) + cs))  # 2nd Neumaier tweak.
        self.__cs = t  # Store the updated first-order correction term.
        self.__ccs += cc  # Update the second-order correction.

    def add_sum(self, ss: "StreamSum") -> None:
        """
        Add another stream sum to this one.

        :param ss: the other stream sum

        >>> ss1 = StreamSum()
        >>> ss1.update((1, 1e20))
        >>> ss2 = StreamSum()
        >>> ss2.update((5, -1e20))
        >>> ss1.add_sum(ss2)
        >>> ss1.result()
        6

        >>> try:
        ...     ss1.add_sum("x")
        ... except TypeError as te:
        ...     print(str(te)[:31])
        other sum should be an instance
        """
        if not isinstance(ss, StreamSum):
            raise type_error(ss, "other sum", StreamSum)
        if ss.__has_value:
            self.add(ss.__i_sum)
            self.add(ss.__sum)
            self.add(ss.__cs)
            self.add(ss.__ccs)

    def result(self) -> int | float | None:
        """
        Get the current result of the summation.

        :return: the current result of the summation, or `None` if no value
            was added yet
        """
        return try_int_add(
            self.__i_sum, self.__sum + self.__cs + self.__ccs) \
            if self.__has_value else None
