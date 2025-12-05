"""
An immutable record for statistics computed over a stream of data.

Stream statistics, represented by class
:class:`~pycommons.math.stream_statistics.StreamStatistics` are statistics
that are computed over a stream of data. During the computation, only a
minimal amount of data is actually kept in memory, such as a running sum,
the overall minimum and maximum, etc.
This makes these statistics suitable

- if the amount of data is large and
- the required accuracy is not very high and/or
- the available computational budget or memory are limited.

In this case, using the
:class:`~pycommons.math.stream_statistics.StreamStatistics` routines are
very suitable.
You could, e.g., use the method
:meth:`~pycommons.math.stream_statistics.StreamStatistics.aggregate` to
obtain an aggregation object. This object allows you to iteratively append
data to the current statistics computation via its `add` method and to obtain
the current (or final) statistics result via the `result` method.

Such a result is an instance of the class
:class:`~pycommons.math.stream_statistics.StreamStatistics`.
It stores the
:attr:`~pycommons.math.stream_statistics.StreamStatistics.minimum` and the
:attr:`~pycommons.math.stream_statistics.StreamStatistics.maximum` of the
data, as well as the number
:attr:`~pycommons.math.stream_statistics.StreamStatistics.n` of observed data
samples.
It also offers the approximations of the arithmetic mean as attribute
:attr:`~pycommons.math.stream_statistics.StreamStatistics.mean_arith` and
the approximation of the standard deviation as attribute
:attr:`~pycommons.math.stream_statistics.StreamStatistics.stddev`.

There is an absolute order defined upon these records.
They are hashable and immutable.
We provide methods to store them to CSV format via the class
:class:`~pycommons.math.stream_statistics.CsvWriter`
and to load them from CSV data via the class
:class:`~pycommons.math.stream_statistics.CsvReader`.
Functions that access attributes can be obtained via
:meth:`~pycommons.math.stream_statistics.StreamStatistics.getter`.

If you require high-accuracy statistics or values such as the median, you
should use
:class:`~pycommons.math.sample_statistics.SampleStatistics` instead.

>>> ag = StreamStatistics.aggregate()
>>> ag.update((1, 2, 3))
>>> ag.add(4)
>>> ag.add(5)
>>> r1 = ag.result()
>>> repr(r1)
'StreamStatistics(n=5, minimum=1, mean_arith=3, maximum=5, \
stddev=1.5811388300841898)'
>>> str(r1)
'5;1;3;5;1.5811388300841898'

>>> r2 = StreamStatistics.from_samples((1, 2, 3, 4, 5))
>>> r1 == r2
True

>>> ag.reset()
>>> try:
...     ag.result()
... except ValueError as ve:
...     print(ve)
n=0 is invalid, must be in 1..9223372036854775808.

>>> print(ag.result_or_none())
None
"""

from dataclasses import dataclass
from math import inf, isfinite, sqrt
from typing import Callable, Final, Iterable, TypeVar, Union, cast

from pycommons.io.csv import (
    CSV_SEPARATOR,
    SCOPE_SEPARATOR,
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_val_or_none,
    pycommons_footer_bottom_comments,
)
from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.math.int_math import (
    try_float_int_div,
    try_int,
)
from pycommons.math.streams import StreamAggregate
from pycommons.strings.string_conv import (
    num_or_none_to_str,
    num_to_str,
    str_to_num,
)
from pycommons.types import check_int_range, type_error, type_name

#: The minimum value key.
KEY_MINIMUM: Final[str] = "min"
#: The median value key.
KEY_MEDIAN: Final[str] = "med"
#: The arithmetic mean value key.
KEY_MEAN_ARITH: Final[str] = "mean"
#: The geometric mean value key.
KEY_MEAN_GEOM: Final[str] = "geom"
#: The maximum value key.
KEY_MAXIMUM: Final[str] = "max"
#: The standard deviation value key.
KEY_STDDEV: Final[str] = "sd"
#: The key for `n`
KEY_N: Final[str] = "n"
#: The single value
KEY_VALUE: Final[str] = "value"

#: the type variable for data to be written to CSV or to be read from CSV
T = TypeVar("T", bound="StreamStatistics")


class StreamStatisticsAggregate[T](StreamAggregate):
    """An Aggregate producing stream statistics."""

    def result(self) -> T:
        """
        Get the stream statistics result.

        The result is guaranteed to be a valid instance of
        :class:`~pycommons.math.stream_statistics.StreamStatistics`.
        It has :attr:`~pycommons.math.stream_statistics.StreamStatistics.n`
        greater than zero.

        If no data was collected, a `ValueError` is raised.
        If you want to get `None` if no data was collected, use
        :meth:`~StreamStatisticsAggregate.result_or_none` instead.

        :return: the result
        :raises ValueError: if no data was collected

        >>> try:
        ...     StreamStatisticsAggregate().result()
        ... except NotImplementedError:
        ...     print("Not implemented!")
        Not implemented!
        """
        raise NotImplementedError

    def result_or_none(self) -> T | None:
        """
        Get the result if any data was collected, otherwise `None`.

        This method returns the same result as
        :meth:`~StreamStatisticsAggregate.result`, with the exception of the
        case where no data was collected at all. In this case,
        :meth:`~StreamStatisticsAggregate.result` will raise a `ValueError`,
        whereas this method here just returns `None`.

        :return: the result, or `None` if no data was collected.

        >>> try:
        ...     StreamStatisticsAggregate().result_or_none()
        ... except NotImplementedError:
        ...     print("Not implemented!")
        Not implemented!
        """
        raise NotImplementedError


