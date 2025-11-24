"""
Tools for computing statistic over a stream.

The classes here try to offer a balance between accuracy and speed.
This is currently an early stage of development.
Things may well change later.

As basic idea, stream sums and statistics try to return integer values as
`int` wherever possible.
"""
from math import inf, sqrt
from typing import Callable, Final, Iterable

from pycommons.math.int_math import try_int
from pycommons.types import type_error


class StreamAggregate:
    """
    The base class for stream aggregates.

    This class provides a basic API for stream data aggregation.
    It is implemented by :class:`StreamSum` and :class:`StreamStats`.
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

    def update(self, data: Iterable[int | float]) -> None:
        """
        Perform a stream update.

        :param data: the data

        >>> ag = StreamAggregate()
        >>> ag.add = lambda d: print(str(d))
        >>> ag.update((1, 2, 3))
        1
        2
        3
        """
        ad: Final[Callable[[int | float], None]] = self.add  # fast calls!
        for v in data:
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
    """

    def __init__(self) -> None:
        """Create the summation object."""
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
        value = try_int(value)  # try to sum ints, check type and non-finite
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
        self.__has_value = True

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
            self.add(ss.__sum)
            self.add(ss.__cs)
            self.add(ss.__ccs)

    def result(self) -> int | float | None:
        """
        Get the current result of the summation.

        :return: the current result of the summation, or `None` if no value
            was added yet
        """
        return try_int(self.__sum + self.__cs + self.__ccs) \
            if self.__has_value else None


class StreamStats(StreamAggregate):
    """
    The stream statistics.

    The stream statistics compute mean and variance of data using Welford's
    algorithm.

    1. Donald E. Knuth (1998). The Art of Computer Programming, volume 2:
       Seminumerical Algorithms, 3rd edn., p. 232. Boston: Addison-Wesley.
    2. B. P. Welford (1962). "Note on a method for calculating corrected sums
       of squares and products". Technometrics 4(3):419-420.

    >>> ss = StreamStats()
    >>> data1 = [4, 7, 13, 16]
    >>> ss.update(data1)
    >>> ss.mean()
    10
    >>> ss.sd()
    5.477225575051661
    >>> sqrt(30)
    5.477225575051661
    >>> ss.n()
    4
    >>> ss.minimum()
    4
    >>> ss.maximum()
    16

    >>> data2 = [1e8 + z for z in data1]
    >>> ss.reset()
    >>> ss.update(data2)
    >>> ss.mean()
    100000010
    >>> ss.sd()
    5.477225575051661
    >>> ss.n()
    4

    >>> data3 = [1e14 + z for z in data1]
    >>> ss.reset()
    >>> ss.update(data3)
    >>> ss.mean()
    100000000000010
    >>> ss.sd()
    5.477225575051661
    >>> ss.n()
    4

    >>> data3 = [z for z in range(1001)]
    >>> ss.reset()
    >>> ss.update(data3)
    >>> ss.mean()
    500
    >>> ss.sd()
    289.10811126635656
    >>> ss.n()
    1001
    """

    def __init__(self) -> None:
        """Initialize the stream statistics."""
        #: the number of samples seen
        self.__n: int = 0
        #: the last mean result
        self.__mean: int | float = 0
        #: the running sum for the variance
        self.__var: int | float = 0
        #: the minimum
        self.__min: int | float = inf
        #: the maximum
        self.__max: int | float = -inf

    def reset(self) -> None:
        """Reset the sample statistics."""
        self.__n = 0
        self.__mean = 0
        self.__var = 0
        self.__min = inf
        self.__max = -inf

    def add(self, value: int | float) -> None:
        """
        Add a value to the statistics.

        :param value: the value
        """
        value = try_int(value)  # try to sum ints, check type and non-finite
        n: Final[int] = self.__n + 1
        self.__n = n
        mean: int | float = self.__mean
        delta: int | float = value - mean
        mean += delta / n
        self.__mean = mean
        self.__var += delta * (value - mean)
        self.__min = min(self.__min, value)
        self.__max = max(self.__max, value)

    def mean(self) -> int | float | None:
        """
        Get the arithmetic mean.

        :return: the arithmetic mean or `None` if no value was added yet

        >>> ss = StreamStats()
        >>> print(ss.mean())
        None
        >>> ss.add(10)
        >>> ss.mean()
        10
        >>> ss.add(20)
        >>> ss.mean()
        15
        >>> ss.add(30)
        >>> ss.mean()
        20
        >>> ss.reset()
        >>> print(ss.mean())
        None
        """
        return None if self.__n <= 0 else try_int(max(self.__min, min(
            self.__max, self.__mean)))

    def sd(self) -> int | float | None:
        """
        Get the standard deviation.

        :return: the standard deviation or `None` if less than two values
            were added yet

        >>> ss = StreamStats()
        >>> print(ss.sd())
        None
        >>> ss.add(5)
        >>> print(ss.sd())
        None
        >>> ss.add(7)
        >>> ss.sd()
        1.4142135623730951
        >>> ss.add(3)
        >>> ss.sd()
        2
        >>> ss.add(7)
        >>> ss.sd()
        1.9148542155126762
        >>> ss.add(10)
        >>> ss.sd()
        2.6076809620810595
        >>> ss.reset()
        >>> print(ss.sd())
        None
        """
        n: Final[int] = self.__n
        return None if n <= 1 else try_int(sqrt(self.__var / (n - 1)))

    def n(self) -> int:
        """
        Get the number of observed samples.

        :return: the number of observed samples

        >>> ss = StreamStats()
        >>> ss.n()
        0
        >>> ss.add(12)
        >>> ss.n()
        1
        >>> ss.add(132)
        >>> ss.n()
        2
        >>> ss.reset()
        >>> ss.n()
        0
        """
        return self.__n

    def minimum(self) -> int | float | None:
        """
        Get the recorded minimum.

        :return: the recorded minimum or `None` if no value was added yet

        >>> ss = StreamStats()
        >>> print(ss.minimum())
        None
        >>> ss.add(23)
        >>> ss.minimum()
        23
        >>> ss.add(12.0)
        >>> ss.minimum()
        12
        >>> ss.add(112)
        >>> ss.minimum()
        12
        >>> ss.reset()
        >>> print(ss.minimum())
        None
        """
        return None if self.__n <= 0 else try_int(self.__min)

    def maximum(self) -> int | float | None:
        """
        Get the recorded maximum.

        :return: the recorded maximum or `None` if no value was added yet

        >>> ss = StreamStats()
        >>> print(ss.maximum())
        None
        >>> ss.add(23)
        >>> ss.maximum()
        23
        >>> ss.add(12)
        >>> ss.maximum()
        23
        >>> ss.add(112)
        >>> ss.maximum()
        112
        >>> ss.reset()
        >>> print(ss.maximum())
        None
        """
        return None if self.__n <= 0 else try_int(self.__max)
