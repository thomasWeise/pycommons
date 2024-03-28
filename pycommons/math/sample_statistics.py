"""A simple and immutable basic statistics record."""

from contextlib import suppress
from dataclasses import dataclass
from math import gcd, inf, isfinite, log2, nextafter, sqrt
from statistics import geometric_mean as stat_geomean
from statistics import mean as stat_mean
from statistics import stdev as stat_stddev
from typing import Final, Iterable

from pycommons.math.int_math import try_int, try_int_div
from pycommons.types import check_int_range, type_error


@dataclass(frozen=True, init=False, order=False, eq=True, unsafe_hash=True)
class SampleStatistics:
    """An immutable record with sample statistics of one quantity."""

    #: The sample size
    n: int
    #: The minimum.
    minimum: int | float
    #: The median.
    median: int | float
    #: The arithmetic mean value.
    mean_arith: int | float
    #: The geometric mean value, if defined.
    mean_geom: int | float | None
    #: The maximum.
    maximum: int | float
    #: The standard deviation.
    stddev: int | float | None

    def __init__(self, n: int, minimum: int | float, median: int | float,
                 mean_arith: int | float, mean_geom: int | float | None,
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

        >>> s1 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s1.n
        2
        >>> s1.minimum
        1
        >>> s1.median
        2
        >>> s1.mean_arith
        4
        >>> s1.mean_geom
        3
        >>> s1.maximum
        6
        >>> s1.stddev
        0.2
        >>> hash(s1)
        1256902036954760112

        >>> s2 = SampleStatistics(1, 0, 0.0, 0, None, 0.0, None)
        >>> s2.n
        1
        >>> s2.minimum
        0
        >>> s2.median
        0
        >>> s2.mean_arith
        0
        >>> print(s2.mean_geom)
        None
        >>> s2.maximum
        0
        >>> print(s2.stddev)
        None
        >>> hash(s2) == hash((1, 0, 0, 0, None, 0, None))
        True

        >>> s3 = SampleStatistics(n=3, minimum=5, median=5, maximum=5,
        ...                       mean_arith=5, mean_geom=5, stddev=0.0)
        >>> s3.stddev
        0
        >>> hash(s3)
        1693271975867638638

        >>> sset = {s1, s1, s2, s1, s3, s3, s2, s1}
        >>> len(sset)
        3
        >>> print(list(sss.n for sss in sorted(sset)))
        [1, 2, 3]
        >>> print(list(sss.minimum for sss in sorted(sset)))
        [0, 1, 5]

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=6, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        median (6) must equal minimum (5) if n=1.

        >>> try:
        ...     SampleStatistics(n=2, minimum=5, median=4, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        median (4) must be >= minimum (5) if n>1.

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=5, maximum=6,
        ...                      mean_arith=5, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        maximum (6) must equal minimum (5) if n=1.

        >>> try:
        ...     SampleStatistics(n=2, minimum=5, median=6, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        maximum (5) must be >= med (6) if n>1.

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=5, maximum=5,
        ...                      mean_arith=4, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        mean_arith (4) must equal minimum (5) if n=1.

        >>> try:
        ...     SampleStatistics(n=2, minimum=5, median=6, maximum=6,
        ...                      mean_arith=4, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        minimum<=mean_arith<=maximum must hold, but got 5, 4, and 6.

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=5, maximum=5,
        ...                      mean_arith=5, mean_geom=None, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        If minimum (5) > 0, then mean_geom must be defined, but it is None.

        >>> try:
        ...     SampleStatistics(n=1, minimum=0, median=0, maximum=0,
        ...                      mean_arith=0, mean_geom=0, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        If minimum (0) <= 0, then mean_geom is undefined, but it is 0.

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=5, maximum=5,
        ...                      mean_arith=5, mean_geom=6, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        mean_geom (6) must equal minimum (5) if n=1.

        >>> try:
        ...     SampleStatistics(n=3, minimum=5, median=6, maximum=7,
        ...                      mean_arith=6, mean_geom=6.1, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        mean_geom (6.1) must be <= mean_arith (6).

        >>> try:
        ...     SampleStatistics(n=3, minimum=5, median=6, maximum=7,
        ...                      mean_arith=6, mean_geom=6, stddev=-1)
        ... except ValueError as ve:
        ...     print(ve)
        stddev must be >= 0, but is -1.

        >>> try:
        ...     SampleStatistics(n=3, minimum=5, median=6, maximum=7,
        ...                      mean_arith=6, mean_geom=6, stddev=0)
        ... except ValueError as ve:
        ...     print(str(ve)[:59])
        If stddev (0) is 0, then minimum (5) must equal maximum (7)

        >>> try:
        ...     SampleStatistics(n=3, minimum=5, median=5, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=1)
        ... except ValueError as ve:
        ...     print(str(ve)[:59])
        If stddev (1) is 0, then minimum (5) must equal maximum (5)

        >>> try:
        ...     SampleStatistics(n=3, minimum=5, median=5, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=None)
        ... except ValueError as ve:
        ...     print(ve)
        If n=1, stddev=None and vice versa, but got n=3 and stddev=None.

        >>> try:
        ...     SampleStatistics(n=1, minimum=5, median=5, maximum=5,
        ...                      mean_arith=5, mean_geom=5, stddev=1)
        ... except ValueError as ve:
        ...     print(ve)
        If n=1, stddev=None and vice versa, but got n=1 and stddev=1.

        >>> try:
        ...     SampleStatistics(n=2, minimum=5, median=5, maximum=6,
        ...                      mean_arith=6, mean_geom=7, stddev=1)
        ... except ValueError as ve:
        ...     print(ve)
        minimum<=mean_geom<=maximum must hold, but got 5, 7, and 6.
        """
        n = check_int_range(n, "n", 1)

        # check minimum
        minimum = try_int(minimum)
        median = try_int(median)
        if n == 1:
            if median != minimum:
                raise ValueError(f"median ({median}) must equal "
                                 f"minimum ({minimum}) if n=1.")
        elif median < minimum:
            raise ValueError(
                f"median ({median}) must be >= minimum ({minimum}) if n>1.")

        # check maximum
        maximum = try_int(maximum)
        if n == 1:
            if maximum != minimum:
                raise ValueError(f"maximum ({maximum}) must equal "
                                 f"minimum ({minimum}) if n=1.")
        elif maximum < median:
            raise ValueError(
                f"maximum ({maximum}) must be >= med ({median}) if n>1.")

        # check arithmetic mean
        mean_arith = try_int(mean_arith)
        if n == 1:
            if mean_arith != minimum:
                raise ValueError(f"mean_arith ({mean_arith}) must equal "
                                 f"minimum ({minimum}) if n=1.")
        elif not (minimum <= mean_arith <= maximum):
            raise ValueError("minimum<=mean_arith<=maximum must hold, but "
                             f"got {minimum}, {mean_arith}, and {maximum}.")

        # check geometric mean
        if mean_geom is None:
            if minimum > 0:
                raise ValueError(
                    f"If minimum ({minimum}) > 0, then mean_geom must be "
                    f"defined, but it is {mean_geom}.")
        else:
            if minimum <= 0:
                raise ValueError(
                    f"If minimum ({minimum}) <= 0, then mean_geom is "
                    f"undefined, but it is {mean_geom}.")
            mean_geom = try_int(mean_geom)
            if n == 1:
                if mean_geom != minimum:
                    raise ValueError(f"mean_geom ({mean_geom}) must equal "
                                     f"minimum ({minimum}) if n=1.")
            else:
                if not (minimum <= mean_geom <= maximum):
                    raise ValueError(
                        "minimum<=mean_geom<=maximum must hold, but "
                        f"got {minimum}, {mean_geom}, and {maximum}.")
                if mean_geom > mean_arith:
                    raise ValueError(
                        f"mean_geom ({mean_geom}) must be <= "
                        f"mean_arith ({mean_arith}).")

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
        object.__setattr__(self, "median", median)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "mean_arith", mean_arith)
        object.__setattr__(self, "mean_geom", mean_geom)
        object.__setattr__(self, "stddev", stddev)

    def min_mean(self) -> int | float:
        """
        Obtain the smallest of the three mean values.

        :return: the smallest of `mean_arith`, `mean_geom`, and `median`

        >>> SampleStatistics(1, 0, 0.0, 0, None, 0.0, None).min_mean()
        0
        >>> SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2).min_mean()
        2
        >>> SampleStatistics(2, 1, 3.2, 4.0, 3, 6, 0.2).min_mean()
        3
        >>> SampleStatistics(2, 1, 5.2, 4.0, 3, 6, 0.2).min_mean()
        3
        """
        if self.mean_geom is None:  # geometric mean is always <= arithmean
            return min(self.mean_arith, self.median)
        return min(self.mean_geom, self.median)

    def max_mean(self) -> int | float:
        """
        Obtain the largest of the three mean values.

        :return: the largest of `mean_arith`, `mean_geom`, and `median`

        >>> SampleStatistics(1, 0, 0.0, 0, None, 0.0, None).max_mean()
        0
        >>> SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2).max_mean()
        4
        >>> SampleStatistics(2, 1, 3.2, 4.0, 3, 6, 0.2).max_mean()
        4
        >>> SampleStatistics(2, 1, 5.2, 4.0, 3, 6, 0.2).max_mean()
        5.2
        """
        return max(self.mean_arith, self.median)

    def __key(self) -> tuple[float | int, float | int, float | int,
                             float | int, float | int, float | int, int]:
        r"""
        Get a comparison key.

        :return: the comparison key

        >>> SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)._SampleStatistics__key()
        (1, 2, 4, 3, 6, 0.2, 2)

        >>> SampleStatistics(1, 0, 0, 0, None, 0, None)\
        ...     ._SampleStatistics__key()
        (0, 0, 0, inf, 0, inf, 1)
        """
        return (self.minimum, self.median, self.mean_arith,
                inf if self.mean_geom is None else self.mean_geom,
                self.maximum, inf if self.stddev is None else self.stddev,
                self.n)

    def __lt__(self, other: "SampleStatistics") -> bool:
        """
        Check if this object is less than another one.

        :param other: the other sample statistics
        :return: `True` if this object is less, `False` otherwise

        >>> s1 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s2 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s1 < s2
        False

        >>> s3 = SampleStatistics(2, 0.5, 2, 4.0, 3, 6, 0.2)
        >>> s3 < s1
        True
        >>> s1 < s3
        False

        >>> try:
        ...     s3 < 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        other should be an instance of pycommons.math.sample_statist
        """
        if isinstance(other, SampleStatistics):
            return self.__key() < other.__key()
        raise type_error(other, "other", SampleStatistics)

    def __le__(self, other: "SampleStatistics") -> bool:
        """
        Check if this object is less than or equal to another one.

        :param other: the other sample statistics
        :return: `True` if this object is less or equal, `False` otherwise

        >>> s1 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s2 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s1 <= s2
        True

        >>> s3 = SampleStatistics(2, 0.5, 2, 4.0, 3, 6, 0.2)
        >>> s3 <= s1
        True
        >>> s1 <= s3
        False

        >>> try:
        ...     s3 <= 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        other should be an instance of pycommons.math.sample_statist
        """
        if isinstance(other, SampleStatistics):
            return self.__key() <= other.__key()
        raise type_error(other, "other", SampleStatistics)

    def __gt__(self, other: "SampleStatistics") -> bool:
        """
        Check if this object is greater than another one.

        :param other: the other sample statistics
        :return: `True` if this object is greater, `False` otherwise

        >>> s1 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s2 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s1 > s2
        False

        >>> s3 = SampleStatistics(2, 0.5, 2, 4.0, 3, 6, 0.2)
        >>> s3 > s1
        False
        >>> s1 > s3
        True

        >>> try:
        ...     s3 > 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        other should be an instance of pycommons.math.sample_statist
        """
        if isinstance(other, SampleStatistics):
            return self.__key() > other.__key()
        raise type_error(other, "other", SampleStatistics)

    def __ge__(self, other: "SampleStatistics") -> bool:
        """
        Check if this object is greater than or equal to another one.

        :param other: the other sample statistics
        :return: `True` if this object is greater or equal, `False` otherwise

        >>> s1 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s2 = SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)
        >>> s1 >= s2
        True

        >>> s3 = SampleStatistics(2, 0.5, 2, 4.0, 3, 6, 0.2)
        >>> s3 >= s1
        False
        >>> s1 >= s3
        True

        >>> try:
        ...     s3 >= 23
        ... except TypeError as te:
        ...     print(str(te)[:60])
        other should be an instance of pycommons.math.sample_statist
        """
        if isinstance(other, SampleStatistics):
            return self.__key() >= other.__key()
        raise type_error(other, "other", SampleStatistics)


def __mean_of_two(a: int | float, b: int | float) -> int | float:
    """
    Compute the mean of two numbers.

    :param a: the first number
    :param b: the second number
    :return: the mean

    >>> __mean_of_two(1, 1)
    1
    >>> __mean_of_two(1.0, 1.0)
    1
    >>> __mean_of_two(1, 2)
    1.5
    >>> __mean_of_two(1, 3)
    2
    >>> __mean_of_two(1.5, 1.7)
    1.6

    >>> __mean_of_two(-1, -1)
    -1
    >>> __mean_of_two(-1.0, -1.0)
    -1
    >>> __mean_of_two(-1, -2)
    -1.5
    >>> __mean_of_two(-1, -3)
    -2
    >>> __mean_of_two(-1.5, -1.7)
    -1.6

    >>> __mean_of_two(1, -1)
    0
    >>> __mean_of_two(-1.0, 1.0)
    0
    >>> __mean_of_two(1, -2)
    -0.5
    >>> __mean_of_two(1, -3)
    -1
    >>> __mean_of_two(1.5, -1.7)
    -0.09999999999999998
    >>> __mean_of_two(-1.5, 1.7)
    0.09999999999999998

    >>> __mean_of_two(1.7976931348623157e+308, 1.7976931348623157e+308)
    1.7976931348623157e+308
    >>> __mean_of_two(1.7976931348623155e+308, 1.7976931348623157e+308)
    1.7976931348623155e+308
    """
    a = try_int(a)
    b = try_int(b)
    if a == b:
        return a
    if isinstance(a, int) and isinstance(b, int):
        int_res: int = a + b
        int_res_sr: Final[int] = int_res >> 1
        return int_res_sr + 0.5 if (int_res & 1) != 0 else int_res_sr
    res: float = a + b
    return (0.5 * res) if isfinite(res) else ((0.5 * a) + (0.5 * b))


def from_sample(source: Iterable[int | float]) -> SampleStatistics:
    """
    Create a statistics object from an iterable.

    :param source: the source
    :return: a statistics representing the statistics over `source`

    >>> s = from_sample([0.0])
    >>> s.n
    1
    >>> s.minimum
    0
    >>> s.maximum
    0
    >>> print(s.mean_geom)
    None
    >>> s.median
    0
    >>> print(s.stddev)
    None

    >>> s = from_sample([1.0])
    >>> s.n
    1
    >>> s.minimum
    1
    >>> s.maximum
    1
    >>> print(s.mean_geom)
    1
    >>> s.median
    1
    >>> print(s.stddev)
    None

    >>> s = from_sample([1.0, 1])
    >>> s.n
    2
    >>> s.minimum
    1
    >>> s.maximum
    1
    >>> print(s.mean_geom)
    1
    >>> s.median
    1
    >>> print(s.stddev)
    0

    >>> s = from_sample([0, 0.0])
    >>> s.n
    2
    >>> s.minimum
    0
    >>> s.maximum
    0
    >>> print(s.mean_geom)
    None
    >>> s.median
    0
    >>> print(s.stddev)
    0

    >>> dd = [1.5, 2.5]
    >>> s = from_sample(dd)
    >>> s.n
    2
    >>> s.minimum
    1.5
    >>> s.maximum
    2.5
    >>> print(s.mean_geom)
    1.9364916731037085
    >>> stat_geomean(dd)
    1.9364916731037085
    >>> s.median
    2
    >>> print(s.stddev)
    0.7071067811865476
    >>> stat_stddev(dd)
    0.7071067811865476

    >>> dd = [1.0, 2.0]
    >>> s = from_sample(dd)
    >>> s.n
    2
    >>> s.minimum
    1
    >>> s.maximum
    2
    >>> print(s.mean_geom)
    1.4142135623730951
    >>> (1 * 2) ** 0.5
    1.4142135623730951
    >>> stat_geomean(dd)
    1.414213562373095
    >>> s.median
    1.5
    >>> print(s.stddev)
    0.7071067811865476
    >>> stat_stddev(dd)
    0.7071067811865476

    >>> dd = [1.0, 2.0, 3.0]
    >>> s = from_sample(dd)
    >>> s.n
    3
    >>> s.minimum
    1
    >>> s.maximum
    3
    >>> print(s.mean_geom)
    1.8171205928321397
    >>> (1 * 2 * 3) ** (1 / 3)
    1.8171205928321397
    >>> stat_geomean(dd)
    1.8171205928321397
    >>> s.median
    2
    >>> print(s.stddev)
    1
    >>> stat_stddev(dd)
    1.0

    >>> dd = [1.0, 0, 3.0]
    >>> s = from_sample(dd)
    >>> s.n
    3
    >>> s.minimum
    0
    >>> s.maximum
    3
    >>> print(s.mean_geom)
    None
    >>> s.median
    1
    >>> print(s.stddev)
    1.5275252316519468
    >>> stat_stddev(dd)
    1.5275252316519468

    >>> dd = [1.0, -2, 3.0]
    >>> s = from_sample(dd)
    >>> s.n
    3
    >>> s.minimum
    -2
    >>> s.maximum
    3
    >>> print(s.mean_geom)
    None
    >>> s.median
    1
    >>> print(s.stddev)
    2.516611478423583
    >>> stat_stddev(dd)
    2.516611478423583

    >>> dd = [1e5, 2e7, 3e9]
    >>> s = from_sample(dd)
    >>> s.n
    3
    >>> s.minimum
    100000
    >>> s.maximum
    3000000000
    >>> print(s.mean_geom)
    18171205.92832138
    >>> (100000 * 20000000 * 3000000000) ** (1 / 3)
    18171205.92832138
    >>> s.median
    20000000
    >>> print(s.stddev)
    1726277112.7487035
    >>> stat_stddev(dd)
    1726277112.7487035

    >>> dd = [3.3, 2.5, 3.7, 4.9]
    >>> s = from_sample(dd)
    >>> s.n
    4
    >>> s.minimum
    2.5
    >>> s.maximum
    4.9
    >>> print(s.mean_geom)
    3.497139351921697
    >>> (3.3 * 2.5 * 3.7 * 4.9) ** 0.25
    3.497139351921697
    >>> s.median
    3.5
    >>> print(s.stddev)
    1.0000000000000002
    >>> stat_stddev(dd)
    1.0000000000000002

    >>> s = from_sample([3, 1, 2, 5])
    >>> print(s.minimum)
    1
    >>> print(s.maximum)
    5
    >>> print(s.mean_arith)
    2.75
    >>> print(s.median)
    2.5
    >>> print(f"{s.mean_geom:.4f}")
    2.3403
    >>> print(f"{s.min_mean():.4f}")
    2.3403
    >>> print(f"{s.max_mean()}")
    2.75

    >>> try:
    ...     from_sample(None)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is None.

    >>> try:
    ...     from_sample(1)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     from_sample([])
    ... except ValueError as ve:
    ...     print(ve)
    Data source cannot be empty.
    """
    if not isinstance(source, Iterable):
        raise type_error(source, "source", Iterable)

    # The median function of statistics would do this anyway, so we may as
    # well do it now.
    data: Final[list[int | float]] = sorted(map(try_int, source))
    n: Final[int] = list.__len__(data)
    if n <= 0:
        raise ValueError("Data source cannot be empty.")

    minimum: int | float = data[0]  # because data is now sorted
    maximum: int | float = data[-1]  # because data is now sorted
    if (minimum >= maximum) or (n <= 1):  # all data is the same
        return SampleStatistics(
            n=n, minimum=minimum, median=minimum, mean_arith=minimum,
            mean_geom=None if minimum <= 0 else minimum, maximum=minimum,
            stddev=None if n <= 1 else 0)

    # Go over the data once and see if we can treat it as all-integer.
    # If yes, then we can compute some statistics very precisely.
    can_int: bool = True  # are all values integers?
    int_sum: int = 0  # the integer sum (for mean, stddev)
    int_prod: int = 1  # the integer product (for geom_mean)
    int_sum_sqr: int = 0  # the sum of squares (for stddev)
    for e in data:  # iterate over all data
        if not isinstance(e, int):
            can_int = False
            break
        int_sum += e  # so we can sum exactly
        int_prod *= e  # and can compute exact products
        int_sum_sqr += e * e  # and compute the sum of squares

    mean_arith: int | float | None = __mean_of_two(
        data[0], data[1]) if n == 2 else None
    mean_geom: int | float | None = None
    stddev: int | float | None = None
    if can_int:
        if stddev is None:
            int_sum2: int = int_sum * int_sum
            i_gcd: Final[int] = gcd(int_sum2, n)
            int_sum2 = int_sum2 // i_gcd
            i_n: Final[int] = n // i_gcd

            var: int | float  # the container for the variance
            var = try_int_div(int_sum_sqr - int_sum2, n - 1) \
                if i_n == 1 else \
                ((int_sum_sqr - (int_sum2 / i_n)) / (n - 1))

            stddev_test: Final[float] = sqrt(var)
            if stddev_test > 0:
                stddev = stddev_test

        if minimum > 0:  # geometric mean only defined for all-positive
            with suppress(BaseException):
                mean_geom_test = 2 ** try_int(log2(int_prod) / n)
                if isfinite(mean_geom_test) and (
                        minimum <= mean_geom_test < maximum):
                    mean_geom = mean_geom_test

        if mean_arith is None:
            mean_arith = try_int_div(int_sum, n)

    if mean_arith is None:
        mean_arith = stat_mean(data)
    if stddev is None:
        stddev = stat_stddev(data)
    if (mean_geom is None) and (minimum > 0):
        mean_geom = stat_geomean(data)

    if mean_geom is not None:
        # Deal with errors that may have arisen due to
        # numerical imprecision.
        if (mean_geom < minimum) and (nextafter(
                mean_geom, inf) >= nextafter(minimum, -inf)):
            mean_geom = minimum
        if (mean_geom > mean_arith) and ((nextafter(
                mean_arith, inf) >= nextafter(mean_geom, -inf)) or (
                (0.9999999999999 * mean_geom) <= mean_arith)):
            mean_geom = mean_arith

    # compute the median
    middle: Final[int] = n >> 1
    median: Final[int | float] = data[middle] if (n & 1) == 1 else (
        __mean_of_two(data[middle - 1], data[middle]))

    return SampleStatistics(minimum=minimum, median=median,
                            mean_arith=mean_arith, mean_geom=mean_geom,
                            maximum=maximum, stddev=stddev, n=n)