@dataclass(frozen=True, init=False, order=False, eq=False)
class StreamStatistics:
    """
    An immutable record with stream statistics of one quantity.

    Stream statistics are statistics records that can be computed over a
    stream of data. They do not require us to have the complete data sample
    in memory at any point in time.

    >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
    >>> s1.n
    2
    >>> s1.minimum
    1
    >>> s1.mean_arith
    4
    >>> s1.maximum
    6
    >>> s1.stddev
    0.2
    >>> hash(s1)
    -997568919428664316

    >>> s2 = StreamStatistics(1, 0, 0, 0.0, None)
    >>> s2.n
    1
    >>> s2.minimum
    0
    >>> s2.mean_arith
    0
    >>> s2.maximum
    0
    >>> print(s2.stddev)
    None
    >>> hash(s2) == hash((0, 0, 0, inf, 0, inf, 1, 0))
    True

    >>> s3 = StreamStatistics(n=3, minimum=5, maximum=5,
    ...                       mean_arith=5, stddev=0.0)
    >>> s3.stddev
    0
    >>> hash(s3)
    -5331876985145994286

    >>> sset = {s1, s1, s2, s1, s3, s3, s2, s1}
    >>> len(sset)
    3
    >>> print(list(sss.n for sss in sorted(sset)))
    [1, 2, 3]
    >>> print(list(sss.minimum for sss in sorted(sset)))
    [0, 1, 5]

    >>> try:
    ...     StreamStatistics(n=1, minimum=5, maximum=6,
    ...                      mean_arith=5, stddev=None)
    ... except ValueError as ve:
    ...     print(ve)
    maximum (6) must equal minimum (5) if n=1.

    >>> try:
    ...     StreamStatistics(n=1, minimum=5, maximum=5,
    ...                      mean_arith=4, stddev=None)
    ... except ValueError as ve:
    ...     print(ve)
    mean_arith (4) must equal minimum (5) if n=1.

    >>> try:
    ...     StreamStatistics(n=2, minimum=5, maximum=6,
    ...                      mean_arith=4, stddev=None)
    ... except ValueError as ve:
    ...     print(ve)
    minimum<=mean_arith<=maximum must hold, but got 5, 4, and 6.

    >>> try:
    ...     StreamStatistics(n=3, minimum=5, maximum=7,
    ...                      mean_arith=6, stddev=-1)
    ... except ValueError as ve:
    ...     print(ve)
    stddev must be >= 0, but is -1.

    >>> try:
    ...     StreamStatistics(n=3, minimum=5, maximum=7,
    ...                      mean_arith=6, stddev=0)
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    If stddev (0) is 0, then minimum (5) must equal maximum (7)

    >>> try:
    ...     StreamStatistics(n=3, minimum=5, maximum=5,
    ...                      mean_arith=5, stddev=1)
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    If stddev (1) is 0, then minimum (5) must equal maximum (5)

    >>> try:
    ...     StreamStatistics(n=3, minimum=5, maximum=5,
    ...                      mean_arith=5, stddev=None)
    ... except ValueError as ve:
    ...     print(ve)
    If n=1, stddev=None and vice versa, but got n=3 and stddev=None.

    >>> try:
    ...     StreamStatistics(n=1, minimum=5, maximum=5,
    ...                      mean_arith=5, stddev=1)
    ... except ValueError as ve:
    ...     print(ve)
    If n=1, stddev=None and vice versa, but got n=1 and stddev=1.
    """

    #: The number of data samples over which the statistics were computed.
    n: int
    #: The minimum, i.e., the value of the smallest among the
    #: :attr:`~StreamStatistics.n` data samples.
    minimum: int | float
    #: The arithmetic mean value, i.e., the sum of the
    #: :attr:`~StreamStatistics.n` data samples divided by
    #: :attr:`~StreamStatistics.n`.
    mean_arith: int | float
    #: The maximum, i.e., the value of the largest among the
    #: :attr:`~StreamStatistics.n` data samples.
    maximum: int | float
    #: The standard deviation, if defined. This value will be `None` if there
    #: was only a single sample.
    stddev: int | float | None

    def __init__(self, n: int, minimum: int | float, mean_arith: int | float,
                 maximum: int | float, stddev: int | float | None):
        """
        Create a sample statistics record.

        :param n: the sample size, must be `n >= 1`
        :param minimum: the minimum
        :param median: the median
        :param mean_arith: the arithmetic mean
        :param mean_geom: the geometric mean, or `None` if it is undefined
        :param maximum: the maximum
        :param stddev: the standard deviation, must be `None` if `n == 0`
        """
        n = check_int_range(n, "n", 1, 9_223_372_036_854_775_808)

        # check minimum
        minimum = try_int(minimum)
        # check maximum
        maximum = try_int(maximum)
        if (n == 1) and (maximum != minimum):
            raise ValueError(f"maximum ({maximum}) must equal "
                             f"minimum ({minimum}) if n=1.")
        # check arithmetic mean
        mean_arith = try_int(mean_arith)
        if n == 1:
            if mean_arith != minimum:
                raise ValueError(f"mean_arith ({mean_arith}) must equal "
                                 f"minimum ({minimum}) if n=1.")
        elif not minimum <= mean_arith <= maximum:
            raise ValueError("minimum<=mean_arith<=maximum must hold, but "
                             f"got {minimum}, {mean_arith}, and {maximum}.")

        if stddev is not None:
            stddev = try_int(stddev)
            if stddev < 0:
                raise ValueError(f"stddev must be >= 0, but is {stddev}.")
            if (n > 1) and ((minimum == maximum) ^ (stddev == 0)):
                raise ValueError(
                    f"If stddev ({stddev}) is 0, then minimum ({minimum}) "
                    f"must equal maximum ({maximum}) and vice versa.")
        if (stddev is None) ^ (n == 1):
            raise ValueError("If n=1, stddev=None and vice versa, but "
                             f"got n={n} and stddev={stddev}.")

        object.__setattr__(self, "n", n)
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "mean_arith", mean_arith)
        object.__setattr__(self, "stddev", stddev)

    def __str__(self) -> str:
        """
        Get a string representation of this object.

        :returns: the string

        >>> print(StreamStatistics(1, 0, 0, 0.0, None))
        1;0;0;0;None

        >>> print(StreamStatistics(10, 1, 1.5, 2, 1.2))
        10;1;1.5;2;1.2
        """
        return CSV_SEPARATOR.join(map(str, (
            self.n, self.minimum, self.mean_arith, self.maximum,
            self.stddev)))

    def min_mean(self) -> int | float:
        """
        Obtain the smallest of the mean values.

        :returns: :attr:`~StreamStatistics.mean_arith`

        >>> StreamStatistics(1, 0, 0, 0.0, None).min_mean()
        0
        >>> StreamStatistics(2, 1, 2, 4.0, 0.2).min_mean()
        2
        """
        return self.mean_arith

    def max_mean(self) -> int | float:
        """
        Obtain the largest of the mean values.

        :returns: :attr:`~StreamStatistics.mean_arith`


        >>> StreamStatistics(1, 0, 0, 0.0, None).max_mean()
        0
        >>> StreamStatistics(2, 1, 2, 4.0, 0.2).max_mean()
        2
        """
        return self.mean_arith

    def compact(self, needs_n: bool = True) \
            -> "int | float | StreamStatistics":
        """
        Try to represent this object as single number, if possible.

        :param needs_n: if this is `True`, the default, then the object is
            only turned into a single number if alsp `n==1`. Otherwise, `n`
            is ignored
        :returns: an integer or float if this objects minimum equals its
            maximum, the object itself otherwise

        >>> s = StreamStatistics.from_single_value(10, 1)
        >>> s.compact() == 10
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = StreamStatistics.from_single_value(10, 2)
        >>> s.compact() is s
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = StreamStatistics.from_single_value(10, 2)
        >>> s.compact(False) == 10
        True

        >>> s = StreamStatistics(2, 1, 3, 5, 3)
        >>> s.compact() is s
        True

        >>> s = StreamStatistics(2, 1, 3, 5, 3)
        >>> s.compact(False) is s
        True

        >>> try:
        ...     s.compact(1)
        ... except TypeError as te:
        ...     print(te)
        needs_n should be an instance of bool but is int, namely 1.

        >>> try:
        ...     s.compact(None)
        ... except TypeError as te:
        ...     print(te)
        needs_n should be an instance of bool but is None.
        """
        if not isinstance(needs_n, bool):
            raise type_error(needs_n, "needs_n", bool)
        mi: Final[int | float] = self.minimum
        return self if (mi < self.maximum) or (
            needs_n and (self.n > 1)) else mi

    def _key(self) -> tuple[int | float, int | float, int | float,
                            int | float, int | float, int | float, int, int]:
        r"""
        Get a comparison and hash key.

        This key is composed of the values for
        :attr:`~StreamStatistics.minimum`, `inf` (for the geometric mean),
        :attr:`~StreamStatistics.mean_arith`, `inf` (for the median),
        :attr:`~StreamStatistics.maximum`, :attr:`~StreamStatistics.stddev`,
        and :attr:`~StreamStatistics.n`. Any statistics value that is
        undefined will be turned to `inf`. The last value is a unique
        identifier of the object type. This is to prevent objects of type
        `StreamStatistics` and `SampleStatistics` to clash. Therefore, the
        former gets `0` as identifier, the latter gets `1`.

        :returns: the comparison key

        >>> StreamStatistics(2, 1, 4.0, 6, 0.2)._key()
        (1, inf, 4, inf, 6, 0.2, 2, 0)

        >>> StreamStatistics(1, 0, 0, 0, None)._key()
        (0, 0, 0, inf, 0, inf, 1, 0)

        >>> StreamStatistics(2, 1, 1, 1, 0)._key()
        (1, 1, 1, 1, 1, 0, 2, 0)

        >>> StreamStatistics(2, 0, 0, 0, 0)._key()
        (0, 0, 0, inf, 0, 0, 2, 0)
        """
        mi: Final[int | float] = self.minimum
        ma: Final[int | float] = self.maximum
        return (mi, inf if ma > mi else mi, self.mean_arith,
                mi if 0 < ma <= mi else inf, ma,
                inf if self.stddev is None else self.stddev, self.n, 0)

    def __lt__(self, other) -> bool:
        """
        Check if this statistics record is less than another one.

        :param other: the other sample statistics
        :returns: `True` if this object is less, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 < s2
        False

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 < s1
        True
        >>> s1 < s3
        False

        >>> try:
        ...     s3 < 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        '<' not supported between instances of 'StreamStatistics' an
        """
        return self._key() < other._key()\
            if isinstance(other, StreamStatistics) else NotImplemented

    def __le__(self, other) -> bool:
        """
        Check if this statistics record is less than or equal to another one.

        :param other: the other sample statistics
        :returns: `True` if this object is less or equal, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 <= s2
        True

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 <= s1
        True
        >>> s1 <= s3
        False

        >>> try:
        ...     s3 <= 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        '<=' not supported between instances of 'StreamStatistics' a
        """
        return self._key() <= other._key() \
            if isinstance(other, StreamStatistics) else NotImplemented

    def __gt__(self, other) -> bool:
        """
        Check if this statistics record is greater than another one.

        :param other: the other sample statistics
        :returns: `True` if this object is greater, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 > s2
        False

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 > s1
        False
        >>> s1 > s3
        True

        >>> try:
        ...     s3 > 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        '>' not supported between instances of 'StreamStatistics' an
        """
        return self._key() > other._key() \
            if isinstance(other, StreamStatistics) else NotImplemented

    def __ge__(self, other) -> bool:
        """
        Check if this object is greater than or equal to another one.

        :param other: the other sample statistics
        :returns: `True` if this object is greater or equal, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 >= s2
        True

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 >= s1
        False
        >>> s1 >= s3
        True

        >>> try:
        ...     s3 >= 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        '>=' not supported between instances of 'StreamStatistics' a
        """
        return self._key() >= other._key() \
            if isinstance(other, StreamStatistics) else NotImplemented

    def __eq__(self, other) -> bool:
        """
        Check if this statistics record equals another object.

        :param other: the other obect
        :returns: `True` if this object is equal, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 == s2
        True

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 == s1
        False

        >>> s3 == 23
        False
        """
        return (isinstance(other, StreamStatistics)) and (
            self._key() == other._key())

    def __ne__(self, other) -> bool:
        """
        Check if this statistics record does not equal another object.

        :param other: the other sample statistics
        :returns: `True` if this object is not equal, `False` otherwise

        >>> s1 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s2 = StreamStatistics(2, 1, 4.0, 6, 0.2)
        >>> s1 != s2
        False

        >>> s3 = StreamStatistics(2, 0.5, 4.0, 6, 0.2)
        >>> s3 != s1
        True

        >>> s3 != "x"
        True
        """
        return (not isinstance(other, StreamStatistics)) or (
            self._key() != other._key())

    def __hash__(self) -> int:
        """
        Compute the hash code of this statistics record.

        :returns: the hash code

        >>> hash(StreamStatistics(2, 1, 4.0, 6, 0.2))
        -997568919428664316

        >>> hash(StreamStatistics(2, -1, 4.0, 6, 0.2))
        -1901621203255131428
        """
        return hash(self._key())

    def get_n(self) -> int:
        """
        Get the number :attr:`~StreamStatistics.n` of samples.

        :returns: the number :attr:`~StreamStatistics.n` of samples.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> StreamStatistics(5, 3, 6, 7, 2).get_n()
        5

        >>> try:
        ...     StreamStatistics.get_n(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.n

    def get_minimum(self) -> int | float:
        """
        Get the :attr:`~StreamStatistics.minimum` of all the samples.

        :returns: the :attr:`~StreamStatistics.minimum` of all the samples
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> StreamStatistics(5, 3, 4, 6, 2).get_minimum()
        3

        >>> try:
        ...     StreamStatistics.get_minimum(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.minimum

    def get_maximum(self) -> int | float:
        """
        Get the :attr:`~StreamStatistics.maximum` of all the samples.

        :returns: the :attr:`~StreamStatistics.maximum` of all the samples
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> StreamStatistics(5, 3, 6, 7, 2).get_maximum()
        7

        >>> try:
        ...     StreamStatistics.get_maximum(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.maximum

    def get_mean_arith(self) -> int | float:
        """
        Get the arithmetic mean (:attr:`~StreamStatistics.mean_arith`).

        :returns: the arithmetic mean (:attr:`~StreamStatistics.mean_arith`)
            of all the samples.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> StreamStatistics(5, 3, 6, 7, 2).get_mean_arith()
        6

        >>> try:
        ...     StreamStatistics.get_mean_arith(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.mean_arith

    def get_median(self) -> int | float | None:
        """
        Get the median of all the samples.

        :returns: This object type does not store the media. However, if
            the minimum is the same as the maximum, the median will have that
            same value, too, so it is returned. Otherwise, this method returns
            `None`. This method will be overridden.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> print(StreamStatistics(5, 3, 6, 7, 2).get_median())
        None

        >>> print(StreamStatistics(5, -3, -3.0, -3, 0).get_median())
        -3

        >>> try:
        ...     StreamStatistics.get_median(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.minimum if self.minimum >= self.maximum else None

    def get_mean_geom(self) -> int | float | None:
        """
        Get the geometric mean of all the samples.

        This class does not offer storing the geometric mean. This means
        that this method will usually return `None`. The only situation
        where it will not return `None` is if the geometric mean can be
        inferred by definition, namely if the minimum and maximum value
        are the same and positive. Subclasses will override this method to
        return meaningful values.

        :returns: the geometric mean of all the samples, `None` if the
            geometric mean is not defined.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> print(StreamStatistics(5, 3, 6, 7, 2).get_mean_geom())
        None

        >>> print(StreamStatistics(5, 2, 2, 2, 0).get_mean_geom())
        2

        >>> try:
        ...     StreamStatistics.get_mean_geom(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        mi: Final[int | float] = self.minimum
        return mi if 0 < self.maximum <= mi else None

    def get_stddev(self) -> int | float | None:
        """
        Get the standard deviation mean (:attr:`~StreamStatistics.stddev`).

        :returns: the standard deviation (:attr:`~StreamStatistics.stddev`)
            of all the samples, `None` if the standard deviation is not
            defined, i.e., if there is only a single sample
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> StreamStatistics(5, 3, 6, 7, 2).get_stddev()
        2

        >>> try:
        ...     StreamStatistics.get_stddev(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, StreamStatistics):
            raise type_error(self, "self", StreamStatistics)
        return self.stddev

    @classmethod
    def aggregate(cls) -> StreamStatisticsAggregate["StreamStatistics"]:
        """
        Get an aggregate suitable for this statistics type.

        :return: the aggregate

        >>> ag = StreamStatistics.aggregate()
        >>> ag.update((1, 2, 3, 4))
        >>> ag.result()
        StreamStatistics(n=4, minimum=1, mean_arith=2.5, maximum=4, \
stddev=1.2909944487358056)
        >>> ag.reset()
        >>> ag.add(4)
        >>> ag.add(5)
        >>> ag.add(6)
        >>> ag.add(7)
        >>> ag.result()
        StreamStatistics(n=4, minimum=4, mean_arith=5.5, maximum=7, \
stddev=1.2909944487358056)
        """
        return _StreamStats()

    @classmethod
    def from_samples(cls, source: Iterable[
            int | float | None]) -> "StreamStatistics":
        """
        Create a statistics record from a stream of samples.

        :return: the statistics record.

        >>> StreamStatistics.from_samples((1, 2, 3, 4))
        StreamStatistics(n=4, minimum=1, mean_arith=2.5, maximum=4, \
stddev=1.2909944487358056)
        """
        agg: Final[StreamStatisticsAggregate] = cls.aggregate()
        agg.update(source)
        return agg.result()

    @classmethod
    def from_single_value(cls, value: Union[
            int, float, "StreamStatistics"], n: int = 1) -> "StreamStatistics":
        r"""
        Create a sample statistics from a single number.

        :param value: the single value
        :param n: the number of samples, i.e., the number of times this value
            occurred
        :returns: the sample statistics

        >>> print(str(StreamStatistics.from_single_value(23)))
        1;23;23;23;None

        >>> s = StreamStatistics.from_single_value(10, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == 10
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(10, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == 10
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(-10, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == -10
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(-10, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == -10
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(10.5, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith  == 10.5
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(10.5, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == 10.5
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(-10.5, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == -10.5
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> s = StreamStatistics.from_single_value(-10.5, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == -10.5
        True
        >>> s is StreamStatistics.from_single_value(s, s.n)
        True

        >>> try:
        ...     StreamStatistics.from_single_value(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        value should be an i

        >>> try:
        ...     StreamStatistics.from_single_value("a")
        ... except TypeError as te:
        ...     print(str(te)[:20])
        value should be an i

        >>> try:
        ...     StreamStatistics.from_single_value(1, None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        n should be an insta

        >>> try:
        ...     StreamStatistics.from_single_value(1, "a")
        ... except TypeError as te:
        ...     print(str(te)[:20])
        n should be an insta

        >>> try:
        ...     StreamStatistics.from_single_value(s, 12)
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        Incompatible numbers

        >>> try:
        ...     StreamStatistics.from_single_value(inf)
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        value=inf is not fin
        """
        n = check_int_range(n, "n", 1, 1_000_000_000_000_000_000)
        if isinstance(value, StreamStatistics):
            if value.n == n:
                return value
            raise ValueError(  # noqa: TRY004
                f"Incompatible numbers of values {n} and {value}.")
        if not isinstance(value, int | float):
            raise type_error(value, "value", (int, float, StreamStatistics))
        if not isfinite(value):
            raise ValueError(f"value={value} is not finite.")
        return StreamStatistics(
            n=n, minimum=value, mean_arith=value, maximum=value,
            stddev=None if n <= 1 else 0)

    @classmethod
    def getter(cls, dimension: str) -> Callable[[
            "StreamStatistics"], int | float | None]:
        """
        Get a function returning the dimension from :class:`StreamStatistics`.

        The returned getter function expects that it receives a valid
        :class:`StreamStatistics` instance as parameter, or an instance of the
        subclass you called :meth:`StreamStatistics.getter` on. If you pass in
        `None`, then ths will raise a `TypeError`. If you are in a situation
        where `None` is possible, use the function
        :meth:`StreamStatistics.getter_or_none` instead, which will return
        `None` in such a case.

        :param dimension: the dimension
        :returns: a :class:`Callable` that returns the value corresponding to
            the dimension
        :raises TypeError: if `dimension` is not a string
        :raises ValueError: if `dimension` is unknown

        >>> StreamStatistics.getter(KEY_N) is StreamStatistics.get_n
        True
        >>> (StreamStatistics.getter(KEY_MINIMUM) is
        ...     StreamStatistics.get_minimum)
        True
        >>> (StreamStatistics.getter(KEY_MEAN_ARITH) is
        ...     StreamStatistics.get_mean_arith)
        True
        >>> (StreamStatistics.getter(KEY_MEAN_GEOM) is
        ...     StreamStatistics.get_mean_geom)
        True
        >>> (StreamStatistics.getter(KEY_MAXIMUM) is
        ...     StreamStatistics.get_maximum)
        True
        >>> (StreamStatistics.getter(KEY_MEDIAN) is
        ...     StreamStatistics.get_median)
        True
        >>> (StreamStatistics.getter(KEY_STDDEV) is
        ...     StreamStatistics.get_stddev)
        True

        >>> s = StreamStatistics(5, 3,  6, 7, 2)
        >>> StreamStatistics.getter(KEY_N)(s)
        5
        >>> StreamStatistics.getter(KEY_MINIMUM)(s)
        3
        >>> StreamStatistics.getter(KEY_MEAN_ARITH)(s)
        6
        >>> print(StreamStatistics.getter(KEY_MEAN_GEOM)(s))
        None
        >>> StreamStatistics.getter(KEY_MAXIMUM)(s)
        7
        >>> StreamStatistics.getter(KEY_STDDEV)(s)
        2
        >>> print(StreamStatistics.getter(KEY_MEDIAN)(s))
        None

        >>> try:
        ...     StreamStatistics.getter(KEY_N)(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in

        >>> try:
        ...     StreamStatistics.getter(None)
        ... except TypeError as te:
        ...     print(te)
        descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' \
object

        >>> try:
        ...     StreamStatistics.getter(1)
        ... except TypeError as te:
        ...     print(te)
        descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

        >>> try:
        ...     StreamStatistics.getter("hello")
        ... except ValueError as ve:
        ...     print(str(ve)[-18:])
        dimension 'hello'.
        """
        tbl_name: Final[str] = "___cls_getters"
        if hasattr(cls, tbl_name):
            getters = cast("Callable", getattr(cls, tbl_name))
        else:
            getters = {
                KEY_N: cls.get_n, KEY_MINIMUM: cls.get_minimum,
                "minimum": cls.get_minimum,
                KEY_MEAN_ARITH: cls.get_mean_arith,
                "mean_arith": cls.get_mean_arith,
                "arithmetic mean": cls.get_mean_arith,
                "average": cls.get_mean_arith, KEY_MEDIAN: cls.get_median,
                "median": cls.get_median, KEY_MEAN_GEOM: cls.get_mean_geom,
                "mean_geom": cls.get_mean_geom,
                "geometric mean": cls.get_mean_geom,
                "gmean": cls.get_mean_geom, KEY_MAXIMUM: cls.get_maximum,
                "maximum": cls.get_maximum, KEY_STDDEV: cls.get_stddev,
                "stddev": cls.get_stddev,
                "standard deviation": cls.get_stddev}.get
            setattr(cls, tbl_name, getters)

        result: Callable[[StreamStatistics], int | float | None] | None \
            = getters(str.strip(dimension), None)
        if result is None:
            raise ValueError(f"Unknown {cls} dimension {dimension!r}.")
        return result

    @classmethod
    def getter_or_none(cls, dimension: str) -> Callable[[
            Union["StreamStatistics", None]], int | float | None]:
        """
        Obtain a getter that returns `None` if the statistics is `None`.

        With this method, you can get a function which returns a value from a
        statistics object if the object is not `None`. If `None` is provided,
        then the function also returns `None`.

        This is especially useful if you work with something like
        :meth:`~StreamStatisticsAggregate.result_or_none`.

        If your data should never be `None`, the better use
        :meth:`StreamStatistics.getter` instead, which returns getter
        functions that raise `TypeError`s if their input is `None`.

        :param dimension: the dimension
        :return: the getter

        >>> ss = StreamStatistics(10, 1, 2, 3, 4)
        >>> g = StreamStatistics.getter_or_none(KEY_MINIMUM)
        >>> g(ss)
        1
        >>> print(g(None))
        None
        >>> StreamStatistics.getter_or_none(KEY_MINIMUM) is g
        True

        >>> g = StreamStatistics.getter_or_none(KEY_MAXIMUM)
        >>> g(ss)
        3
        >>> print(g(None))
        None
        """
        tbl_name: Final[str] = "___cls_getters_or_none"
        if hasattr(cls, tbl_name):
            getters = cast("dict", getattr(cls, tbl_name))
        else:
            getters = {}
            setattr(cls, tbl_name, getters)

        dimension = str.strip(dimension)
        if dimension in getters:
            return getters[dimension]

        def __getter(x, _y=cls.getter(dimension)) -> int | float | None:
            return None if x is None else _y(x)

        getters[dimension] = __getter
        return cast("Callable", __getter)


class _StreamStats(StreamStatisticsAggregate[StreamStatistics]):
    """
    The internal stream statistics.

    The stream statistics compute mean and variance of data using Welford's
    algorithm.

    1. Donald E. Knuth (1998). The Art of Computer Programming, volume 2:
       Seminumerical Algorithms, 3rd edn., p. 232. Boston: Addison-Wesley.
    2. B. P. Welford (1962). "Note on a method for calculating corrected sums
       of squares and products". Technometrics 4(3):419-420.

    >>> ss = _StreamStats()
    >>> data1 = [4, 7, 13, 16]
    >>> ss.update(data1)
    >>> ss.result()
    StreamStatistics(n=4, minimum=4, mean_arith=10, maximum=16, \
stddev=5.477225575051661)

    >>> data2 = [1e8 + z for z in data1]
    >>> ss.reset()
    >>> ss.update(data2)
    >>> ss.result()
    StreamStatistics(n=4, minimum=100000004, mean_arith=100000010, \
maximum=100000016, stddev=5.477225575051661)

    >>> data3 = [1e14 + z for z in data1]
    >>> ss.reset()
    >>> ss.update(data3)
    >>> ss.result()
    StreamStatistics(n=4, minimum=100000000000004, \
mean_arith=100000000000010, maximum=100000000000016, stddev=5.477225575051661)

    >>> data3 = [z for z in range(1001)]
    >>> ss.reset()
    >>> ss.update(data3)
    >>> ss.result()
    StreamStatistics(n=1001, minimum=0, mean_arith=500, maximum=1000, \
stddev=289.10811126635656)
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

    def result(self) -> StreamStatistics:
        """
        Get the arithmetic mean.

        :return: the arithmetic mean or `None` if no value was added yet
        """
        n: Final[int] = self.__n
        mi: Final[int | float] = self.__min
        ma: Final[int | float] = self.__max
        return StreamStatistics(
            n, mi, max(mi, min(ma, self.__mean)), ma,
            None if n <= 1 else (0 if ma <= mi else sqrt(
                try_float_int_div(self.__var, n - 1))))

    def result_or_none(self) -> StreamStatistics | None:
        """
        Get the result if any data was collected, otherwise `None`.

        :return: The return value of :meth:`result` if any data was collected,
            otherwise `None`
        """
        return self.result() if self.__n > 0 else None


class CsvReader(CsvReaderBase[StreamStatistics]):
    """
    A csv parser for sample statistics.

    >>> from pycommons.io.csv import csv_read
    >>> csv = ["n;min;mean;max;sd",
    ...        "3;2;3;10;5", "6;2;;;0", "1;;2", "3;;;0;",
    ...        "4;5;12;33;7"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    3;2;3;10;5
    6;2;2;2;0
    1;2;2;2;None
    3;0;0;0;0
    4;5;12;33;7

    >>> csv = ["value", "1", "3", "0", "-5", "7"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    1;1;1;1;None
    1;3;3;3;None
    1;0;0;0;None
    1;-5;-5;-5;None
    1;7;7;7;None

    >>> csv = ["n;m;sd", "1;3;", "3;5;0"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    1;3;3;3;None
    3;5;5;5;0

    >>> csv = ["n;m", "1;3", "3;5"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    1;3;3;3;None
    3;5;5;5;0
    """

    def __init__(self, columns: dict[str, int]) -> None:
        """
        Create a CSV parser for :class:`SampleStatistics`.

        :param columns: the columns

        >>> try:
        ...     CsvReader(None)
        ... except TypeError as te:
        ...     print(te)
        columns should be an instance of dict but is None.

        >>> try:
        ...     CsvReader(1)
        ... except TypeError as te:
        ...     print(te)
        columns should be an instance of dict but is int, namely 1.

        >>> try:
        ...     CsvReader(dict())
        ... except ValueError as ve:
        ...     print(ve)
        No useful keys remain in {}.

        >>> try:
        ...     CsvReader({"a": 1, "b": 2})
        ... except ValueError as ve:
        ...     print(ve)
        No useful keys remain in {'a': 1, 'b': 2}.

        >>> try:
        ...     CsvReader({KEY_N: 1, "b": 2, "c": 3})
        ... except ValueError as ve:
        ...     print(ve)
        No useful keys remain in {'b': 2, 'c': 3}.

        >>> try:
        ...     CsvReader({KEY_MINIMUM: 1, "b": 2, "c": 3})
        ... except ValueError as ve:
        ...     print(ve)
        Found strange keys in {'b': 2, 'c': 3}.
        """
        super().__init__(columns)

        #: the index of the number of elements
        self.idx_n: Final[int | None] = csv_column_or_none(
            columns, KEY_N)

        has: int = 0
        has_idx: int = -1

        #: the index of the minimum
        self.__idx_min: int | None = csv_column_or_none(
            columns, KEY_MINIMUM)
        if self.__idx_min is not None:
            has += 1
            has_idx = self.__idx_min

        #: the index for the arithmetic mean
        self.__idx_mean_arith: int | None = csv_column_or_none(
            columns, KEY_MEAN_ARITH)
        if self.__idx_mean_arith is not None:
            has += 1
            has_idx = self.__idx_mean_arith

        #: the index for the maximum
        self.__idx_max: int | None = csv_column_or_none(
            columns, KEY_MAXIMUM)
        if self.__idx_max is not None:
            has += 1
            has_idx = self.__idx_max

        #: the index for the standard deviation
        self.__idx_sd: Final[int | None] = csv_column_or_none(
            columns, KEY_STDDEV)

        if has <= 0:
            if dict.__len__(columns) == 1:
                self.__idx_min = has_idx = csv_column(
                    columns, next(iter(columns.keys())), True)
                has = 1
            else:
                raise ValueError(f"No useful keys remain in {columns!r}.")
        if dict.__len__(columns) > 1:
            raise ValueError(f"Found strange keys in {columns!r}.")

        #: is this a parser for single number statistics?
        self.__is_single: Final[bool] = (self.__idx_sd is None) and (has == 1)

        if self.__is_single:
            self.__idx_min = self.__idx_max = self.__idx_mean_arith = has_idx

    def parse_row(self, data: list[str]) -> StreamStatistics:
        """
        Parse a row of data.

        :param data: the data row
        :returns: the sample statistics

        >>> cc = CsvReader({KEY_MINIMUM: 0, KEY_MEAN_ARITH: 1, KEY_MAXIMUM: 2,
        ...                 KEY_STDDEV: 3, KEY_N: 4})
        >>> try:
        ...     cc.parse_row([None, None, None, None, "5"])
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        No value defined for
        """
        n: Final[int] = 1 if self.idx_n is None else int(data[self.idx_n])
        mi: int | float | None = csv_val_or_none(
            data, self.__idx_min, str_to_num)

        if self.__is_single:
            return StreamStatistics(
                n=n, minimum=mi, mean_arith=mi,
                maximum=mi, stddev=None if n <= 1 else 0)

        ar: int | float | None = csv_val_or_none(
            data, self.__idx_mean_arith, str_to_num)
        ma: int | float | None = csv_val_or_none(
            data, self.__idx_max, str_to_num)
        sd: int | float | None = csv_val_or_none(
            data, self.__idx_sd, str_to_num)

        if mi is None:
            if ar is not None:
                mi = ar
            elif ma is not None:
                mi = ma
            else:
                raise ValueError(
                    f"No value defined for min@{self.__idx_min}={mi}, mean@"
                    f"{self.__idx_mean_arith}={ar}, max@"
                    f"{self.__idx_max}={ma} defined in {data!r}.")
        return StreamStatistics(
            n=n, minimum=mi, mean_arith=mi if ar is None else ar,
            maximum=mi if ma is None else ma,
            stddev=(0 if (n > 1) else None) if sd is None else sd)

    def parse_optional_row(self, data: list[str] | None) \
            -> StreamStatistics | None:
        """
        Parse a row of data that may be empty.

        :param data: the row of data that may be empty
        :returns: the sample statistic, if the row contains data, else `None`

        >>> print(CsvReader.parse_optional_row(None, ["1"]))
        None
        >>> print(CsvReader.parse_optional_row(CsvReader({"v": 0}), ["1"]))
        1;1;1;1;None
        >>> print(CsvReader.parse_optional_row(CsvReader({"v": 0}), [""]))
        None
        """
        if (self is None) or (data is None):
            return None  # trick to make this method usable pseudo-static
        # pylint: disable=R0916
        if (((self.__idx_min is not None) and (
                str.__len__(data[self.__idx_min]) > 0)) or (
                (self.__idx_mean_arith is not None) and (
                str.__len__(data[self.__idx_mean_arith]) > 0)) or (
                (self.__idx_max is not None) and (
                str.__len__(data[self.__idx_max]) > 0))):
            return self.parse_row(data)
        return None


class CsvWriter(CsvWriterBase[T]):
    """A class for CSV writing of :class:`StreamStatistics`."""

    def __init__(self,
                 data: Iterable[T],
                 scope: str | None = None,
                 n_not_needed: bool = False,
                 what_short: str | None = None,
                 what_long: str | None = None,
                 clazz: type[T] = cast("type[T]", StreamStatistics)) -> None:
        """
        Initialize the csv writer.

        :param data: the data to use
        :param scope: the prefix to be pre-pended to all columns
        :param n_not_needed: should we omit the `n` column?
        :param what_short: the short description of what the statistics is
            about
        :param what_long: the long description of what the statistics is about
        :param clazz: the stream statistics type

        >>> try:
        ...     CsvWriter([], None, n_not_needed=None)
        ... except TypeError as te:
        ...     print(te)
        n_not_needed should be an instance of bool but is None.

        >>> try:
        ...     CsvWriter([], clazz=str)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        clazz should be an i

        >>> try:
        ...     CsvWriter([])
        ... except ValueError as ve:
        ...     s = str(ve)
        ...     print(s[s.index(' ') + 1:])
        CsvWriter did not see any data.

        >>> try:
        ...     CsvWriter([1])
        ... except TypeError as te:
        ...     print(str(te)[:29])
        data[0] should be an instance
        """
        super().__init__(data, scope)

        if not issubclass(clazz, StreamStatistics):
            raise type_error(clazz, "clazz", type[StreamStatistics])
        #: the internal type
        self.__cls: Final[type[StreamStatistics]] = clazz

        if not isinstance(n_not_needed, bool):
            raise type_error(n_not_needed, "n_not_needed", bool)
        # We need to check at most three conditions to see whether we can
        # compact the output:
        # 1. If all minimum, mean, median, maximum (and geometric mean, if
        # defined) are the same, then we can collapse this column.
        all_same: bool = True
        # 2. If no geometric mean is found, then we can also omit this column.
        has_no_geom: bool = True
        # 3. If no median is found, then we can also omit this column.
        has_no_median: bool = True
        # 4. If the `n` column is not needed or if all `n=1`, then we can omit
        # it. We only need to check if n is not needed if self.n_not_needed is
        # False because otherwise, we rely on self.n_not_needed.
        # n_really_not_needed will become False if we find one situation where
        # we actually need n.
        n_really_not_needed: bool = n_not_needed
        # So if n_really_not_needed is True, we need to do 3 checks.
        # Otherwise, we only need two checks.
        checks_needed: int = 4 if n_really_not_needed else 3
        # the number of samples seen
        seen: int = 0

        for i, d in enumerate(data):  # Iterate over the data.
            if not isinstance(d, clazz):
                raise type_error(d, f"data[{i}]", clazz)
            seen += 1
            if n_really_not_needed and (d.n != 1):
                n_really_not_needed = False
                checks_needed -= 1
                if checks_needed <= 0:
                    break
            if all_same and (d.minimum < d.maximum):
                all_same = False
                checks_needed -= 1
                if checks_needed <= 0:
                    break
            if has_no_geom and (d.get_mean_geom() is not None):
                has_no_geom = False
                checks_needed -= 1
                if checks_needed <= 0:
                    break
            if has_no_median and (d.get_median() is not None):
                has_no_median = False
                checks_needed -= 1
                if checks_needed <= 0:
                    break

        if seen <= 0:
            raise ValueError(
                f"{type_name(self.__cls)} CsvWriter did not see any data.")

        # stream statistics do not have geometric means or medians
        if self.__cls is StreamStatistics:
            has_no_geom = has_no_median = True

        n_not_needed = n_really_not_needed or n_not_needed
        #: do we have a geometric mean?
        has_geo_mean: Final[bool] = (not has_no_geom) and (not all_same)
        #: do we have a median?
        has_median: Final[bool] = (not has_no_median) and (not all_same)

        #: the key for `n` is `None` if `n` is not printed, else it is the key
        self.__key_n: Final[str | None] = None if n_not_needed \
            else csv_scope(scope, KEY_N)

        key_all: str | None = None
        key_min: str | None = None
        key_mean_arith: str | None = None
        key_med: str | None = None
        key_max: str | None = None
        key_mean_geom: str | None = None
        key_sd: str | None = None

        if all_same:
            key_all = KEY_VALUE if scope is None else (
                csv_scope(scope, None if self.__key_n is None else KEY_VALUE))
        else:
            key_min = csv_scope(scope, KEY_MINIMUM)
            key_mean_arith = csv_scope(scope, KEY_MEAN_ARITH)
            if has_median:
                key_med = csv_scope(scope, KEY_MEDIAN)
            key_max = csv_scope(scope, KEY_MAXIMUM)
            if has_geo_mean:
                key_mean_geom = csv_scope(scope, KEY_MEAN_GEOM)
            key_sd = csv_scope(scope, KEY_STDDEV)

        #: the key for single values
        self.__key_all: Final[str | None] = key_all
        #: the key for minimum values
        self.__key_min: Final[str | None] = key_min
        #: the key for the arithmetic mean
        self.__key_mean_arith: Final[str | None] = key_mean_arith
        #: the key for the median
        self.__key_med: Final[str | None] = key_med
        #: the key for the geometric mean
        self.__key_mean_geom: Final[str | None] = key_mean_geom
        #: the key for the maximum value
        self.__key_max: Final[str | None] = key_max
        #: the key for the standard deviation
        self.__key_sd: Final[str | None] = key_sd

        long_name: str | None = \
            None if what_long is None else str.strip(what_long)
        short_name: str | None = \
            None if what_short is None else str.strip(what_short)
        if long_name is None:
            long_name = short_name
        elif short_name is None:
            short_name = long_name
        else:
            long_name = f"{long_name} ({short_name})"

        #: the short description of what the statistics are about
        self.__short_name: Final[str | None] = short_name
        #: the long description of what the statistics are about
        self.__long_name: Final[str | None] = long_name

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the column titles
        """
        if self.__key_n is not None:
            yield self.__key_n

        if self.__key_all is None:
            yield self.__key_min
            yield self.__key_mean_arith
            if self.__key_med is not None:
                yield self.__key_med
            if self.__key_mean_geom is not None:
                yield self.__key_mean_geom
            yield self.__key_max
            yield self.__key_sd
        else:
            yield self.__key_all

    def get_optional_row(self,
                         data: int | float | T | None,
                         n: int | None = None) -> Iterable[str]:
        """
        Attach an empty row of the correct shape to the output.

        This function may be needed in cases where the statistics are part of
        other records that sometimes do not contain the record.

        :param data: the data item
        :param n: the number of samples
        :returns: the optional row data

        >>> try:
        ...     list(CsvWriter([StreamStatistics.from_single_value(
        ...             1)]).get_optional_row("x"))
        ... except TypeError as te:
        ...     print(str(te)[:53])
        data should be an instance of any in {None, float, in
        """
        if data is None:
            # attach an empty row
            for _ in range((0 if self.__key_n is None else 1) + (
                    (4 if self.__key_mean_geom is None else 5)
                    + (0 if self.__key_med is None else 1)
                    if self.__key_all is None else 1)):
                yield ""
            return
        if isinstance(data, int | float):  # convert single value
            data = cast("T", self.__cls.from_single_value(
                data, 1 if n is None else n))
        elif not isinstance(data, StreamStatistics):  # huh?
            raise type_error(data, "data", (
                int, float, StreamStatistics, None))
        elif (n is not None) and (n != data.n):  # sanity check
            raise ValueError(f"data.n={data.n} but n={n}.")
        yield from self.get_row(data)

    def get_row(self, data: T) -> Iterable[str]:
        """
        Render a single sample statistics to a CSV row.

        :param data: the data sample statistics
        :returns: the row iterator
        """
        if self.__key_n is not None:
            yield str(data.n)
        if self.__key_all is None:
            yield num_to_str(data.minimum)
            yield num_to_str(data.mean_arith)
            if self.__key_med is not None:
                yield num_to_str(data.get_median())
            if self.__key_mean_geom is not None:
                yield num_or_none_to_str(data.get_mean_geom())
            yield num_to_str(data.maximum)
            yield num_or_none_to_str(data.stddev)
        else:
            if data.minimum != data.maximum:
                raise ValueError(f"Inconsistent data {data}.")
            yield num_to_str(data.minimum)

    def get_header_comments(self) -> Iterable[str]:
        """
        Get any possible header comments.

        :returns: the iterable of header comments
        """
        return [f"Statistics about {self.__long_name}."]\
            if (self.scope is not None) and (self.__long_name is not None)\
            else ()

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get any possible footer comments.

        :returns: the footer comments
        """
        long_name: str | None = self.__long_name
        long_name = "" if long_name is None else f" {long_name}"
        short_name: str | None = self.__short_name
        short_name = "" if short_name is None else f" {short_name}"
        name: str = long_name
        first: bool = True

        scope: Final[str] = self.scope
        if (scope is not None) and (
                (self.__key_n is not None) or (
                self.__key_all is not None)):
            if first:
                yield ""
                first = False
            yield (f"All{name} sample statistics start with "
                   f"{(scope + SCOPE_SEPARATOR)!r}.")
            name = short_name

        if self.__key_n is not None:
            if first:
                yield ""
                first = False
            yield f"{self.__key_n}: the number of{name} samples"
            name = short_name
        if self.__key_all is None:
            if first:
                yield ""
            n_name: str | None = self.__key_n
            if n_name is None:
                n_name = KEY_N
            yield f"{self.__key_min}: the smallest encountered{name} value"
            name = short_name
            yield (f"{self.__key_mean_arith}: the arithmetic mean of all the"
                   f"{name} values, i.e., the sum of the values divided by "
                   f"their number {n_name}")
            if self.__key_med is not None:
                yield (f"{self.__key_med}: the median of all the{name} "
                       "values, which can be computed by sorting the values "
                       "and then picking the value in the middle of the "
                       f"sorted list (in case of an odd number {n_name} of "
                       "values) or the arithmetic mean (half the sum) of the "
                       "two values in the middle (in case of an even number "
                       f"{n_name})")
            if self.__key_mean_geom is not None:
                yield (f"{self.__key_mean_geom}: the geometric mean of all the"
                       f" {name} values, i.e., the {n_name}-th root of the "
                       f"product of all values, which is only defined if all "
                       f"values are > 0")
            yield f"{self.__key_max}: the largest encountered{name} value"
            yield (f"{self.__key_sd}: the standard deviation of the{name} "
                   "values, which is a measure of spread: the larger it "
                   "is, the farther are the values distributed away from "
                   f"the arithmetic mean {self.__key_mean_arith}. It can be "
                   "computed as the ((sum of squares) - (square of the sum)"
                   f" / {n_name}) / ({n_name} - 1) of all{name} values.")
        else:
            if first:
                yield ""
            yield f"{self.__key_all}: all{name} samples have this value"

    def get_footer_bottom_comments(self) -> Iterable[str] | None:
        """
        Get the bottom footer comments.

        :returns: an iterator with the bottom comments

        >>> for p in CsvWriter([StreamStatistics(
        ...     1, 1, 1, 1, None)]).get_footer_bottom_comments():
        ...         print(p[:30])
        This CSV output has been creat
        Statistics were computed using
        You can find pycommons at http
        """
        yield from pycommons_footer_bottom_comments(
            self, ("Statistics were computed using pycommons."
                   f"math in mode {type_name(self.__cls)}."))
