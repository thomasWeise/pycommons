"""A simple and immutable basic statistics record."""

from contextlib import suppress
from dataclasses import dataclass
from fractions import Fraction
from math import ceil, inf, isfinite, nan, nextafter
from statistics import geometric_mean as stat_geomean
from statistics import mean as stat_mean
from typing import Final, Iterable, Union

from pycommons.io.csv import (
    CSV_SEPARATOR,
    csv_column,
    csv_column_or_none,
    csv_val_or_none,
)
from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.math.int_math import __DBL_INT_LIMIT_P_I as _DBL_INT_LIMIT_P_I
from pycommons.math.int_math import (
    ceil_div,
    float_to_frac,
    try_int,
    try_int_div,
)
from pycommons.math.stream_statistics import (
    KEY_MAXIMUM,
    KEY_MEAN_ARITH,
    KEY_MEAN_GEOM,
    KEY_MEDIAN,
    KEY_MINIMUM,
    KEY_N,
    KEY_STDDEV,
    StreamStatistics,
    StreamStatisticsAggregate,
)
from pycommons.math.stream_statistics import CsvWriter as CsvWriterBase
from pycommons.strings.string_conv import (
    str_to_num,
)
from pycommons.types import check_int_range, type_error


def _mean_of_two(a: int | float, b: int | float) -> int | float:
    """
    Compute the mean of two numbers.

    :param a: the first number
    :param b: the second number
    :returns: the mean

    >>> _mean_of_two(1, 1)
    1
    >>> _mean_of_two(1.0, 1.0)
    1
    >>> _mean_of_two(1, 2)
    1.5
    >>> _mean_of_two(1, 3)
    2
    >>> _mean_of_two(1.5, 1.7)
    1.6

    >>> _mean_of_two(-1, -1)
    -1
    >>> _mean_of_two(-1.0, -1.0)
    -1
    >>> _mean_of_two(-1, -2)
    -1.5
    >>> _mean_of_two(-1, -3)
    -2
    >>> _mean_of_two(-1.5, -1.7)
    -1.6

    >>> _mean_of_two(1, -1)
    0
    >>> _mean_of_two(-1.0, 1.0)
    0
    >>> _mean_of_two(1, -2)
    -0.5
    >>> _mean_of_two(1, -3)
    -1
    >>> _mean_of_two(1.5, -1.7)
    -0.09999999999999998
    >>> _mean_of_two(-1.5, 1.7)
    0.09999999999999998

    >>> _mean_of_two(1.7976931348623157e+308, 1.7976931348623157e+308)
    1.7976931348623157e+308
    >>> _mean_of_two(1.7976931348623155e+308, 1.7976931348623157e+308)
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


def _almost_le(a: int | float, b: int | float) -> bool:
    """
    Check if `a <= b` holds approximately.

    `a <= b` holds if, well, `a` is less than or equal to `b`. It holds almost
    if `a` is just a tiny bit larger than `b`.

    :param a: the first value
    :param b: the second value
    :returns: `True` if we can say: `a` is approximately less or equal than `b`
        and any deviation from this probably results from numerical issues.

    >>> _almost_le(1, 0)
    False
    >>> _almost_le(0, 0)
    True
    >>> _almost_le(1.1, 1.09)
    False
    >>> _almost_le(1.1, 1.099999)
    False
    >>> _almost_le(1.1, 1.09999999)
    False
    >>> _almost_le(1.1, 1.0999999999)
    False
    >>> _almost_le(1.1, 1.099999999999)
    False
    >>> _almost_le(1.099999999999, 1.1)
    True
    >>> _almost_le(1.1, 1.0999999999999)
    True
    >>> _almost_le(1.0999999999999, 1.1)
    True

    >>> _almost_le(0, -1)
    False
    >>> _almost_le(-1.09, -1.1)
    False
    >>> _almost_le(-1.099999, -1.1)
    False
    >>> _almost_le(-1.09999999, -1.1)
    False
    >>> _almost_le(-1.0999999999, -1.1)
    False
    >>> _almost_le(-1.099999999999, -1.1)
    False
    >>> _almost_le(-1.1, -1.099999999999)
    True
    >>> _almost_le(-1.0999999999999, -1.1)
    True
    >>> _almost_le(-1.1, -1.0999999999999)
    True

    >>> _almost_le(23384026197294446691258957323460528314494920687616,
    ...             2.3384026197294286e+49)
    True
    >>> _almost_le(nextafter(5, inf), nextafter(5, -inf))
    True
    >>> _almost_le(nextafter(nextafter(5, inf), inf),
    ...             nextafter(nextafter(5, -inf), -inf))
    True
    >>> _almost_le(nextafter(nextafter(nextafter(5, inf), inf), inf),
    ...             nextafter(nextafter(nextafter(5, -inf), -inf), -inf))
    True
    >>> _almost_le(nextafter(nextafter(nextafter(nextafter(5, inf), inf),
    ...             inf), inf), nextafter(nextafter(nextafter(5, -inf),
    ...             -inf), -inf))
    True
    >>> _almost_le(5.114672824837722e+148, 5.1146728248374894e+148)
    True

    >>> _almost_le(-1.7976931348623157e+308,
    ...             -int(1.7976931348623157e+308) * 10)
    False
    >>> _almost_le(-int(1.7976931348623157e+308) * 10,
    ...             -1.7976931348623157e+308)
    True
    >>> _almost_le(1e-302, 0)
    True
    >>> _almost_le(1e-200, 0)
    False
    """
    if a <= b:
        return True

    if a < 0:
        a, b = -b, -a  # maybe: a = -19, b = -20 -> maybe: a = 20, b = 19
    elif b <= 0:
        return (b >= 0) and (a <= 1e-300)

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
        return (9999999999999 * a_int) <= (b_int * 10000000000000)


def _to_frac(a: int | float) -> Fraction:
    """
    Convert a number to a fraction.

    :param a: the number
    :returns: the fraction

    >>> _to_frac(23)
    Fraction(23, 1)
    >>> _to_frac(2.34)
    Fraction(117, 50)
    """
    return Fraction(a) if isinstance(a, int) else Fraction(*float_to_frac(a))


def _from_frac(a: int | float | Fraction) -> int | float:
    """
    Convert a fraction to either an integer or a float.

    :param a: the fraction
    :returns: the integer or float value

    >>> _from_frac(1.6)
    1.6
    >>> _from_frac(123)
    123
    >>> _from_frac(Fraction(7, 8))
    0.875
    >>> _from_frac(Fraction(1237, 1))
    1237
    """
    if isinstance(a, int):
        return a
    if isinstance(a, float):
        return try_int(a)
    num: Final[int] = a.numerator
    denom: Final[int] = a.denominator
    if denom == 1:
        return num
    return try_int_div(num, denom)


#: the 0 fraction
_FRAC_0: Final[Fraction] = Fraction(0, 1)
#: the 1 fraction
_FRAC_1: Final[Fraction] = Fraction(1, 1)


def _int_root_bound_lower(base: int, root: int) -> int:
    """
    Compute a lower bound for a root.

    We use that `log(a ** b) = log(a) * b`.
    In binary, this means that: `a ** b == 2 ** (log2(a) * b)`, or, for roots
    `a ** (1/b) == 2 ** (log2(a) / b`.
    In bits, `2 ** x == 1 << x` and `floor(log2(x)) == x.bit_length() - 1`.
    Therefore, we know that `a ** (1/b) >= 1 << ((a.bit_length() // b) - 1)`.
    Similarly, we can have an upper bound by rounding up at each step
    `a ** (1/b) <= 1 << (1 + ((b.bit_length() + 1) // root)

    :param base: the base number
    :param root: the root
    :returns: the lower bound

    >>> _int_root_bound_lower(8, 3)
    1

    >>> _int_root_bound_lower(8, 2)
    2

    >>> _int_root_bound_lower(25, 3)
    1
    """
    logdiv: Final[int] = base.bit_length() // root
    return (1 << (logdiv - 1)) if logdiv > 0 else (0 if base < 1 else 1)


def _int_root_bound_upper(base: int, root: int) -> int:
    """
    Compute an upper bound for a root.

    :param base: the base number
    :param root: the root
    :returns: the upper bound

    >>> _int_root_bound_upper(8, 3)
    4

    >>> _int_root_bound_upper(8, 2)
    4

    >>> _int_root_bound_upper(25, 3)
    8
    """
    return base if root == 1 else min(1 << (1 + ceil_div(
        base.bit_length() + 1, root)), (base // 2) + (1 if base < 6 else 0))


def _frac_root_bound_lower(base: Fraction, root: int) -> Fraction:
    """
    Compute a lower bound for a root.

    :param base: the base number
    :param root: the root
    :returns: the lower bound

    >>> _frac_root_bound_lower(Fraction(8), 3)
    Fraction(1, 1)

    >>> _frac_root_bound_lower(Fraction(8), 2)
    Fraction(2, 1)

    >>> _frac_root_bound_lower(Fraction(25), 3)
    Fraction(1, 1)

    >>> _frac_root_bound_lower(Fraction(3, 8), 3)
    Fraction(1, 2)

    >>> _frac_root_bound_lower(Fraction(11, 8), 2)
    Fraction(1, 1)

    >>> _frac_root_bound_lower(Fraction(11, 25), 3)
    Fraction(1, 2)
    """
    return _FRAC_0 if base <= _FRAC_0 else (
        Fraction(1, _int_root_bound_upper(ceil_div(
            base.denominator, base.numerator), root))
        if base < _FRAC_1 else (
            _FRAC_1 if base == _FRAC_1 else Fraction(
                _int_root_bound_lower(int(base), root))))


def _frac_root_bound_upper(base: Fraction, root: int) -> Fraction:
    """
    Compute an upper bound for a root.

    :param base: the base number
    :param root: the root
    :returns: the upper bound

    >>> _frac_root_bound_upper(Fraction(8), 3)
    Fraction(4, 1)

    >>> _frac_root_bound_upper(Fraction(8), 2)
    Fraction(4, 1)

    >>> _frac_root_bound_upper(Fraction(25), 3)
    Fraction(8, 1)

    >>> _frac_root_bound_upper(Fraction(3, 8), 3)
    Fraction(1, 1)

    >>> _frac_root_bound_upper(Fraction(11, 8), 2)
    Fraction(2, 1)

    >>> _frac_root_bound_upper(Fraction(11, 25), 3)
    Fraction(1, 1)
    """
    return _FRAC_0 if base <= _FRAC_0 else (
        Fraction(1, _int_root_bound_lower(
            base.denominator // base.numerator, root))
        if base < _FRAC_1 else (
            _FRAC_1 if base == _FRAC_1 else Fraction(
                _int_root_bound_upper(ceil(base), root))))


def _limited_root(base: Fraction, root: int,
                  mini: Fraction = _FRAC_0,
                  maxi: Fraction | None = None) -> int | float:
    """
    Try to compute a root at a precision so exact that no digits are lost.

    :param base: the base
    :param root: the exponent
    :param mini: a limit for the smallest possible result
    :param maxi: a maximum value, the limit for the largest possible result,
        or `None` if no upper limit is known
    :returns: the power

    >>> from math import sqrt
    >>> sqrt(3)
    1.7320508075688772
    >>> _limited_root(Fraction(3, 1), 2)
    1.7320508075688772
    >>> _limited_root(Fraction(4, 1), 2)
    2

    >>> _limited_root(Fraction(3 ** 3, 1), 3)
    3
    >>> type(_limited_root(Fraction(3 ** 3, 1), 3))
    <class 'int'>

    >>> _limited_root(Fraction(3 ** 333, 1), 333)
    3

    >>> _limited_root(Fraction(9000 ** 1000, 1), 1000)
    9000

    >>> _limited_root(Fraction((10 ** 8) ** 100, 1), 35)
    71968567300115201992879

    >>> 0.456 ** (1 / 25)
    0.9690776862089129
    >>> _limited_root(Fraction(456, 1000), 25)
    0.9690776862089129

    >>> _limited_root(Fraction(2, 1), 2)
    1.4142135623730951
    >>> sqrt(2)
    1.4142135623730951
    """
    lower: Fraction | None = None
    upper: Fraction | None = None
    if base.denominator == 1:
        ibase = base.numerator
        if ibase <= 1:
            return ibase

        ilower: int = max(int(mini), _int_root_bound_lower(ibase, root))
        iupper: int = _int_root_bound_upper(ibase, root)
        if maxi is not None:
            iupper = min(int(maxi) + 1, iupper)
        imid: int = ilower
        while ilower <= iupper:
            imid = (ilower + iupper) >> 1
            imid_exp = imid ** root
            if imid_exp > ibase:
                iupper = imid - 1
            elif imid_exp < ibase:
                ilower = imid + 1
            else:
                return imid  # We got an exact integer result
        # No exact integer result, but at least new limits
        upper = Fraction(imid + 1)
        lower = Fraction(max(0, imid - 1))

    # Now we do binary search using fractions
    if upper is None:
        upper = max(base, _FRAC_1)
    if maxi is not None:
        upper = min(upper, maxi)
    upper = min(upper, _frac_root_bound_upper(base, root))
    if lower is None:
        lower = _FRAC_0
    lower = max(mini, lower)
    lower = max(lower, _frac_root_bound_lower(base, root))

    # Now compute the root using binary search within the limits.
    guess: int | float = nan
    equal_steps: int = 4
    while equal_steps > 0:
        last_guess: int | float = guess
        mid: Fraction = (lower + upper) / 2
        mid_exp = mid ** root
        if mid_exp > base:
            upper = mid
        elif mid_exp < base:
            lower = mid
        else:
            return _from_frac(mid)

        guess = _from_frac(mid)
        if (type(guess) is type(last_guess)) and (guess == last_guess):
            equal_steps -= 1
        else:
            equal_steps = 4
    return guess


@dataclass(frozen=True, init=False, order=False, eq=False)
class SampleStatistics(StreamStatistics):
    """An immutable record with sample statistics of one quantity."""

    #: The median, i.e., the value in the middle of the sorted list of
    #: :attr:`~pycommons.math.stream_statistics.StreamStatistics.n` data
    # samples.
    median: int | float
    #: The geometric mean value, if defined. This is the
    #: :attr:`~pycommons.math.stream_statistics.StreamStatistics.n`-th root
    #: of the product of all data samples.
    #: This value will be `None` if there was any sample which is not greater
    #: than 0.
    mean_geom: int | float | None

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
        8839096310731950625

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
        >>> hash(s2) == hash((0, 0, 0, inf, 0, inf, 1, 1))
        True

        >>> s3 = SampleStatistics(n=3, minimum=5, median=5, maximum=5,
        ...                       mean_arith=5, mean_geom=5, stddev=0.0)
        >>> s3.stddev
        0
        >>> hash(s3)
        1175763770956004139

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
        ...                      mean_arith=5, mean_geom=5, stddev=0)
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
        ...                      mean_arith=5, mean_geom=5, stddev=0)
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
        ...                      mean_arith=6, mean_geom=6.1, stddev=1)
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
        super().__init__(n, minimum, mean_arith, maximum, stddev)

        # check minimum
        median = try_int(median)
        if n == 1:
            if median != self.minimum:
                raise ValueError(f"median ({median}) must equal "
                                 f"minimum ({self.minimum}) if n=1.")
        elif median < self.minimum:
            raise ValueError(f"median ({median}) must be >= minimum ("
                             f"{self.minimum}) if n>1.")

        # check maximum
        if self.maximum < median:
            raise ValueError(
                f"maximum ({self.maximum}) must be >= med ({median}) if n>1.")

        # check geometric mean
        if mean_geom is None:
            if self.minimum > 0:
                raise ValueError(
                    f"If minimum ({self.minimum}) > 0, then mean_geom must be"
                    f" defined, but it is {mean_geom}.")
        else:
            if self.minimum <= 0:
                raise ValueError(
                    f"If minimum ({self.minimum}) <= 0, then mean_geom is "
                    f"undefined, but it is {mean_geom}.")
            mean_geom = try_int(mean_geom)
            if n == 1:
                if mean_geom != self.minimum:
                    raise ValueError(f"mean_geom ({mean_geom}) must equal "
                                     f"minimum ({self.minimum}) if n=1.")
            else:
                if not self.minimum <= mean_geom <= self.maximum:
                    raise ValueError(
                        "minimum<=mean_geom<=maximum must hold, but got "
                        f"{self.minimum}, {mean_geom}, and {self.maximum}.")
                if mean_geom > self.mean_arith:
                    raise ValueError(
                        f"mean_geom ({mean_geom}) must be <= "
                        f"mean_arith ({self.mean_arith}).")

        object.__setattr__(self, "median", median)
        object.__setattr__(self, "mean_geom", mean_geom)

    def __str__(self) -> str:
        """
        Get a string representation of this object.

        :returns: the string
        """
        return CSV_SEPARATOR.join(map(str, (
            self.n, self.minimum, self.median, self.mean_arith,
            self.mean_geom, self.maximum, self.stddev)))

    def min_mean(self) -> int | float:
        """
        Obtain the smallest of the three mean values.

        :returns: the smallest of `mean_arith`, `mean_geom`, and `median`

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

        :returns: the largest of `mean_arith`, `mean_geom`, and `median`

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
        :returns: an integer or float if this objects minimum equals its
            maximum, the object itself otherwise

        >>> s = SampleStatistics.from_single_value(10, 1)
        >>> s.compact() == 10
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = SampleStatistics.from_single_value(10, 2)
        >>> s.compact() is s
        True
        >>> s.compact() == s.compact(True)
        True

        >>> s = SampleStatistics.from_single_value(10, 2)
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

        :returns: the comparison key

        >>> SampleStatistics(2, 1, 2, 4.0, 3, 6, 0.2)._key()
        (1, 2, 4, 3, 6, 0.2, 2, 1)

        >>> SampleStatistics(1, 0, 0, 0, None, 0, None)._key()
        (0, 0, 0, inf, 0, inf, 1, 1)
        """
        return (self.minimum, self.median, self.mean_arith,
                inf if self.mean_geom is None else self.mean_geom,
                self.maximum, inf if self.stddev is None else self.stddev,
                self.n, 1)

    def get_mean_geom(self) -> int | float | None:
        """
        Get the geometric mean (:attr:`~SampleStatistics.mean_geom`).

        :returns: the geometric mean (:attr:`~SampleStatistics.mean_geom`) of
            all the samples, `None` if the geometric mean is not defined.
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
        Get the :attr:`~SampleStatistics.median` of all the samples.

        :returns: the :attr:`~SampleStatistics.median` of all the samples.
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

    @classmethod
    def from_single_value(cls, value: Union[
            int, float, "StreamStatistics"], n: int = 1) -> "SampleStatistics":
        r"""
        Create a sample statistics from a single number.

        :param value: the single value
        :param n: the number of samples, i.e., the number of times this value
            occurred
        :returns: the sample statistics

        >>> s = SampleStatistics.from_single_value(10, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
        ...     == s.median == 10
        True
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(10, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
        ...     == s.median == 10
        True
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(-10, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == s.median == -10
        True
        >>> print(s.mean_geom)
        None
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(-10, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == s.median == -10
        True
        >>> print(s.mean_geom)
        None
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(10.5, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
        ...     == s.median == 10.5
        True
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(10.5, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == s.mean_geom \
        ...     == s.median == 10.5
        True
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(-10.5, 2)
        >>> print(s.stddev)
        0
        >>> s.minimum == s.maximum == s.mean_arith == s.median == -10.5
        True
        >>> print(s.mean_geom)
        None
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> s = SampleStatistics.from_single_value(-10.5, 1)
        >>> print(s.stddev)
        None
        >>> s.minimum == s.maximum == s.mean_arith == s.median == -10.5
        True
        >>> print(s.mean_geom)
        None
        >>> s is SampleStatistics.from_single_value(s, s.n)
        True

        >>> print(SampleStatistics.from_single_value(
        ...     StreamStatistics(5, 1, 1, 1, 0), 5))
        5;1;1;1;1;1;0

        >>> try:
        ...     SampleStatistics.from_single_value(StreamStatistics(
        ...         5, 1, 2, 3, 5), 5)
        ... except ValueError as ve:
        ...     print(ve)
        Cannot create SampleStatistics from 5;1;2;3;5.

        >>> try:
        ...     SampleStatistics.from_single_value(None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        value should be an i

        >>> try:
        ...     SampleStatistics.from_single_value("a")
        ... except TypeError as te:
        ...     print(str(te)[:20])
        value should be an i

        >>> try:
        ...     SampleStatistics.from_single_value(1, None)
        ... except TypeError as te:
        ...     print(str(te)[:20])
        n should be an insta

        >>> try:
        ...     SampleStatistics.from_single_value(1, "a")
        ... except TypeError as te:
        ...     print(str(te)[:20])
        n should be an insta

        >>> try:
        ...     SampleStatistics.from_single_value(s, 12)
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        Incompatible numbers

        >>> try:
        ...     SampleStatistics.from_single_value(inf)
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        value=inf is not fin
        """
        n = check_int_range(n, "n", 1, 1_000_000_000_000_000_000)

        if isinstance(value, StreamStatistics):
            if value.n != n:
                raise ValueError(  # noqa: TRY004
                    f"Incompatible numbers of values {n} and {value}.")
            if isinstance(value, SampleStatistics):
                return value
            if value.maximum != value.minimum:
                raise ValueError(
                    f"Cannot create SampleStatistics from {value}.")
            value = value.maximum
        if not isinstance(value, int | float):
            raise type_error(value, "value", (int, float, SampleStatistics))
        if not isfinite(value):
            raise ValueError(f"value={value} is not finite.")
        return SampleStatistics(
            n=n, minimum=value, median=value, mean_arith=value,
            mean_geom=None if value <= 0 else value, maximum=value,
            stddev=None if n <= 1 else 0)

    @classmethod
    def aggregate(cls) -> StreamStatisticsAggregate["SampleStatistics"]:
        """
        Get an aggregate suitable for this statistics type.

        :return: the aggregate

        >>> ag = SampleStatistics.aggregate()
        >>> ag.update((1, 2, 3, 4))
        >>> ag.result()
        SampleStatistics(n=4, minimum=1, mean_arith=2.5, maximum=4, \
stddev=1.2909944487358056, median=2.5, mean_geom=2.213363839400643)
        >>> ag.reset()
        >>> ag.add(4)
        >>> ag.add(5)
        >>> ag.add(6)
        >>> ag.add(7)
        >>> ag.result()
        SampleStatistics(n=4, minimum=4, mean_arith=5.5, maximum=7, \
stddev=1.2909944487358056, median=5.5, mean_geom=5.383563270955295)
        """
        return _SampleStats()

    @classmethod
    def from_samples(cls, source: Iterable[
            int | float | None]) -> "SampleStatistics":
        """
        Create a statistics object from an iterable of integers or floats.

        As bottom line, this function will forward computations to the
        :mod:`statistics` routines that ship with Python if nothing else works.
        However, sometimes, something else may work: In particular, if the data
        consists of only integers. In this case, it just might be possible to
        compute the statistics very accurately with integer precision, where
        possible. Also, otherwise, we can often accummulate the data using
        instances of :class:`fractions.Fraction`. Indeed, even the
        :mod:`statistics` routines may do this, but they convert to `float` in
        cases of non-1 denominators, even if the integer presentation was much
        more accurate.

        :param source: the source
        :returns: a statistics representing the statistics over `source`

        >>> s = SampleStatistics.from_samples([0.0])
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

        >>> s = SampleStatistics.from_samples([1.0])
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

        >>> s = SampleStatistics.from_samples([1.0, 1])
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

        >>> s = SampleStatistics.from_samples([0, 0.0])
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

        >>> from statistics import stdev as stat_stddev
        >>> dd = [1.5, 2.5]
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
        >>> s.n
        4
        >>> s.minimum
        2.5
        >>> s.maximum
        4.9
        >>> print(s.mean_geom)
        3.4971393519216964
        >>> 3.4971393519216964 ** 4
        149.5725
        >>> (3.3 * 2.5 * 3.7 * 4.9) ** 0.25
        3.497139351921697
        >>> s.median
        3.5
        >>> s.stddev
        1.0000000000000002
        >>> stat_stddev(dd)
        1.0000000000000002

        >>> dd = [3, 1, 2, 5]
        >>> s = SampleStatistics.from_samples(dd)
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
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.minimum)
        8
        >>> print(s.maximum)
        16
        >>> print(s.mean_arith)
        12.5
        >>> print(s.median)
        13
        >>> print(s.mean_geom)
        12.197150265022891
        >>> stat_geomean(dd)
        12.19715026502289
        >>> print(s.stddev)
        2.673602092336881
        >>> stat_stddev(dd)
        2.673602092336881

        >>> dd = [3, 4, 7, 14, 15, 16, 26, 28, 29, 30, 31, 31]
        >>> s = SampleStatistics.from_samples(dd)
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
        10.917042556563484
        >>> print(str(stat_stddev(dd))[:-1])
        10.91704255656348

        >>> dd = [375977836981734264856247621159545315,
        ...       1041417453269301410322718941408784761,
        ...       2109650311556162106262064987699051941]
        >>> s = SampleStatistics.from_samples(dd)
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
        938280139276529201997232316081385153
        >>> stat_geomean(dd)
        9.38280139276522e+35

        >>> str(dd[0] * dd[1] * dd[2])[:60]
        '826033329443972563356247815302467930409182372405786485790679'
        >>> str(938280139276529201997232316081385153 ** 3)[:60]
        '826033329443972563356247815302467929164458081790138679285598'
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
        >>> s = SampleStatistics.from_samples(dd)
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
        378318848166864995660791573439112525534046591591759
        >>> stat_geomean(dd)
        3.78318848166862e+50

        >>> print(s.stddev)
        210311926886813737006941586539087921260462032505870
        >>> stat_stddev(dd)
        2.1031192688681374e+50

        >>> dd = [4, 5, 5, 6, 6, 6, 6, 6, 8, 8]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        5.884283961687533
        >>> print(stat_geomean(dd))
        5.884283961687533

        >>> dd = [4, 4, 4, 5, 5, 8]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        4.836542350243914
        >>> print(stat_geomean(dd))
        4.8365423502439135

        >>> dd = [2, 8, 11, 17, 26, 30, 32]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        13.327348017053906
        >>> print(stat_geomean(dd))
        13.327348017053906

        >>> dd = [2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        3.4710522375429465
        >>> print(stat_geomean(dd))
        3.471052237542947

        >>> dd = [3, 4, 4, 5, 6, 8, 8, 8, 8]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        5.653305998922543
        >>> print(stat_geomean(dd))
        5.653305998922543

        >>> dd = [16, 17, 19, 20, 20, 21, 22, 23, 24, 24, 25, 26, 29, 31,
        ...       31, 31, 32, 32, 32]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        24.419566831650357
        >>> print(stat_geomean(dd))
        24.41956683165036

        >>> dd = [66, 68, 69, 70, 72, 73, 73, 79, 81, 87, 94, 99, 100,
        ...       102, 103, 112, 118, 119, 123, 123]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        89.45680043258344
        >>> print(stat_geomean(dd))
        89.45680043258346

        >>> dd = [44, 63, 63, 68, 68, 68, 70, 74, 74, 80, 95, 108, 110, 128]
        >>> s = SampleStatistics.from_samples(dd)
        >>> print(s.mean_geom)
        76.68646417360762
        >>> print(stat_geomean(dd))
        76.68646417360763

        >>> try:
        ...     SampleStatistics.from_samples(None)
        ... except TypeError as te:
        ...     print(te)
        source should be an instance of typing.Iterable but is None.

        >>> SampleStatistics.from_samples((int("3432135447287235494201\
93506618248802478442\
545733127827402743350092428341563721880022852900744775368104117201410\
41"), int("4543178800835483269512609282884075126142677531600199807725\
0558561959304806690567285991174956892786401583087254156"), int("35473\
203294104466229269097724582630304968924904656920211268628173495602053\
843032960943121516556362641127137000879"))).mean_arith
        38408781925110551288804847071749420604746651597990567009597840581\
565913672301929416406528849308895284373981465359

        Corner cases where the standard deviation resulting from compact
        fractions deviates from the standard deviation resulting from
        normalized fractions:

        >>> dd = [-7.737125245533627e+25] * 28
        >>> dd[2] = -7.737125245533626e+25
        >>> s = SampleStatistics.from_samples(dd)
        >>> s.stddev
        1623345050.6245058
        >>> stat_stddev(dd)
        1623345050.6245058
        >>> ddx = tuple(map(_to_frac, dd))
        >>> ds = sum(ddx)
        >>> dss = sum(ddy * ddy for ddy in ddx)
        >>> from math import sqrt
        >>> sqrt((dss - (ds * ds / 28)) / 27)
        1623345050.6245055

        Here the standard deviation becomes meaningless.
        If you compute it based on converting all values to floats, you get
        something like 0.435.
        You get the same result if you represent all values directly as
        Fractions.
        However, if you represent the float values as more compact Fractions,
        i.e., as Fractions that map to the exactly same floats but have smaller
        denominators, you get a standard deviation of 9.32+64.
        Basically, the difference is 65 orders of magnitude.
        But the source numbers would be exactly the same...
        The reason is the limited range of floats.
        >>> dd = (7.588550360256754e+81, int("75885503602567541832791480735\
293707\
29071901715047420004889892225542594864082845697"), int("758855036025675418327\
9148073529370729071901715047420004889892225542594864082845697"), \
7.588550360256754e+81, 7.588550360256754e+81, 7.588550360256754e+81, \
int("7588550360256754183279148073529370729071901715047420004889892225\
542594864082845696"), 7.588550360256754e+81, 7.588550360256754e+81, \
7.588550360256754e+81, 7.588550360256754e+81, int("758855036025675418\
3279148073529370729071901715047420004889892225542594864082845696"), int("7588\
55036025675418327914807352937072907190171504742000488989222554259486408284569\
7"), int("7588550360256754183279148073529370729071901715047420004889892225542\
594864082845696"), int("75885503602567541832791480735293707290719017150474200\
04889892225542594864082845696"), int("758855036025675418327914807352937072907\
1901715047420004889892225542594864082845697"), 7.588550360256754e+81,\
int("7588550360256754183279148073529370729071901715047420004889892225\
542594864082845697"), int("75885503602567541832791480735293707290719017150474\
20004889892225542594864082845697"), int("758855036025675418327914807352937072\
9071901715047420004889892225542594864082845697"), 7.588550360256754e+81, \
int("7588550360256754183279148073529370729071901715047420004889892225\
542594864082845696"), int("75885503602567541832791480735293707290719017150474\
20004889892225542594864082845696"), 7.588550360256754e+81, \
7.588550360256754e+81, int("75885503602567541832791480735293707290719\
01715047420004889892225542594864082845696"), 7.588550360256754e+81, \
7.588550360256754e+81, 7.588550360256754e+81)
        >>> s = SampleStatistics.from_samples(dd)
        >>> s.stddev
        0.4354941703556927
        >>> stat_stddev(dd)
        0.4354941703556927
        >>> ddx = tuple(map(_to_frac, dd))
        >>> ds = sum(ddx)
        >>> dss = sum(ddy * ddy for ddy in ddx)
        >>> _limited_root((dss - (ds * ds / len(dd))) / (len(dd) - 1), 2)
        93206175962530968626911348905791729797971161757128018983942059951
        >>> ddx = tuple(map(Fraction, dd))
        >>> ds = sum(ddx)
        >>> dss = sum(ddy * ddy for ddy in ddx)
        >>> _limited_root((dss - (ds * ds / len(dd))) / (len(dd) - 1), 2)
        0.4354941703556927

        >>> try:
        ...     SampleStatistics.from_samples(1)
        ... except TypeError as te:
        ...     print(te)
        source should be an instance of typing.Iterable but is int, namely 1.

        >>> try:
        ...     SampleStatistics.from_samples([])
        ... except ValueError as ve:
        ...     print(ve)
        Data source cannot be empty.
        """
        if not isinstance(source, Iterable):
            raise type_error(source, "source", Iterable)

        # The median function of statistics would do this anyway, so we may as
        # well do it now.
        data: Final[list[int | float]] = sorted(map(try_int, (
            _s for _s in source if _s is not None)))
        n: Final[int] = list.__len__(data)
        if n <= 0:
            raise ValueError("Data source cannot be empty.")

        minimum: int | float = data[0]  # because data is now sorted
        maximum: int | float = data[-1]  # because data is now sorted
        if (minimum >= maximum) or (n <= 1):  # all data is the same
            return SampleStatistics.from_single_value(minimum, n)

        # Compute the median.
        middle: Final[int] = n >> 1
        median: Final[int | float] = data[middle] if (n & 1) == 1 else (
            _mean_of_two(data[middle - 1], data[middle]))

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
                < _DBL_INT_LIMIT_P_I) else None)
        mean_arith_frac: Fraction | None = None
        mean_geom: int | float | None = None  # don't know the geometric mean
        # Go over the data once and see if we can treat it as all-integer.
        # If yes, then we can compute some statistics very precisely.
        # are all values integers?
        int_sum: int = 0  # the integer sum (for mean, stddev)
        int_sum_sqr: int = 0  # the sum of squares (for stddev)
        int_sum_sqr_2: int = 0  # the sum of squares (for stddev)
        int_prod: int = 1  # the integer product (for geom_mean)
        frac_sum: Fraction = _FRAC_0
        frac_sum_sqr: Fraction = frac_sum
        frac_prod: Fraction = _FRAC_1

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
                  else round(mean_arith))

        for ii, ee in enumerate(data):  # iterate over all data
            if can_int and (not isinstance(ee, int)):
                frac_sum = Fraction(int_sum + ii * shift)
                frac_sum_sqr = Fraction(int_sum_sqr_2)
                frac_prod = Fraction(int_prod)
                can_int = False
            if can_int:  # == ee must be int
                int_sum_sqr_2 += ee * ee  # type: ignore
                int_prod *= ee  # type: ignore
                e: int = ee - shift  # type: ignore
                int_sum += e  # so we can sum exactly
                int_sum_sqr += e * e  # and compute the sum of squares
            else:
                eef = Fraction(ee)
                frac_sum += eef
                frac_sum_sqr += eef * eef
                frac_prod *= eef

        if n > 2:  # mean_arith is None or an approximation
            mean_arith_frac = (Fraction(int_sum, n) + shift) \
                if can_int else (frac_sum / n)
            mean_arith = _from_frac(mean_arith_frac)
        stddev: Final[int | float] = _limited_root(((int_sum_sqr - Fraction(
            int_sum * int_sum, n)) if can_int else (frac_sum_sqr - (
                frac_sum * frac_sum / n))) / (n - 1), 2)

        if minimum > 0:  # geometric mean only defined for all-positive
            if can_int:
                frac_prod = Fraction(int_prod)
            # # mean_geom always <= mean_arith
            mean_geom = _limited_root(
                frac_prod, n, _to_frac(minimum), min(
                    _to_frac(maximum), (Fraction(mean_arith) if isinstance(
                        mean_arith, int) else Fraction(nextafter(
                            mean_arith, inf))) if (mean_arith_frac is None)
                    else mean_arith_frac))

        if (mean_geom is None) and (minimum > 0):
            mean_geom = stat_geomean(data)

        if mean_geom is not None:
            # Deal with errors that may have arisen due to
            # numerical imprecision.
            if mean_geom < minimum:
                if _almost_le(minimum, mean_geom):
                    mean_geom = minimum
                else:
                    raise ValueError(
                        f"mean_geom={mean_geom} but min={minimum}")
            if mean_arith < mean_geom:
                if _almost_le(mean_geom, mean_arith):
                    mean_geom = mean_arith
                else:
                    raise ValueError(
                        f"mean_geom={mean_geom} but mean_arith={mean_arith}")

        return SampleStatistics(minimum=minimum, median=median,
                                mean_arith=mean_arith, mean_geom=mean_geom,
                                maximum=maximum, stddev=stddev, n=n)


class CsvReader(CsvReaderBase[SampleStatistics]):
    """
    A csv parser for sample statistics.

    >>> from pycommons.io.csv import csv_read
    >>> csv = ["n;min;mean;med;geom;max;sd",
    ...        "3;2;3;4;3;10;5", "6;2;;;;;0", "1;;;2;;;", "3;;;;;0;",
    ...        "4;5;12;32;11;33;7"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    3;2;4;3;3;10;5
    6;2;2;2;2;2;0
    1;2;2;2;2;2;None
    3;0;0;0;None;0;0
    4;5;32;12;11;33;7

    >>> csv = ["value", "1", "3", "0", "-5", "7"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    1;1;1;1;1;1;None
    1;3;3;3;3;3;None
    1;0;0;0;None;0;None
    1;-5;-5;-5;None;-5;None
    1;7;7;7;7;7;None

    >>> csv = ["n;m;sd", "1;3;", "3;5;0"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
    1;3;3;3;3;3;None
    3;5;5;5;5;5;0

    >>> csv = ["n;m", "1;3", "3;5"]
    >>> for p in csv_read(csv, CsvReader, CsvReader.parse_row):
    ...     print(p)
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
        :returns: the sample statistics

        >>> cc = CsvReader({KEY_MINIMUM: 0, KEY_MEAN_ARITH: 1, KEY_MAXIMUM: 2,
        ...                 KEY_STDDEV: 3, KEY_MEDIAN: 4, KEY_MEAN_GEOM: 5,
        ...                 KEY_N: 6})
        >>> try:
        ...     cc.parse_row([None, None, None, None, None, None, "5"])
        ... except ValueError as ve:
        ...     print(str(ve)[:20])
        No value defined for
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
        :returns: the sample statistic, if the row contains data, else `None`

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


class CsvWriter(CsvWriterBase[SampleStatistics]):
    """A class for CSV writing of :class:`SampleStatistics`."""

    def __init__(self,
                 data: Iterable[SampleStatistics],
                 scope: str | None = None,
                 n_not_needed: bool = False,
                 what_short: str | None = None,
                 what_long: str | None = None) -> None:
        """
        Initialize the csv writer.

        :param data: the data to use
        :param scope: the prefix to be pre-pended to all columns
        :param n_not_needed: should we omit the `n` column?
        :param what_short: the short description of what the statistics is
            about
        :param what_long: the long statistics of what the statistics is about

        >>> try:
        ...     CsvWriter([], None, n_not_needed=None)
        ... except TypeError as te:
        ...     print(te)
        n_not_needed should be an instance of bool but is None.

        >>> try:
        ...     CsvWriter([])
        ... except ValueError as ve:
        ...     s = str(ve)
        ...     print(s[s.index(' ') + 1:])
        CsvWriter did not see any data.

        >>> try:
        ...     CsvWriter([1])
        ... except TypeError as te:
        ...     print(str(te)[:60])
        data[0] should be an instance of pycommons.math.sample_stati
        """
        super().__init__(data, scope, n_not_needed, what_short, what_long,
                         SampleStatistics)


class _SampleStats(StreamStatisticsAggregate[SampleStatistics]):
    """The internal sample statistics aggregate."""

    def __init__(self) -> None:
        """Initialize the stream statistics."""
        #: the internal data list
        self.__lst: Final[list[int | float]] = []

    def reset(self) -> None:
        """Reset the sample statistics."""
        self.__lst.clear()

    def add(self, value: int | float) -> None:
        """
        Add a value to the statistics.

        :param value: the value
        """
        self.__lst.append(try_int(value))

    def update(self, data: Iterable[int | float | None]) -> None:
        """
        Add a stream of data.

        :param data: the data stream
        """
        self.__lst.extend(_s for _s in data if _s is not None)

    def result(self) -> SampleStatistics:
        """
        Get the arithmetic mean.

        :return: the arithmetic mean or `None` if no value was added yet
        """
        return SampleStatistics.from_samples(self.__lst)
