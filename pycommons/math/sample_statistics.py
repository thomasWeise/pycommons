"""A simple and immutable basic statistics record."""

from contextlib import suppress
from dataclasses import dataclass
from math import gcd, inf, isfinite, log2, nextafter, sqrt
from statistics import geometric_mean as stat_geomean
from statistics import mean as stat_mean
from statistics import stdev as stat_stddev
from typing import Callable, Final, Iterable, cast

from pycommons.io.csv import (
    CSV_SEPARATOR,
    SCOPE_SEPARATOR,
    csv_column,
    csv_column_or_none,
    csv_scope,
    csv_val_or_none,
    pycommons_footer_bottom_comments,
)
from pycommons.math.int_math import (
    __DBL_INT_LIMIT_P_I,
    try_float_int_div,
    try_int,
    try_int_add,
    try_int_div,
    try_int_mul,
    try_int_sqrt,
)
from pycommons.strings.string_conv import (
    num_or_none_to_str,
    num_to_str,
    str_to_num,
)
from pycommons.types import check_int_range, type_error

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


@dataclass(frozen=True, init=False, order=False, eq=True, unsafe_hash=True)
class SampleStatistics:
    """An immutable record with sample statistics of one quantity."""

    #: The number of data samples over which the statistics were computed.
    n: int
    #: The minimum, i.e., the value of the smallest among the :attr:`~n` data
    #: samples.
    minimum: int | float
    #: The median, i.e., the value in the middle of the sorted list of
    #: :attr:`~n` data samples.
    median: int | float
    #: The arithmetic mean value, i.e., the sum of the :attr:`~n` data samples
    #: divided by :attr:`~n`.
    mean_arith: int | float
    #: The geometric mean value, if defined. This is the :attr:`~n`-th root of
    #: the product of all data samples. This value will be `None` if there
    #: was any sample which is not greater than 0.
    mean_geom: int | float | None
    #: The maximum, i.e., the value of the largest among the :attr:`~n` data
    #: samples.
    maximum: int | float
    #: The standard deviation, if defined. This value will be `None` if there
    #: was only a single sample.
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
        n = check_int_range(n, "n", 1, 2 << 62)

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

    def __str__(self) -> str:
        """
        Get a string representation of this object.

        :return: the string
        """
        return CSV_SEPARATOR.join(map(str, (
            self.n, self.minimum, self.median, self.mean_arith,
            self.mean_geom, self.maximum, self.stddev)))

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

    def compact(self, needs_n: bool = True) \
            -> "int | float | SampleStatistics":
        """
        Try to represent this object as single number, if possible.

        :param needs_n: if this is `True`, the default, then the object is
            only turned into a single number if alsp `n==1`. Otherwise, `n`
            is ignored
        :return: an integer or float if this objects minimum equals its
            maximum, the object itself otherwise

        >>> s = from_single_value(10, 1)
        >>> s.compact() == 10
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = from_single_value(10, 2)
        >>> s.compact() is s
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = from_single_value(10, 2)
        >>> s.compact(False) == 10
        True

        >>> s = SampleStatistics(2, 1, 2, 4, 3, 5, 3)
        >>> s.compact() is s
        True

        >>> s = SampleStatistics(2, 1, 2, 4, 3, 5, 3)
        >>> s.compact(False) is s
        True

        >>> try:
        ...     s.compact(1)
        ... except TypeError as te:
        ...     print(te)
        needs_n should be an instance of bool but is int, namely '1'.

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

    def get_n(self) -> int:
        """
        Get the number :attr:`~n` of samples.

        :return: the number :attr:`~n` of samples.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_n()
        5

        >>> try:
        ...     SampleStatistics.get_n(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.n

    def get_minimum(self) -> int | float:
        """
        Get the :attr:`~minimum` of all the samples.

        :return: the :attr:`~minimum` of all the samples
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_minimum()
        3

        >>> try:
        ...     SampleStatistics.get_minimum(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.minimum

    def get_maximum(self) -> int | float:
        """
        Get the :attr:`~maximum` of all the samples.

        :return: the :attr:`~maximum` of all the samples
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_maximum()
        7

        >>> try:
        ...     SampleStatistics.get_maximum(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.maximum

    def get_mean_arith(self) -> int | float:
        """
        Get the arithmetic mean (:attr:`~mean_arith`) of all the samples.

        :return: the arithmetic mean (:attr:`~mean_arith`) of all the samples.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_mean_arith()
        6

        >>> try:
        ...     SampleStatistics.get_mean_arith(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.mean_arith

    def get_mean_geom(self) -> int | float | None:
        """
        Get the geometric mean (:attr:`~mean_geom`) of all the samples.

        :return: the geometric mean (:attr:`~mean_geom`) of all the samples,
            `None` if the geometric mean is not defined.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_mean_geom()
        4

        >>> try:
        ...     SampleStatistics.get_mean_geom(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.mean_geom

    def get_median(self) -> int | float:
        """
        Get the :attr:`~median` of all the samples.

        :return: the :attr:`~median` of all the samples.
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_median()
        5

        >>> try:
        ...     SampleStatistics.get_median(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.median

    def get_stddev(self) -> int | float | None:
        """
        Get the standard deviation mean (:attr:`~stddev`) of all the samples.

        :return: the standard deviation (:attr:`~stddev`) of all the samples,
            `None` if the standard deviation is not defined, i.e., if there is
            only a single sample
        :raises TypeError: if an object of the wrong type is passed in as self

        >>> SampleStatistics(5, 3, 5, 6, 4, 7, 2).get_stddev()
        2

        >>> try:
        ...     SampleStatistics.get_stddev(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        self should be an in
        """
        if not isinstance(self, SampleStatistics):
            raise type_error(self, "self", SampleStatistics)
        return self.stddev


#: the internal map of property names to getters
__PROPERTIES: Final[Callable[[str, None], Callable[[
    SampleStatistics], int | float | None] | None]] = {
    KEY_N: SampleStatistics.get_n,
    KEY_MINIMUM: SampleStatistics.get_minimum,
    "minimum": SampleStatistics.get_minimum,
    KEY_MEAN_ARITH: SampleStatistics.get_mean_arith,
    "mean_arith": SampleStatistics.get_mean_arith,
    "arithmetic mean": SampleStatistics.get_mean_arith,
    "average": SampleStatistics.get_mean_arith,
    KEY_MEDIAN: SampleStatistics.get_median,
    "median": SampleStatistics.get_median,
    KEY_MEAN_GEOM: SampleStatistics.get_mean_geom,
    "mean_geom": SampleStatistics.get_mean_geom,
    "geometric mean": SampleStatistics.get_mean_geom,
    "gmean": SampleStatistics.get_mean_geom,
    KEY_MAXIMUM: SampleStatistics.get_maximum,
    "maximum": SampleStatistics.get_maximum,
    KEY_STDDEV: SampleStatistics.get_stddev,
    "stddev": SampleStatistics.get_stddev,
    "standard deviation": SampleStatistics.get_stddev,
}.get


def getter(dimension: str) -> Callable[
        [SampleStatistics], int | float | None]:
    """
    Get a function returning the dimension from :class:`SampleStatistics`.

    :param dimension: the dimension
    :returns: a :class:`Callable` that returns the value corresponding to the
        dimension
    :raises TypeError: if `dimension` is not a string
    :raises ValueError: if `dimension` is unknown

    >>> getter(KEY_N) is SampleStatistics.get_n
    True
    >>> getter(KEY_MINIMUM) is SampleStatistics.get_minimum
    True
    >>> getter(KEY_MEAN_ARITH) is SampleStatistics.get_mean_arith
    True
    >>> getter(KEY_MEDIAN) is SampleStatistics.get_median
    True
    >>> getter(KEY_MEAN_GEOM) is SampleStatistics.get_mean_geom
    True
    >>> getter(KEY_MAXIMUM) is SampleStatistics.get_maximum
    True
    >>> getter(KEY_STDDEV) is SampleStatistics.get_stddev
    True

    >>> s = SampleStatistics(5, 3, 5, 6, 4, 7, 2)
    >>> getter(KEY_N)(s)
    5
    >>> getter(KEY_MINIMUM)(s)
    3
    >>> getter(KEY_MEAN_ARITH)(s)
    6
    >>> getter(KEY_MEDIAN)(s)
    5
    >>> getter(KEY_MEAN_GEOM)(s)
    4
    >>> getter(KEY_MAXIMUM)(s)
    7
    >>> getter(KEY_STDDEV)(s)
    2

    >>> try:
    ...     getter(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     getter(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     getter("hello")
    ... except ValueError as ve:
    ...     print(ve)
    Unknown SampleStatistics dimension 'hello'.
    """
    result: Callable[[SampleStatistics], int | float | None] | None = \
        __PROPERTIES(str.strip(dimension), None)
    if result is None:
        raise ValueError(f"Unknown SampleStatistics dimension {dimension!r}.")
    return result


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
        return try_int_div(a + b, 2)

    res: float = a + b
    return (0.5 * res) if isfinite(res) else ((0.5 * a) + (0.5 * b))


def __almost_le(a: int | float, b: int | float) -> bool:
    """
    Check if `a <= b` holds approximately.

    :param a: the first value
    :param b: the second value
    :return: `True` if we can say: `a` is approximately less or equal than `b`
        and any deviation from this probably results from numerical issues.

    >>> __almost_le(1, 0)
    False
    >>> __almost_le(0, 0)
    True
    >>> __almost_le(1.1, 1.09)
    False
    >>> __almost_le(1.1, 1.099999)
    False
    >>> __almost_le(1.1, 1.09999999)
    False
    >>> __almost_le(1.1, 1.0999999999)
    False
    >>> __almost_le(1.1, 1.099999999999)
    False
    >>> __almost_le(1.099999999999, 1.1)
    True
    >>> __almost_le(1.1, 1.0999999999999)
    True
    >>> __almost_le(1.0999999999999, 1.1)
    True

    >>> __almost_le(0, -1)
    False
    >>> __almost_le(-1.09, -1.1)
    False
    >>> __almost_le(-1.099999, -1.1)
    False
    >>> __almost_le(-1.09999999, -1.1)
    False
    >>> __almost_le(-1.0999999999, -1.1)
    False
    >>> __almost_le(-1.099999999999, -1.1)
    False
    >>> __almost_le(-1.1, -1.099999999999)
    True
    >>> __almost_le(-1.0999999999999, -1.1)
    True
    >>> __almost_le(-1.1, -1.0999999999999)
    True

    >>> __almost_le(23384026197294446691258957323460528314494920687616,
    ...             2.3384026197294286e+49)
    True
    >>> __almost_le(nextafter(5, inf), nextafter(5, -inf))
    True
    >>> __almost_le(nextafter(nextafter(5, inf), inf),
    ...             nextafter(nextafter(5, -inf), -inf))
    True
    >>> __almost_le(nextafter(nextafter(nextafter(5, inf), inf), inf),
    ...             nextafter(nextafter(nextafter(5, -inf), -inf), -inf))
    True
    >>> __almost_le(nextafter(nextafter(nextafter(nextafter(5, inf), inf),
    ...             inf), inf), nextafter(nextafter(nextafter(5, -inf),
    ...             -inf), -inf))
    True
    >>> __almost_le(5.114672824837722e+148, 5.1146728248374894e+148)
    True
    """
    if a <= b:
        return True

    if a < 0:
        if b >= 0:
            return False
        a, b = -b, -a
    elif b <= 0:
        return False

    if (a <= 0) != (b <= 0):
        return False

    with suppress(OverflowError):
        use_a: int | float = a
        use_b: int | float = b
        for _ in range(3):
            use_a = nextafter(use_a, -inf)
            use_b = nextafter(use_b, inf)
            if use_a <= use_b:
                return True
    try:
        return (b / a) > 0.9999999999999
    except OverflowError:
        a_int: Final[int] = int(a)
        b_int: Final[int] = int(b)
        if (a_int <= 0) or (b_int <= 0):
            return False
        with suppress(OverflowError):
            return (b_int / a_int) > 0.9999999999999
    return False


def from_single_value(value: int | float | SampleStatistics, n: int = 1) \
        -> SampleStatistics:
    r"""
    Create a sample statistics from a single number.

    :param value: the single value
    :param n: the number of samples, i.e., the number of times this value
        occurred
    :return: the sample statistics

    >>> s = from_single_value(10, 2)
    >>> print(s.stddev)
    0
    >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
    ...     == s.median == 10
    True
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(10, 1)
    >>> print(s.stddev)
    None
    >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
    ...     == s.median == 10
    True
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(-10, 2)
    >>> print(s.stddev)
    0
    >>> s.minimum == s.maximum == s.mean_arith == s.median == -10
    True
    >>> print(s.mean_geom)
    None
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(-10, 1)
    >>> print(s.stddev)
    None
    >>> s.minimum == s.maximum == s.mean_arith == s.median == -10
    True
    >>> print(s.mean_geom)
    None
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(10.5, 2)
    >>> print(s.stddev)
    0
    >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
    ...     == s.median == 10.5
    True
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(10.5, 1)
    >>> print(s.stddev)
    None
    >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
    ...     == s.median == 10.5
    True
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(-10.5, 2)
    >>> print(s.stddev)
    0
    >>> s.minimum == s.maximum == s.mean_arith == s.median == -10.5
    True
    >>> print(s.mean_geom)
    None
    >>> s is from_single_value(s, s.n)
    True

    >>> s = from_single_value(-10.5, 1)
    >>> print(s.stddev)
    None
    >>> s.minimum == s.maximum == s.mean_arith == s.median == -10.5
    True
    >>> print(s.mean_geom)
    None
    >>> s is from_single_value(s, s.n)
    True

    >>> try:
    ...     from_single_value(None)
    ... except TypeError as te:
    ...     print(str(te)[:20])
    value should be an i

    >>> try:
    ...     from_single_value("a")
    ... except TypeError as te:
    ...     print(str(te)[:20])
    value should be an i

    >>> try:
    ...     from_single_value(1, None)
    ... except TypeError as te:
    ...     print(str(te)[:20])
    n should be an insta

    >>> try:
    ...     from_single_value(1, "a")
    ... except TypeError as te:
    ...     print(str(te)[:20])
    n should be an insta

    >>> try:
    ...     from_single_value(s, 12)
    ... except ValueError as ve:
    ...     print(str(ve)[:20])
    Incompatible numbers

    >>> try:
    ...     from_single_value(inf)
    ... except ValueError as ve:
    ...     print(str(ve)[:20])
    value=inf is not fin
    """
    n = check_int_range(n, "n", 1, 1_000_000_000_000_000_000)
    if isinstance(value, SampleStatistics):
        if value.n == n:
            return value
        raise ValueError(  # noqa: TRY004
            f"Incompatible numbers of values {n} and {value}.")
    if not isinstance(value, int | float):
        raise type_error(value, "value", (int, float, SampleStatistics))
    if not isfinite(value):
        raise ValueError(f"value={value} is not finite.")
    return SampleStatistics(
        n=n, minimum=value, median=value, mean_arith=value,
        mean_geom=None if value <= 0 else value, maximum=value,
        stddev=None if n <= 1 else 0)


def from_samples(source: Iterable[int | float]) -> SampleStatistics:
    """
    Create a statistics object from an iterable of integers or floats.

    As bottom line, this function will forward computations to the
    :mod:`statistics` routines that ship with Python if nothing else works.
    However, sometimes, something else may work: In particular, if the data
    consists of only integers. In this case, it just might be possible to
    compute the statistics very accurately with integer precision, where
    possible.

    Let's say we have a sequence of pure integers.
    We can compute the arithmetic mean by


    :param source: the source
    :return: a statistics representing the statistics over `source`

    >>> s = from_samples([0.0])
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

    >>> s = from_samples([1.0])
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

    >>> s = from_samples([1.0, 1])
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

    >>> s = from_samples([0, 0.0])
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
    >>> s = from_samples(dd)
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
    >>> s = from_samples(dd)
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
    >>> s = from_samples(dd)
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
    >>> s = from_samples(dd)
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
    >>> s = from_samples(dd)
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
    >>> s = from_samples(dd)
    >>> s.n
    3
    >>> s.minimum
    100000
    >>> s.maximum
    3000000000
    >>> print(s.mean_geom)
    18171205.928321395
    >>> (100000 * 20000000 * 3000000000) ** (1 / 3)
    18171205.92832138
    >>> 100000 * (((100000 // 100000) * (20000000 // 100000) * (
    ...     3000000000 // 100000)) ** (1 / 3))
    18171205.92832139
    >>> print(s.mean_geom ** 3)
    5.999999999999999e+21
    >>> print(18171205.92832139 ** 3)
    5.999999999999995e+21
    >>> s.median
    20000000
    >>> print(s.stddev)
    1726277112.7487035
    >>> stat_stddev(dd)
    1726277112.7487035

    >>> dd = [3.3, 2.5, 3.7, 4.9]
    >>> s = from_samples(dd)
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

    >>> dd = [3, 1, 2, 5]
    >>> s = from_samples(dd)
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

    >>> dd = [8, 8, 8, 8, 9, 10, 10, 11, 11, 12, 12, 12, 12, 13,
    ...       13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 16, 16, 16]
    >>> s = from_samples(dd)
    >>> print(s.minimum)
    8
    >>> print(s.maximum)
    16
    >>> print(s.mean_arith)
    12.5
    >>> print(s.median)
    13
    >>> print(s.mean_geom)
    12.19715026502289
    >>> stat_geomean(dd)
    12.19715026502289
    >>> print(s.stddev)
    2.673602092336881
    >>> stat_stddev(dd)
    2.673602092336881

    >>> dd = [3, 4, 7, 14, 15, 16, 26, 28, 29, 30, 31, 31]
    >>> s = from_samples(dd)
    >>> print(s.minimum)
    3
    >>> print(s.maximum)
    31
    >>> print(s.mean_arith)
    19.5
    >>> print(s.median)
    21

    >>> print(s.mean_geom)
    15.354984483655892
    >>> stat_geomean(dd)
    15.354984483655894
    >>> k = 1
    >>> for i in dd:
    ...     k *= i
    >>> k
    171787904870400
    >>> len(dd)
    12
    >>> k ** (1 / 12)
    15.354984483655889
    >>> 15.354984483655889 ** 12
    171787904870399.62
    >>> 15.354984483655894 ** 12
    171787904870400.34
    >>> 15.354984483655892 ** 12
    171787904870400.1

    >>> print(s.stddev)
    10.917042556563485
    >>> print(str(stat_stddev(dd))[:-1])
    10.91704255656348

    >>> dd = [375977836981734264856247621159545315,
    ...       1041417453269301410322718941408784761,
    ...       2109650311556162106262064987699051941]
    >>> s = from_samples(dd)
    >>> print(s.minimum)
    375977836981734264856247621159545315
    >>> print(s.maximum)
    2109650311556162106262064987699051941
    >>> print(s.mean_arith)
    1175681867269065927147010516755794006
    >>> stat_mean(dd)
    1.1756818672690659e+36
    >>> print(s.median)
    1041417453269301410322718941408784761

    >>> print(s.mean_geom)
    9.382801392765291e+35
    >>> stat_geomean(dd)
    9.38280139276522e+35

    >>> str(dd[0] * dd[1] * dd[2])[:60]
    '826033329443972563356247815302467930409182372405786485790679'
    >>> str(int(9.382801392765291e+35) ** 3)[:60]
    '826033329443972374842763874805993468673735440486439147266106'
    >>> str(int(9.38280139276522e+35) ** 3)[:60]
    '826033329443953666416831847378532327244986484162191539691938'

    >>> print(s.stddev)
    874600058269081159245960567663054887
    >>> stat_stddev(dd)
    8.746000582690812e+35

    >>> dd = [104275295274308290135253194482044160663473778025704,
    ...       436826861307375084714000787588311944456580437896461,
    ...       482178404791292289021955619498303854464057392180997,
    ...       521745351662201002493923306143082542601267608373030,
    ...       676289718505789968602970820038005797309334755525626]
    >>> s = from_samples(dd)
    >>> print(s.minimum)
    104275295274308290135253194482044160663473778025704
    >>> print(s.maximum)
    676289718505789968602970820038005797309334755525626
    >>> print(s.mean_arith)
    444263126308193326993620745549949659898942794400364
    >>> stat_mean(dd)
    4.442631263081933e+50
    >>> print(s.median)
    482178404791292289021955619498303854464057392180997

    >>> print(s.mean_geom)
    3.783188481668667e+50
    >>> stat_geomean(dd)
    3.78318848166862e+50

    >>> print(s.stddev)
    210311926886813737006941586539087921260462032505870
    >>> stat_stddev(dd)
    2.1031192688681374e+50

    >>> dd = [4, 5, 5, 6, 6, 6, 6, 6, 8, 8]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    5.884283961687533
    >>> print(stat_geomean(dd))
    5.884283961687533

    >>> dd = [4, 4, 4, 5, 5, 8]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    4.836542350243914
    >>> print(stat_geomean(dd))
    4.8365423502439135

    >>> dd = [2, 8, 11, 17, 26, 30, 32]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    13.327348017053906
    >>> print(stat_geomean(dd))
    13.327348017053906

    >>> dd = [2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    3.4710522375429465
    >>> print(stat_geomean(dd))
    3.471052237542947

    >>> dd = [3, 4, 4, 5, 6, 8, 8, 8, 8]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    5.653305998922543
    >>> print(stat_geomean(dd))
    5.653305998922543

    >>> dd = [16, 17, 19, 20, 20, 21, 22, 23, 24, 24, 25, 26, 29, 31,
    ...       31, 31, 32, 32, 32]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    24.419566831650357
    >>> print(stat_geomean(dd))
    24.41956683165036

    >>> dd = [66, 68, 69, 70, 72, 73, 73, 79, 81, 87, 94, 99, 100, 102, 103,
    ...       112, 118, 119, 123, 123]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    89.45680043258344
    >>> print(stat_geomean(dd))
    89.45680043258346

    >>> dd = [44, 63, 63, 68, 68, 68, 70, 74, 74, 80, 95, 108, 110, 128]
    >>> s = from_samples(dd)
    >>> print(s.mean_geom)
    76.6864641736076
    >>> print(stat_geomean(dd))
    76.68646417360763

    >>> try:
    ...     from_samples(None)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is None.

    >>> from_samples((int("343213544728723549420193506618248802478442\
545733127827402743350092428341563721880022852900744775368104117201410\
41"), int("4543178800835483269512609282884075126142677531600199807725\
0558561959304806690567285991174956892786401583087254156"), int("35473\
203294104466229269097724582630304968924904656920211268628173495602053\
843032960943121516556362641127137000879"))).mean_arith
    38408781925110551288804847071749420604746651597990567009597840581\
565913672301929416406528849308895284373981465359

    >>> try:
    ...     from_samples(1)
    ... except TypeError as te:
    ...     print(te)
    source should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     from_samples([])
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
        return from_single_value(minimum, n)

    # Compute the median.
    middle: Final[int] = n >> 1
    median: Final[int | float] = data[middle] if (n & 1) == 1 else (
        __mean_of_two(data[middle - 1], data[middle]))

    # Is it possible, at this stage, that all data are integers?
    can_int: bool = isinstance(minimum, int) and isinstance(maximum, int)

    # If we have only two numbers, we also already have the mean.
    # Otherwise, if we have only integer data so far and we know that
    # regardless how we dice it, the sum of the data will never exceed
    # the range in which floats can accurately represent integers, then
    # we also know that we can compute the arithmetic mean exactly.
    mean_arith: int | float | None = median if n <= 2 else (
        try_int(stat_mean(data)) if can_int and (
            (n * (1 + max(maximum, 0) - min(minimum, 0)))
            < __DBL_INT_LIMIT_P_I) else None)
    mean_geom: int | float | None = None  # We do not know the geometric mean
    stddev: int | float | None = None  # and neither the standard deviation.

    if can_int:  # can we try to do exact computations using ints?
        # Go over the data once and see if we can treat it as all-integer.
        # If yes, then we can compute some statistics very precisely.
        # are all values integers?
        int_sum: int = 0  # the integer sum (for mean, stddev)
        int_prod: int = 1  # the integer product (for geom_mean)
        int_sum_sqr: int = 0  # the sum of squares (for stddev)
        big_gcd: int = cast(int, minimum)  # the GCD of *all* the integers

        # The following is *only* used if we have *only* integer data.
        # stddev((a, b, ...)) = stddev((a-x, b-x, ...))
        # If we can shift the whole data such that its center is around 0,
        # then the difference that we have to add up become smaller, and thus
        # the floating point arithmetic that we may need to use becomes more
        # accurate. If we know the mean, then shifting the data by the mean
        # will lead to the smallest sum of deviations. If we know only the
        # median, then this is better than nothing.
        shift: Final[int] = int(median) if mean_arith is None \
            else (mean_arith if isinstance(mean_arith, int)
                  else int(round(mean_arith)))

        for ee in data:  # iterate over all data
            if not isinstance(ee, int):
                can_int = False
                break
            int_prod *= ee  # We can compute exact products (needed for gmean)
            big_gcd = gcd(big_gcd, ee)
            e: int = ee - shift  # shift to improve precision
            int_sum += e  # so we can sum exactly
            int_sum_sqr += e * e  # and compute the sum of squares

        if can_int:
            if n > 2:  # mean_arith is None or an approximation
                mean_arith = try_int_add(shift, try_int_div(int_sum, n))

            if stddev is None:
                with suppress(ArithmeticError):
                    issmvs: int | float = try_int_add(
                        int_sum_sqr, -try_int_div(int_sum * int_sum, n))
                    var: Final[int | float] = try_float_int_div(issmvs, n - 1)
                    stddev_test: Final[float] = try_int_sqrt(var) if \
                        isinstance(var, int) else sqrt(var)
                    if stddev_test > 0:
                        stddev = stddev_test

            if minimum > 0:  # geometric mean only defined for all-positive
                mean_geom_a: float | None = None
                mean_geom_b: float | None = None

                # most likely, big_gcd is 1 ... but we can try...
                int_prod //= (big_gcd ** n)  # must be exact: it's the gcd
                lower: Final[int] = cast(int, minimum) // big_gcd  # exact
                upper: Final[int] = cast(int, maximum) // big_gcd  # exact

                # two different attempts to compute the geometric mean
                # either by log-scaling
                with suppress(ArithmeticError):
                    mean_geom_test = 2 ** try_int(log2(int_prod) / n)
                    if isfinite(mean_geom_test) and (
                            lower <= mean_geom_test <= upper):
                        mean_geom_a = mean_geom_test

                # or by computing the actual root
                with suppress(ArithmeticError):
                    mean_geom_test = try_int(int_prod ** (1 / n))
                    if isfinite(mean_geom_test) and (
                            lower <= mean_geom_test <= upper):
                        mean_geom_b = mean_geom_test

                if mean_geom_a is None:  # the log scaling failed
                    mean_geom = None if mean_geom_b is None \
                        else try_int_mul(big_gcd, mean_geom_b)
                elif mean_geom_b is not None:  # so the actual root worked, too
                    if mean_geom_a > mean_geom_b:
                        mean_geom_a, mean_geom_b = mean_geom_b, mean_geom_a
                    # the difference will not be big, we can try everything
                    best_diff = inf
                    while mean_geom_a <= mean_geom_b:
                        diff = abs(int_prod - (mean_geom_a ** n))
                        if diff < best_diff:
                            best_diff = diff
                            mean_geom = try_int_mul(big_gcd, mean_geom_a)
                        mean_geom_a = nextafter(mean_geom_a, inf)
                else:
                    mean_geom = try_int_mul(big_gcd, mean_geom_a)

    if mean_arith is None:
        mean_arith = stat_mean(data)
    if stddev is None:
        stddev = stat_stddev(data)
    if (mean_geom is None) and (minimum > 0):
        mean_geom = stat_geomean(data)

    if mean_geom is not None:
        # Deal with errors that may have arisen due to
        # numerical imprecision.
        if mean_geom < minimum:
            if __almost_le(minimum, mean_geom):
                mean_geom = minimum
            else:
                raise ValueError(f"mean_geom={mean_geom} but min={minimum}")
        if mean_arith < mean_geom:
            if __almost_le(mean_geom, mean_arith):
                mean_geom = mean_arith
            else:
                raise ValueError(
                    f"mean_geom={mean_geom} but mean_arith={mean_arith}")

    return SampleStatistics(minimum=minimum, median=median,
                            mean_arith=mean_arith, mean_geom=mean_geom,
                            maximum=maximum, stddev=stddev, n=n)


class CsvReader:
    """
    A csv parser for sample statistics.

    >>> from pycommons.io.csv import csv_read
    >>> csv = ["n;min;mean;med;geom;max;sd",
    ...        "3;2;3;4;3;10;5", "6;2;;;;;0", "1;;;2;;;", "3;;;;;0;",
    ...        "4;5;12;32;11;33;7"]
    >>> csv_read(csv, CsvReader, CsvReader.parse_row, print)
    3;2;4;3;3;10;5
    6;2;2;2;2;2;0
    1;2;2;2;2;2;None
    3;0;0;0;None;0;0
    4;5;32;12;11;33;7

    >>> csv = ["value", "1", "3", "0", "-5", "7"]
    >>> csv_read(csv, CsvReader, CsvReader.parse_row, print)
    1;1;1;1;1;1;None
    1;3;3;3;3;3;None
    1;0;0;0;None;0;None
    1;-5;-5;-5;None;-5;None
    1;7;7;7;7;7;None

    >>> csv = ["n;m;sd", "1;3;", "3;5;0"]
    >>> csv_read(csv, CsvReader, CsvReader.parse_row, print)
    1;3;3;3;3;3;None
    3;5;5;5;5;5;0

    >>> csv = ["n;m", "1;3", "3;5"]
    >>> csv_read(csv, CsvReader, CsvReader.parse_row, print)
    1;3;3;3;3;3;None
    3;5;5;5;5;5;0
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
        columns should be an instance of dict but is int, namely '1'.

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
        super().__init__()

        if not isinstance(columns, dict):
            raise type_error(columns, "columns", dict)

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

        #: the index for the median
        self.__idx_median: int | None = csv_column_or_none(
            columns, KEY_MEDIAN)
        if self.__idx_median is not None:
            has += 1
            has_idx = self.__idx_median

        #: the index for the geometric mean
        self.__idx_mean_geom: int | None = csv_column_or_none(
            columns, KEY_MEAN_GEOM)
        if self.__idx_mean_geom is not None:
            has += 1
            has_idx = self.__idx_mean_geom

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
            self.__idx_min = self.__idx_max = self.__idx_median \
                = self.__idx_mean_arith = has_idx

    def parse_row(self, data: list[str]) -> SampleStatistics:
        """
        Parse a row of data.

        :param data: the data row
        :return: the sample statistics
        """
        n: Final[int] = 1 if self.idx_n is None else int(data[self.idx_n])
        mi: int | float | None = csv_val_or_none(
            data, self.__idx_min, str_to_num)

        if self.__is_single:
            return SampleStatistics(
                n=n, minimum=mi, median=mi, mean_arith=mi,
                mean_geom=mi if (mi > 0) or (self.__idx_mean_geom is not None)
                else None, maximum=mi, stddev=None if n <= 1 else 0)

        ar: int | float | None = csv_val_or_none(
            data, self.__idx_mean_arith, str_to_num)
        me: int | float | None = csv_val_or_none(
            data, self.__idx_median, str_to_num)
        ge: int | float | None = csv_val_or_none(
            data, self.__idx_mean_geom, str_to_num)
        ma: int | float | None = csv_val_or_none(
            data, self.__idx_max, str_to_num)
        sd: int | float | None = csv_val_or_none(
            data, self.__idx_sd, str_to_num)

        if mi is None:
            if ar is not None:
                mi = ar
            elif me is not None:
                mi = me
            elif ge is not None:
                mi = ge
            elif ma is not None:
                mi = ma
            else:
                raise ValueError(
                    f"No value defined for min@{self.__idx_min}={mi}, mean@"
                    f"{self.__idx_mean_arith}={ar}, med@{self.__idx_median}="
                    f"{me}, gmean@{self.__idx_mean_geom}={ge}, max@"
                    f"{self.__idx_max}={ma} defined in {data!r}.")
        return SampleStatistics(
            n=n, minimum=mi, mean_arith=mi if ar is None else ar,
            median=mi if me is None else me, mean_geom=(
                mi if mi > 0 else None) if (ge is None) else ge,
            maximum=mi if ma is None else ma,
            stddev=(0 if (n > 1) else None) if sd is None else sd)

    def parse_optional_row(self, data: list[str] | None) \
            -> SampleStatistics | None:
        """
        Parse a row of data that may be empty.

        :param data: the row of data that may be empty
        :return: the sample statistic, if the row contains data, else `None`

        >>> print(CsvReader.parse_optional_row(None, ["1"]))
        None
        >>> print(CsvReader.parse_optional_row(CsvReader({"v": 0}), ["1"]))
        1;1;1;1;1;1;None
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
                (self.__idx_median is not None) and (
                str.__len__(data[self.__idx_median]) > 0)) or (
                (self.__idx_mean_geom is not None) and (
                str.__len__(data[self.__idx_mean_geom]) > 0)) or (
                (self.__idx_max is not None) and (
                str.__len__(data[self.__idx_max]) > 0))):
            return self.parse_row(data)
        return None


class CsvWriter:
    """A class for CSV writing of :class:`SampleStatistics`."""

    def __init__(self, scope: str | None = None,
                 n_not_needed: bool = False,
                 what_short: str | None = None,
                 what_long: str | None = None) -> None:
        """
        Initialize the csv writer.

        :param scope: the prefix to be pre-pended to all columns
        :param n_not_needed: should we omit the `n` column?
        :param what_short: the short description of what the statistics is
            about
        :param what_long: the long statistics of what the statistics is about

        >>> try:
        ...     CsvWriter(n_not_needed=None)
        ... except TypeError as te:
        ...     print(te)
        n_not_needed should be an instance of bool but is None.
        """
        #: an optional scope
        self.__scope: Final[str | None] = (
            str.strip(scope)) if scope is not None else None
        if not isinstance(n_not_needed, bool):
            raise type_error(n_not_needed, "n_not_needed", bool)
        #: is the n-column needed
        self.n_not_needed: Final[bool] = n_not_needed

        #: has this writer been set up?
        self.__setup: bool = False
        #: should we print only a single value
        self.__single_value: bool = False
        #: do we have the n column
        self.__has_n: bool = True
        #: do we need the geometric mean column?
        self.__has_geo_mean: bool = True

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
        #: the key for n if n is printed
        self.__key_n: str | None = None
        #: the key for single values
        self.__key_all: str | None = None
        #: the key for minimum values
        self.__key_min: str | None = None
        #: the key for the arithmetic mean
        self.__key_mean_arith: str | None = None
        #: the key for the median
        self.__key_med: str | None = None
        #: the key for the geometric mean
        self.__key_mean_geom: str | None = None
        #: the key for the maximum value
        self.__key_max: str | None = None
        #: the key for the standard deviation
        self.__key_sd: str | None = None

    def setup(self, data: Iterable[SampleStatistics]) -> "CsvWriter":
        """
        Set up this csv writer based on existing data.

        :param data: the data to setup with
        :returns: this writer

        >>> a = CsvWriter()
        >>> try:
        ...     a.setup([])
        ... except ValueError as ve:
        ...     print(ve)
        SampleStatistics CsvWriter did not see any data.
        >>> try:
        ...     a.setup([])
        ... except ValueError as ve:
        ...     print(ve)
        SampleStatistics CsvWriter has already been set up.

        >>> try:
        ...     CsvWriter().setup([1])
        ... except TypeError as te:
        ...     print(str(te)[:60])
        data[i] should be an instance of pycommons.math.sample_stati
        """
        if self.__setup:
            raise ValueError(
                "SampleStatistics CsvWriter has already been set up.")
        self.__setup = True

        # We need to check at most three conditions to see whether we can
        # compact the output:
        # 1. If all minimum, mean, median, maximum (and geometric mean, if
        # defined) are the same, then we can collapse this column.
        all_same: bool = True
        # 2. If no geometric mean is found, then we can also omit this column.
        has_no_geom: bool = True
        # 3. If the `n` column is not needed or if all `n=1`, then we can omit
        # it. We only need to check if n is not needed if self.n_not_needed is
        # False because otherwise, we rely on self.n_not_needed.
        # n_really_not_needed will become False if we find one situation where
        # we actually need n.
        n_really_not_needed: bool = not self.n_not_needed
        # So if n_really_not_needed is True, we need to do 3 checks.
        # Otherwise, we only need two checks.
        checks_needed: int = 3 if n_really_not_needed else 2
        # the number of samples seen
        seen: int = 0

        for d in data:  # Iterate over the data until all checks are done.
            if not isinstance(d, SampleStatistics):
                raise type_error(d, "data[i]", SampleStatistics)
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
            if has_no_geom and (d.mean_geom is not None):
                has_no_geom = False
                checks_needed -= 1
                if checks_needed <= 0:
                    break

        if seen <= 0:
            raise ValueError(
                "SampleStatistics CsvWriter did not see any data.")
        n_not_needed = n_really_not_needed or self.n_not_needed
        # Now we know the columns that need to be generated.
        self.__has_n = not n_not_needed
        self.__single_value = all_same
        self.__has_geo_mean = (not has_no_geom) and (not all_same)

        scope: Final[str | None] = self.__scope

        # set up the keys
        if self.__has_n:
            self.__key_n = csv_scope(scope, KEY_N)
        if self.__single_value:
            self.__key_all = KEY_VALUE if scope is None else csv_scope(
                scope, KEY_VALUE if self.__has_n else None)
        else:
            self.__key_min = csv_scope(scope, KEY_MINIMUM)
            self.__key_mean_arith = csv_scope(scope, KEY_MEAN_ARITH)
            self.__key_med = csv_scope(scope, KEY_MEDIAN)
            self.__key_max = csv_scope(scope, KEY_MAXIMUM)
            if self.__has_geo_mean:
                self.__key_mean_geom = csv_scope(scope, KEY_MEAN_GEOM)
            self.__key_sd = csv_scope(scope, KEY_STDDEV)

        return self

    def get_column_titles(self, dest: Callable[[str], None]) -> None:
        """
        Get the column titles.

        :param dest: the destination string consumer

        >>> try:
        ...     CsvWriter().get_column_titles(print)
        ... except ValueError as ve:
        ...     print(ve)
        SampleStatistics CsvWriter has not been set up.
        """
        if not self.__setup:
            raise ValueError("SampleStatistics CsvWriter has not been set up.")
        if self.__has_n:
            dest(self.__key_n)

        if self.__single_value:
            dest(self.__key_all)
        else:
            dest(self.__key_min)
            dest(self.__key_mean_arith)
            dest(self.__key_med)
            if self.__has_geo_mean:
                dest(self.__key_mean_geom)
            dest(self.__key_max)
            dest(self.__key_sd)

    def get_optional_row(self,
                         data: int | float | SampleStatistics | None,
                         dest: Callable[[str], None],
                         n: int | None = None) -> None:
        """
        Attach an empty row of the correct shape to the output.

        This function may be needed in cases where the statistics are part of
        other records that sometimes do not contain the record.

        :param data: the data item
        :param dest: the output destination
        :param n: the number of samples

        >>> try:
        ...     CsvWriter().get_optional_row("x", print)
        ... except TypeError as te:
        ...     print(str(te)[:53])
        data should be an instance of any in {None, float, in
        """
        if data is None:
            # attach an empty row
            for _ in range((1 if self.__has_n else 0) + (
                    1 if self.__single_value else (
                    6 if self.__has_geo_mean else 5))):
                dest("")
            return
        if isinstance(data, int | float):  # convert single value
            data = from_single_value(data, 1 if n is None else n)
        elif not isinstance(data, SampleStatistics):  # huh?
            raise type_error(data, "data", (
                int, float, SampleStatistics, None))
        elif (n is not None) and (n != data.n):  # sanity check
            raise ValueError(f"data.n={data.n} but n={n}.")
        self.get_row(data, dest)

    def get_row(self, data: SampleStatistics,
                dest: Callable[[str], None]) -> None:
        """
        Render a single sample statistics to a CSV row.

        :param data: the data sample statistics
        :param dest: the string consumer
        """
        if self.__has_n:
            dest(str(data.n))
        if self.__single_value:
            if data.minimum != data.maximum:
                raise ValueError(f"Inconsistent data {data}.")
            dest(num_to_str(data.minimum))
        else:
            dest(num_to_str(data.minimum))
            dest(num_to_str(data.mean_arith))
            dest(num_to_str(data.median))
            if self.__has_geo_mean:
                dest(num_or_none_to_str(data.mean_geom))
            dest(num_to_str(data.maximum))
            dest(num_or_none_to_str(data.stddev))

    def get_header_comments(self, dest: Callable[[str], None]) -> None:
        """
        Get any possible header comments.

        :param dest: the destination
        """
        if (self.__scope is not None) and (self.__long_name is not None):
            dest(f"Sample statistics about {self.__long_name}.")

    def get_footer_comments(self, dest: Callable[[str], None]) -> None:
        """
        Get any possible footer comments.

        :param dest: the destination
        """
        long_name: str | None = self.__long_name
        long_name = "" if long_name is None else f" {long_name}"
        short_name: str | None = self.__short_name
        short_name = "" if short_name is None else f" {short_name}"
        name: str = long_name
        first: bool = True

        scope: Final[str] = self.__scope
        if (scope is not None) and (
                self.__has_n or (not self.__single_value)):
            if first:
                dest("")
                first = False
            dest(f"All{name} sample statistics start with "
                 f"{(scope + SCOPE_SEPARATOR)!r}.")
            name = short_name

        if self.__has_n:
            if first:
                dest("")
                first = False
            dest(f"{self.__key_n}: the number of{name} samples")
            name = short_name
        if self.__single_value:
            if first:
                dest("")
            dest(f"{self.__key_all}: all{name} samples have this value")
        else:
            if first:
                dest("")
            n_name: str | None = self.__key_n
            if n_name is None:
                n_name = KEY_N
            dest(f"{self.__key_min}: the smallest encountered{name} value")
            name = short_name
            dest(f"{self.__key_mean_arith}: the arithmetic mean of all the"
                 f"{name} values, i.e., the sum of the values divided by "
                 f"their number {n_name}")
            dest(f"{self.__key_med}: the median of all the{name} values, "
                 f"which can be computed by sorting the values and then "
                 f"picking the value in the middle of the sorted list (in "
                 f"case of an odd number {n_name} of values) or the "
                 f"arithmetic mean (half the sum) of the two values in the "
                 f"middle (in case of an even number {n_name})")
            if self.__has_geo_mean:
                dest(f"{self.__key_mean_geom}: the geometric mean of all the"
                     f"{name} values, i.e., the {n_name}-th root of the "
                     f"product of all values, which is only defined if all "
                     f"values are > 0")
            dest(f"{self.__key_max}: the largest encountered{name} value")
            dest(f"{self.__key_sd}: the standard deviation of the{name} "
                 "values, which is a measure of spread: the larger it "
                 "is, the farther are the values distributed away from "
                 f"the arithmetic mean {self.__key_mean_arith}. It can be "
                 "computed as the ((sum of squares) - (square of the sum)"
                 f" / {n_name}) / ({n_name} - 1) of all{name} values.")

    def get_footer_bottom_comments(self, dest: Callable[[str], None]) -> None:
        """
        Get the bottom footer comments.

        :param dest: the string destination

        >>> def __qpt(s: str):
        ...     print(s[:70])
        >>> CsvWriter.get_footer_bottom_comments(None, __qpt)
        This CSV output has been created using the versatile CSV API of pycomm
        Sample statistics were computed using pycommons.math.sample_statistics
        You can find pycommons at https://thomasweise.github.io/pycommons.
        """
        pycommons_footer_bottom_comments(
            self, dest, ("Sample statistics were computed "
                         "using pycommons.math.sample_statistics."))
