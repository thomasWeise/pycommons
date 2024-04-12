"""
Mathematics routines combining integers and floats.

These routines try to return results with the highest possible precision,
ideally as integers.
If floating point values need to be converted to integers, then we round
towards the nearest integer numbers, whereas `0.5` is always rounded up and
`-0.5` is always rounded down.
Thus, `1.5` becomes `2` and `-1.5` becomes `-2`.
"""

from contextlib import suppress
from math import gcd, isfinite, isqrt, sqrt
from sys import float_info
from typing import Final

from pycommons.types import type_error

#: The positive limit for doubles that can be represented exactly as ints.
#: We cannot represent any number `z` with `|z| >= 2 ** 53` as float without
#: losing some digits, because floats have only 52 bits.
#: `float(9007199254740992) == 9007199254740992.0`
#: `float(9007199254740991) == 9007199254740991.0`
#: But:
#: #: `float(9007199254740993) == 9007199254740992.0`.
__DBL_INT_LIMIT_P_I: Final[int] = 2 ** float_info.mant_dig
#: The positive limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_P_F: Final[float] = float(__DBL_INT_LIMIT_P_I)  # = 1 << 53
#: The negative limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_N_I: Final[int] = -__DBL_INT_LIMIT_P_I
#: The negative limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_N_F: Final[float] = __DBL_INT_LIMIT_N_I


def __try_int(val: float) -> int | float:
    """
    Convert a float to an int without any fancy checks.

    :param val: the flot
    :returns: the float or int

    >>> from math import inf, nan, nextafter
    >>> type(__try_int(0.0))
    <class 'int'>
    >>> type(__try_int(0.5))
    <class 'float'>
    >>> type(__try_int(inf))
    <class 'float'>
    >>> type(__try_int(-inf))
    <class 'float'>
    >>> type(__try_int(nan))
    <class 'float'>
    >>> 1 << 53
    9007199254740992
    >>> type(__try_int(9007199254740992.0))
    <class 'int'>
    >>> __try_int(9007199254740992.0)
    9007199254740992
    >>> too_big = nextafter(9007199254740992.0, inf)
    >>> print(too_big)
    9007199254740994.0
    >>> type(__try_int(too_big))
    <class 'float'>
    >>> type(__try_int(-9007199254740992.0))
    <class 'int'>
    >>> __try_int(-9007199254740992.0)
    -9007199254740992
    >>> type(__try_int(-too_big))
    <class 'float'>
    """
    if __DBL_INT_LIMIT_N_F <= val <= __DBL_INT_LIMIT_P_F:
        a = int(val)
        if a == val:
            return a
    return val


def try_int(value: int | float) -> int | float:
    """
    Attempt to convert a float to an integer.

    This method will convert a floating point number to an integer if the
    floating point number was representing an exact integer. This is the
    case if it has a) no fractional part and b) is in the range
    `-9007199254740992...9007199254740992`, i.e., the range where `+1` and
    `-1` work without loss of precision.

    :param value: the input value, which must either be `int` or `float`
    :return: an `int` if `value` can be represented as `int` without loss of
        precision, `val` otherwise
    :raises TypeError: if `value` is neither an instance of `int` nor of
        `float`
    :raises ValueError: if `value` is a `float`, but not finite

    >>> print(type(try_int(10.5)))
    <class 'float'>
    >>> print(type(try_int(10)))
    <class 'int'>

    >>> from math import inf, nan, nextafter
    >>> type(try_int(0.0))
    <class 'int'>
    >>> type(try_int(0.5))
    <class 'float'>

    >>> try:
    ...     try_int(inf)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is inf.

    >>> try:
    ...     try_int(-inf)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is -inf.

    >>> try:
    ...     try_int(nan)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is nan.

    >>> try:
    ...     try_int("blab")  # noqa  # type: off
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is str, namely \
'blab'.

    >>> type(try_int(9007199254740992.0))
    <class 'int'>
    >>> try_int(9007199254740992.0)
    9007199254740992
    >>> too_big = nextafter(9007199254740992.0, inf)
    >>> print(too_big)
    9007199254740994.0
    >>> type(try_int(too_big))
    <class 'float'>
    >>> type(try_int(-9007199254740992.0))
    <class 'int'>
    >>> try_int(-9007199254740992.0)
    -9007199254740992
    >>> type(try_int(-too_big))
    <class 'float'>
    """
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError(f"Value must be finite, but is {value}.")
        if __DBL_INT_LIMIT_N_F <= value <= __DBL_INT_LIMIT_P_F:
            a = int(value)
            if a == value:
                return a
        return value
    raise type_error(value, "value", (int, float))


def float_to_frac(value: int | float) -> tuple[int, int]:
    """
    Turn a floating point number into an integer fraction.

    If we want to translate a floating point number to an integer fraction,
    then we have several possible ways to go about this. The reason is that,
    due to the loss in precision when representing fractions as floating point
    numbers, several different integer fractions can produce the exactly same
    floating point number.

    One choice would be to use :meth:`float.as_integer_ratio`, which turns the
    binary representation of the floating point number to an integer fraction.
    This is the canonical way that, without losing any precision, will return
    an integer fraction that fits exactly to the floating point value.

    However, as said, there may be multiple such fractions. And some of them
    may be more "compact" than others.

    A second approach would be to first represent the floating point value as
    a string. The string that this produces also represents exactly this
    floating point value, obviously. Now we can translate the string to a
    fraction - and this can give us a different result.

    Which of the two is right?

    Both of them are. Kind of. So I'd figure we test both and stick with the
    :meth:`float.as_integer_ratio` default result - unless the string path
    provides a more compact representation. As simple yard stick let's use
    `|numerator| + denominator` and pick whichever fraction gives us the
    smallest value.

    :param value: the floating point value
    :return: the integer fraction
    :raises TypeError: if value is neither an integer nor a float
    :raises ValueError: if value is not finite

    >>> float_to_frac(0.1)
    (1, 10)

    >>> float_to_frac(1e-1)
    (1, 10)

    >>> float_to_frac(1e-20)
    (1, 100000000000000000000)

    >>> 1e-20.as_integer_ratio()
    (6646139978924579, 664613997892457936451903530140172288)

    >>> float_to_frac(1e-30)
    (1, 1000000000000000000000000000000)

    >>> float_to_frac(1e30)
    (1000000000000000000000000000000, 1)

    >>> float_to_frac(1000)
    (1000, 1)

    >>> float_to_frac(1000.567)
    (1000567, 1000)

    >>> float_to_frac(1.234e-5)
    (617, 50000000)

    >>> float_to_frac(1.234e5)
    (123400, 1)

    >>> float_to_frac(0)
    (0, 1)
    >>> 0 / 1
    0.0

    >>> float_to_frac(-5376935265607590)
    (-5376935265607590, 1)
    >>> -5376935265607590 / 1
    -5376935265607590.0

    >>> float_to_frac(4)
    (4, 1)
    >>> 4 / 1
    4.0

    >>> float_to_frac(-21844.45693689149)
    (-2184445693689149, 100000000000)
    >>> -2184445693689149 / 100000000000
    -21844.45693689149

    >>> float_to_frac(-3010907.436657168)
    (-188181714791073, 62500000)
    >>> -188181714791073 / 62500000
    -3010907.436657168

    >>> float_to_frac(13660.023207762431)
    (1877419294078101, 137438953472)
    >>> 1877419294078101 / 137438953472
    13660.023207762431

    >>> float_to_frac(438027.68586526066)
    (58791080797933, 134217728)
    >>> 58791080797933 / 134217728
    438027.68586526066

    >>> float_to_frac(-8338355882.478134)
    (-546462491114087, 65536)
    >>> -546462491114087 / 65536
    -8338355882.478134

    >>> float_to_frac(-32835294.95774138)
    (-275442417964869, 8388608)
    >>> -275442417964869 / 8388608
    -32835294.95774138

    >>> float_to_frac(-0.8436071305882418)
    (-3799268758964299, 4503599627370496)
    >>> -3799268758964299 / 4503599627370496
    -0.8436071305882418

    >>> float_to_frac(-971533.786640197)
    (-32599264379521, 33554432)
    >>> -32599264379521 / 33554432
    -971533.786640197

    >>> float_to_frac(187487280836.01147)
    (767947902304303, 4096)
    >>> 767947902304303 / 4096
    187487280836.01147

    >>> float_to_frac(24214223389953.125)
    (193713787119625, 8)
    >>> 193713787119625 / 8
    24214223389953.125

    >>> float_to_frac(2645.112807929305)
    (363541536137187, 137438953472)
    >>> 363541536137187 / 137438953472
    2645.112807929305

    >>> float_to_frac(92129361.64291245)
    (1545674200225257, 16777216)
    >>> 1545674200225257 / 16777216
    92129361.64291245

    >>> float_to_frac(7218177.564653773)
    (1937614786056805, 268435456)
    >>> 1937614786056805 / 268435456
    7218177.564653773

    >>> float_to_frac(-1.4589908563595052e+16)
    (-14589908563595052, 1)
    >>> -14589908563595052 / 1
    -1.4589908563595052e+16

    >>> float_to_frac(-1.607745417434216e+16)
    (-16077454174342160, 1)
    >>> -16077454174342160 / 1
    -1.607745417434216e+16

    >>> float_to_frac(-952261813.8291152)
    (-595163633643197, 625000)
    >>> -595163633643197 / 625000
    -952261813.8291152

    >>> float_to_frac(124.69515801820336)
    (779344737613771, 6250000000000)
    >>> 779344737613771 / 6250000000000
    124.69515801820336

    >>> float_to_frac(1.041491959175676e+16)
    (10414919591756760, 1)
    >>> 10414919591756760 / 1
    1.041491959175676e+16

    >>> float_to_frac(1.4933667846659504e+16)
    (14933667846659504, 1)
    >>> 14933667846659504 / 1
    1.4933667846659504e+16

    >>> float_to_frac(-6.034817133993009e-05)
    (-271784001959, 4503599627370496)
    >>> -271784001959 / 4503599627370496
    -6.034817133993009e-05

    >>> float_to_frac(-2.682658826813622e-05)
    (-1887753327, 70368744177664)
    >>> -1887753327 / 70368744177664
    -2.682658826813622e-05

    >>> float_to_frac(6.342974725370709e-05)
    (17853886631, 281474976710656)
    >>> 17853886631 / 281474976710656
    6.342974725370709e-05

    >>> float_to_frac(8.759559844406795e-05)
    (3081996129, 35184372088832)
    >>> 3081996129 / 35184372088832
    8.759559844406795e-05

    >>> float_to_frac(-9.6e-09)
    (-3, 312500000)
    >>> -3 / 312500000
    -9.6e-09

    >>> float_to_frac(-0.4)
    (-2, 5)
    >>> -2 / 5
    -0.4

    >>> float_to_frac(2e-10)
    (1, 5000000000)
    >>> 1 / 5000000000
    2e-10

    >>> float_to_frac(0.3)
    (3, 10)
    >>> 3 / 10
    0.3

    >>> float_to_frac(-3e-09)
    (-3, 1000000000)
    >>> -3 / 1000000000
    -3e-09

    >>> float_to_frac(1e-07)
    (1, 10000000)
    >>> 1 / 10000000
    1e-07

    >>> float_to_frac(-8e-08)
    (-1, 12500000)
    >>> -1 / 12500000
    -8e-08

    >>> float_to_frac(-0.01)
    (-1, 100)
    >>> -1 / 100
    -0.01

    >>> float_to_frac(1e-08)
    (1, 100000000)
    >>> 1 / 100000000
    1e-08

    >>> float_to_frac(0.01)
    (1, 100)
    >>> 1 / 100
    0.01

    >>> float_to_frac(-2e-06)
    (-1, 500000)
    >>> -1 / 500000
    -2e-06

    >>> float_to_frac(-6e-08)
    (-3, 50000000)
    >>> -3 / 50000000
    -6e-08

    >>> float_to_frac(7e-05)
    (7, 100000)
    >>> 7 / 100000
    7e-05

    >>> float_to_frac(-1e+40)
    (-10000000000000000000000000000000000000000, 1)
    >>> -10000000000000000000000000000000000000000 / 1
    -1e+40

    >>> float_to_frac(1e+40)
    (10000000000000000000000000000000000000000, 1)
    >>> 10000000000000000000000000000000000000000 / 1
    1e+40
    """
    value = try_int(value)
    if isinstance(value, int):
        return value, 1

    # First, we convert the floating point number to a string, which
    # necessarily exactly represents the value. Then we will go and turn
    # the string into a fraction.
    value_str: Final[str] = float.__repr__(value)
    minus: Final[bool] = value_str[0] == "-"

    start_idx: int = 1 if minus else 0
    end_idx: int = str.__len__(value_str)
    dot_idx: Final[int] = str.find(value_str, ".")
    exp_idx: Final[int] = str.find(value_str, "e")

    int_denominator: int = 1
    int_multiplier: int = 1
    if exp_idx > 0:
        int_exp = int(value_str[exp_idx + 1:end_idx])
        if int_exp < 0:
            int_denominator = 10 ** (-int_exp)
        else:
            int_multiplier = 10 ** int_exp
        end_idx = exp_idx

    int_numerator: int = 0
    if dot_idx >= 0:
        int_denom_2 = 10 ** (end_idx - dot_idx - 1)
        int_numerator = ((int(value_str[start_idx:dot_idx]) * int_denom_2)
                         + int(value_str[dot_idx + 1:end_idx]))
        int_denominator *= int_denom_2
    else:
        int_numerator = int(value_str[start_idx:end_idx])

    int_numerator *= int_multiplier
    divi: Final[int] = gcd(int_numerator, int_denominator)
    int_numerator = int_numerator // divi
    int_denominator = int_denominator // divi

    str_size: Final[int] = int_numerator + int_denominator
    if minus:  # pack the minus back into the numerator, if needed
        int_numerator = -int_numerator

    # This is the default way that produces exact fractional representations
    # based on the binary layout. We will prefer this way, unless the
    # string-based approach delivers a more compact fraction.
    alt_numer, alt_denom = value.as_integer_ratio()
    if ((int_numerator / int_denominator) != value) or (
            (abs(alt_numer) + alt_denom) <= str_size):
        # We stick with the default, unless it leads to verbose fractions.
        return alt_numer, alt_denom

    return int_numerator, int_denominator


def try_int_div(a: int, b: int) -> int | float:
    """
    Try to divide two integers at best precision.

    Floating point divisions can incur some loss of precision. We try
    to avoid this here as much as possible. First, we check if `a` is
    divisible by `b` without any fractional part. If this is true, then
    we can do a pure integer division without loss of any precision.
    In other words, if `a % b == 0`, then `a / b` is itself an integer,
    i.e., can be represented exactly.

    Otherwise, it will have a fractional part, so it would ideally be a
    `float`.
    Well.

    What if the integer `a` is  really large? Converting it to floating
    point number may then incur a loss of precision. And why do we convert
    it to a `float` in the first place? To properly represent the fractional
    part. Because the integer part is `a // b` is an integer. The fractional
    part `f` is then by definition `f = (a % b) // b == (a - b*(a // b)) / b`.
    Obviously, `0<f<1`. It may be entirely possible that we lose several full
    integer *digits* by converting the integer `a` to a `float` ... just to
    then be able to add a fraction `f`. So this loss of precision may be much
    larger than the little fractional part that we would add (which will
    always be in `(0, 1)`. In such a case, it may be much better to stay in
    the realm of integers and instead lose the fractional part. Thus, we also
    test whether multiplying the result of the floating point computation with
    `b` is closer to `a` than integer results rounded in either direction.

    During this procedure, we try to pick the result closest to the original
    value. This, however, may only be possible if we can actually compute the
    difference. If we deal with floating point numbers and integers, some
    integers may simply be too large for being ever converted to a float. In
    this case, we remain entirely in the integer realm and only round if need
    be.

    :param a: the first integer
    :param b: the second integer
    :return: a/b, either as `int` or as `float` but always a finite value
    :raises ZeroDivisionError: if `b==0`
    :raises TypeError: if `a` or `b` are not integers

    >>> print(try_int_div(10, 2))
    5
    >>> print(try_int_div(10, -2))
    -5
    >>> print(try_int_div(-10, 2))
    -5
    >>> print(try_int_div(-10, -2))
    5
    >>> print(type(try_int_div(10, 2)))
    <class 'int'>
    >>> print(try_int_div(10, 3))
    3.3333333333333335
    >>> print(try_int_div(-10, 3))
    -3.3333333333333335
    >>> print(try_int_div(10, -3))
    -3.3333333333333335
    >>> print(try_int_div(-10, -3))
    3.3333333333333335
    >>> print(type(try_int_div(10, 3)))
    <class 'float'>
    >>> print(try_int_div(9007199254740992, 1))
    9007199254740992
    >>> print(try_int_div(2109792310235001520128, 234234))
    9007199254740992
    >>> print(try_int_div(2109792310235001520128, 234235))
    9007160801054503
    >>> print(try_int_div(2109792310235001520128, 234233))
    9007237708755818
    >>> large = 123456789012345678901234567890123456789012345678901234567\
89012345678901234567890123456789012345678901234567890123456789012345678901234\
56789012345678901234567890123456789012345678901234567890123456789012345678901\
23456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
67890123456789012345678901234567890123456789012345678901234567890123456789012\
3456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
678901234567890123456789012345678901234567890

    >>> try:
    ...     large / 1
    ... except OverflowError as oe:
    ...     print(oe)
    integer division result too large for a float
    >>> try_int_div(large, 1)
    123456789012345678901234567890123456789012345678901234567\
89012345678901234567890123456789012345678901234567890123456789012345678901234\
56789012345678901234567890123456789012345678901234567890123456789012345678901\
23456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
67890123456789012345678901234567890123456789012345678901234567890123456789012\
3456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
678901234567890123456789012345678901234567890

    >>> try_int_div(large * 7, 1 * 7)
    123456789012345678901234567890123456789012345678901234567\
89012345678901234567890123456789012345678901234567890123456789012345678901234\
56789012345678901234567890123456789012345678901234567890123456789012345678901\
23456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
67890123456789012345678901234567890123456789012345678901234567890123456789012\
3456789012345678901234567890123456789012345678901234567890123456789012345678\
90123456789012345678901234567890123456789012345678901234567890123456789012345\
678901234567890123456789012345678901234567890

    >>> res = try_int_div(large, 7)
    >>> print(res)
    1763668414462081127160493827001763668414462081127160493827001763668414462\
08112716049382700176366841446208112716049382700176366841446208112716049382700\
17636684144620811271604938270017636684144620811271604938270017636684144620811\
27160493827001763668414462081127160493827001763668414462081127160493827001763\
66841446208112716049382700176366841446208112716049382700176366841446208112716\
04938270017636684144620811271604938270017636684144620811271604938270017636684\
14462081127160493827001763668414462081127160493827001763668414462081127160493\
82700176366841446208112716049382700176366841446208112716049382700176366841446\
208112716049382700176366841
    >>> large - (res * 7)
    3

    >>> res = try_int_div(large - 1, 7)
    >>> print(res)
    1763668414462081127160493827001763668414462081127160493827001763668414462\
08112716049382700176366841446208112716049382700176366841446208112716049382700\
17636684144620811271604938270017636684144620811271604938270017636684144620811\
27160493827001763668414462081127160493827001763668414462081127160493827001763\
66841446208112716049382700176366841446208112716049382700176366841446208112716\
04938270017636684144620811271604938270017636684144620811271604938270017636684\
14462081127160493827001763668414462081127160493827001763668414462081127160493\
82700176366841446208112716049382700176366841446208112716049382700176366841446\
208112716049382700176366841
    >>> (large - 1) - (res * 7)
    2

    >>> res = try_int_div(large + 1, 7)
    >>> print(res)
    1763668414462081127160493827001763668414462081127160493827001763668414462\
08112716049382700176366841446208112716049382700176366841446208112716049382700\
17636684144620811271604938270017636684144620811271604938270017636684144620811\
27160493827001763668414462081127160493827001763668414462081127160493827001763\
66841446208112716049382700176366841446208112716049382700176366841446208112716\
04938270017636684144620811271604938270017636684144620811271604938270017636684\
14462081127160493827001763668414462081127160493827001763668414462081127160493\
82700176366841446208112716049382700176366841446208112716049382700176366841446\
208112716049382700176366842
    >>> (large + 1) - (res * 7)
    -3

    >>> try:
    ...     try_int_div(0, 0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try:
    ...     try_int_div(1, 0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try:
    ...     try_int_div(-1, 0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try_int_div(153, 17)
    9
    >>> try_int_div(-153, 17)
    -9
    >>> try_int_div(626240198453350272215815210991, 180)
    3479112213629723734532306728
    >>> try_int_div(-626240198453350272215815210991, 180)
    -3479112213629723734532306728
    >>> try_int_div(312641328808813509022862142116, 184)
    1699137656569638635993815990
    >>> try_int_div(-312641328808813509022862142116, 184)
    -1699137656569638635993815990
    >>> try_int_div(300228563787891776398328530521, 6)
    50038093964648629399721421754
    >>> try_int_div(300228563787891776398328530520, 6)
    50038093964648629399721421753
    >>> try_int_div(-300228563787891776398328530521, 6)
    -50038093964648629399721421754

    >>> try_int_div(153, -17)
    -9
    >>> try_int_div(-153, -17)
    9
    >>> try_int_div(626240198453350272215815210991, -180)
    -3479112213629723734532306728
    >>> try_int_div(-626240198453350272215815210991, -180)
    3479112213629723734532306728
    >>> try_int_div(312641328808813509022862142116, -184)
    -1699137656569638635993815990
    >>> try_int_div(-312641328808813509022862142116, -184)
    1699137656569638635993815990
    >>> try_int_div(300228563787891776398328530521, -6)
    -50038093964648629399721421754
    >>> try_int_div(-300228563787891776398328530521, -6)
    50038093964648629399721421754

    >>> try_int_div(471560594207063922064065980174, 160)
    2947253713794149512900412376

    >>> try_int_div(7995687632, 605623302520652727304862084393)
    1.3202410803417417e-20

    >>> try_int_div(308201705551808339041017943851, 23)
    13400074154426449523522519298

    >>> try_int_div(899348944156468188933109403939, 54)
    16654610076971633128390914888

    >>> try_int_div(494818043590514116668712249977, 42)
    11781381990250336111159815476

    >>> try_int_div(738070379515233920, 205)
    3600343314708458

    >>> try_int_div(3502315235185234554036893628, 2914324106703)
    1201759003787480

    >>> try_int_div(7410628973168661103, 3869)
    1915386139356076.8

    >>> try_int_div(1230161216449799063065724370370, 4689247521470)
    262336592559346126

    >>> try_int_div(1052870426843577701006624798274, 28)
    37602515244413489321665171367

    >>> try_int_div(218235816140080518429116, 65180391)
    3348182065064330.5

    >>> try_int_div(542681063252950460111634072, 1417)
    382978873149576894927053

    >>> try_int_div(6347580784084238615827, 9508617)
    667560885466754.9

    >>> try_int_div(25864142832167873073008, 8621014)
    3000127691727199.5

    >>> try_int_div(35377667634669293542601414338, 8678403583)
    4076517909811212054

    >>> try_int_div(1423204593957046760175, 6)
    237200765659507793363

    >>> try_int_div(1959151753859121847452742, 155502)
    12598884605079817928

    >>> try_int_div(153429321515534965993379305, 15165212220)
    10117189215010864

    >>> try_int_div(638685779810794590594721888599, 6355644831674)
    100491106209686119

    >>> try_int_div(14634805, 3163458943542033136)
    4.626203551614245e-12

    >>> try_int_div(2728490692514068837390, 1134)
    2406076448425104795

    >>> try_int_div(52133244, 2145832361321597595907)
    2.4295115005112346e-14

    >>> try_int_div(989732710522254024, 870)
    1137623805197993.2

    >>> try_int_div(1015, 4100715151904)
    2.475178017494646e-10

    >>> try_int_div(750731, 60649291746)
    1.2378231936228884e-05

    >>> try_int_div(7972413701754221571302566, 1660418690)
    4801447821425222

    >>> try_int_div(356135676699525125944, 46208)
    7707229845471025

    >>> try_int_div(10448177882855961291672, 1739414)
    6006722886475538

    >>> try_int_div(739391142068058031063862, 8456)
    87439822855730609161

    >>> try_int_div(316514845935646909034735039673, 32172)
    9838208564455020173900753

    >>> try_int_div(4158458869534984918534998087, 30)
    138615295651166163951166603

    >>> try_int_div(102306108211747181839762853503, 29118)
    3513500522417308257427119

    >>> all(try_int_div(1, y) == (1 / y) for y in range(2, 10))
    True

    >>> all(try_int_div(2, y) == (2 / y) for y in range(3, 10))
    True

    >>> try_int_div(820432337843942760, 85)
    9652145151105209

    >>> try_int_div(84050617, 3577089862)
    0.023496926340286613

    >>> try_int_div(812060021745358856, 996816531)
    814653445.7356013

    >>> try_int_div(38029336, 472982612237)
    8.040324319775297e-05

    >>> try_int_div(50229909719349513, 9)
    5581101079927724

    >>> try_int_div(61320503685013026, 2728161164469337)
    22.476862614874392

    >>> try_int_div(23134400382350491, 8)
    2891800047793811.5

    >>> try_int_div(12510965, 67561917605841203)
    1.8517776645993746e-10

    >>> try_int_div(27246707584980173, 4)
    6811676896245043

    >>> try_int_div(135385235231741420, 6)
    22564205871956903

    >>> try_int_div(90, 153429501803)
    5.865886217603572e-10

    >>> try_int_div(734553401849288248, 951111)
    772310909924.5916

    >>> try_int_div(9820998979656, 4239082999146)
    2.3167744018304255

    >>> try_int_div(133105116441194557, 17)
    7829712731834974

    >>> try_int_div(1004604250960040176, 14)
    71757446497145727

    >>> try_int_div(246148731190755584, 6)
    41024788531792597

    >>> try_int_div(991564, 72057594037927936)
    1.3760714789867734e-11

    >>> try_int_div(2623725286393384, 139634775865757)
    18.789912972079378

    >>> try_int_div(63010439554808723, 9)
    7001159950534303

    >>> try_int_div(2801452, 427673)
    6.550453266865105

    >>> try_int_div(14177411351567, 349688426689780)
    0.04054298132132421

    >>> try_int_div(126660394112336947, 368)
    344185853566133

    >>> try_int_div(1031427640916897886, 7)
    147346805845271127

    >>> try_int_div(33290935002573849, 2)
    16645467501286925

    >>> try_int_div(209062743096233332, 64)
    3266605360878646

    >>> try_int_div(253174817711179642, 57)
    4441663468617186.5

    >>> try_int_div(29462133006911895, 24943246)
    1181166757.8033707

    >>> try_int_div(93475849985676023, 60673699562)
    1540632.1134276118

    >>> try_int_div(-16, -16)
    1

    >>> try_int_div(242, 150)
    1.6133333333333333

    >>> try_int_div(-547, -698)
    0.7836676217765043

    >>> try_int_div(463, 105)
    4.40952380952381

    >>> try_int_div(-148, -203)
    0.729064039408867

    >>> try_int_div(0, -25)
    0

    >>> try_int_div(24, -177)
    -0.13559322033898305

    >>> try_int_div(-166, 186)
    -0.8924731182795699

    >>> try_int_div(-608143760099358008316, 16)
    -38008985006209875520

    >>> try_int_div(-6917198296130591233, 2932)
    -2359208150112753

    >>> try_int_div(-40068404846647758412, 2431)
    -16482272664190769

    >>> try_int_div(809884532216820092, -80)
    -10123556652710251

    >>> try_int_div(-9428902965475478968, -1946)
    4845273877428304

    >>> try_int_div(94881103250893722164, 174)
    545293696844216794

    >>> try_int_div(558275776531402194, 196)
    2848345798629603

    >>> try_int_div(-5470954588630039684, -1425)
    3839266377985993

    >>> x = 52051907638184435686872083537997907834107397007408814104887055550\
62651162584515572343506336421788506498764827396236326664325857298113627143047\
51960058116028166468699987611855171916670918181477368243402962224866666859483\
27106641344727853102203836313167806475289935694133683049416723665601922267867\
43423073756386687744959209264639678418438341653942959851578625489694262628828\
01502680997461128779292890987864647476268814586685317933377503211673153129336\
03
    >>> y = -1390354761575126197823721816501267487365151253235077143453455350\
42071715351921681111638693456863646113210365045493352
    >>> try_int_div(x, y)
    -374378605207314720094873468836285633819929467061778300817269205498029513\
65402433513265745971266615921400317429877366670340545494622384105823993306348\
52843139170606054848072439314573682429224161889047753873201343420620892557508\
62700497112616274728625215898978448963212698759159253800300962780904741771804\
645167943738988195771748632862162

    >>> x = -2371099749665044990658141554075074237566818135879925492767658755\
91466431785344954996723447284617738104563308335316636469414432945133872626562\
47514537471872530515191642703803616012611248118482218872482697827387761273565\
86825000794528611072492997052827719254891404531142028847153355973782623685875\
55388033455119839506838214696423221276537787120528956164822252461892023157114\
02799038227958323905920667727058869625829951896827916647011550854954614174228\
0327582498733595995697631187168710055335569609973997123439124471957303314220
    >>> y = 23343578649740692313745114608806472033684574464287511781560680643\
78701796266433578371331497
    >>> try_int_div(x, y)
    -101573961098350440775039372298606794268469908577045401233130406288914282\
92918893248309802232281829255680862092165642164462698933290177430764947955661\
87652857199541665161754173953190591131037518696771010612358486878465958542091\
54914381056640460582835505879418330902968200425941036454902030259440742425865\
93440206970165106076445287259870479244010983474198088053313334979762284802017\
1153886834216445854191456742632611734684212485945595091

    >>> x = 40410061884642793201602670149115414017394734761323545080847020296\
25252534757283636685784303675489231680221820894136736092474359799408796002401\
87921742390653841150636438854369236710256224057607718115525186887758631639670\
82468402380054839668544662058030344964306015945683011983835531538788295592437\
65716882229369219075665520432950975969718863463181388344946182200519006147179\
64461315530742161850062785306859778524746068148875909170944464910610460508750\
707051996751159775959805908309
    >>> try_int_div(x, 455824846955327759894405021890034373481341853483437732)
    8865260890133771894279961299939580714408739728863480476996077470796169955\
43085620471927592765951912973058793385603301586629745150439814928912960267883\
66400412702824502182496145839556516762964408587815797906905800899307550385283\
59797468484699310297417864757571840405529641545438878013277855865542975695833\
88146919245416237227940140677498927052487483630425657258239092995434299050034\
021769275549143357256693312576946435784210430

    >>> x = -6232936786190843094006005233017695847240511752635979691082519622\
89671822451515008492890632740917254159586399372900046205300278719490624751881\
76026655230475873682972201137642189143060727745274448518821915960488822897219\
19105433159267999911968464110051361652323090653411336081715581855840751539611\
44549510551090842769903146173949669899963195645511983189442245054559694895154\
28690282113755080383328799009405959846487733552322199361433571441631699077621\
235779724223724145601506861527256455350316142
    >>> y = -672227780379448967615099076221459579351218967417588220
    >>> try_int_div(x, y)
    9272060703401113879042492429626067042706252670698636022710487050821126676\
43853746484009770979124008642489211907343513622775392767108564692587266167738\
93885766234994122772733590708011238049750176667082969644614903930265971589853\
26674807243894898200722561326294551914700598739493395761954564220400052036328\
58909594484124974270252599224045683880122299500249240856446063861849302671425\
05617327729864850535306650812894643758024556770793387750201

    >>> try:
    ...     try_int_div(1.0, 2)
    ... except TypeError as te:
    ...     print(te)
    a should be an instance of int but is float, namely '1.0'.

    >>> try:
    ...     try_int_div(1, 2.0)
    ... except TypeError as te:
    ...     print(te)
    b should be an instance of int but is float, namely '2.0'.
    """
    if not isinstance(a, int):
        raise type_error(a, "a", int)
    if not isinstance(b, int):
        raise type_error(b, "b", int)
    minus: bool = False
    if a < 0:
        minus = True
        a = -a
    if b < 0:
        minus = not minus
        b = -b

    # Let's say a = 762 and b = 204.
    # We first compute the GCD to reduce both sides of the equation.
    the_gcd: Final[int] = gcd(a, b)  # == 6 in the example
    a = a // the_gcd  # == 127 in the example
    b = b // the_gcd  # == 34 in the example

    # First, let's compute the result of the pure integer division.
    int_res_1: Final[int] = a // b  # == 3 in our example
    int_mult_1: Final[int] = int_res_1 * b  # == 102 in the example
    if int_mult_1 == a:  # if there is no rest, then we can stop here
        return -int_res_1 if minus else int_res_1

    int_frac_1: Final[int] = a - int_mult_1  # == 25 in the example
    int_res_2: Final[int] = int_res_1 + 1  # rounding up, == 4 in the example
    # Compute int_frac_2 == (int_res_2 * b - a, but simplified:
    int_frac_2: Final[int] = b - int_frac_1  # == 9 in the example

    # OK, there may be a loss of precision if we do the floating point
    # computation. But we should try it now anyway.
    # if `a` and `b` can exactly be represented as floats (by being not more
    # than `__DBL_INT_LIMIT_P_I`, then we are OK and can directly use the
    # result. Otherwise, if the result is between the lower and the upper
    # limit, then we will also take it. This would mean to basically default
    # to the normal division in Python in cases where it falls into the
    # expected range of possible results.
    with suppress(ArithmeticError):
        float_res = __try_int(a / b)  # == 3.5588235294117645 in the example
        if ((a <= __DBL_INT_LIMIT_P_I) and (b <= __DBL_INT_LIMIT_P_I)) or (
                int_res_1 < float_res < int_res_2):
            return -float_res if minus else float_res

    best_result: Final[int] = \
        int_res_2 if int_frac_2 <= int_frac_1 else int_res_1
    return -best_result if minus else best_result  # fix sign of result


def try_float_int_div(a: int | float, b: int) -> int | float:
    """
    Try to divide a float by an int at best precision.

    :param a: the first number, which is either a float or an int
    :param b: the second number, which must be an int
    :return: `a/b`, but always finite

    :raises ValueError: if either one of the arguments or the final result
        would not be finite
    :raises TypeError: if either one of `a` or `b` is neither an integer nor
        a float

    >>> try_float_int_div(10, 2)
    5

    >>> try_float_int_div(10.0, 2)
    5

    >>> try_float_int_div(10, 3)
    3.3333333333333335

    >>> try_float_int_div(-10, 2)
    -5

    >>> try_float_int_div(-10.2, 2)
    -5.1

    >>> try_float_int_div(-10.0, 2)
    -5

    >>> try_float_int_div(-10, 3)
    -3.3333333333333335

    >>> print(type(try_float_int_div(10.0, 2)))
    <class 'int'>

    >>> print(type(try_float_int_div(10.0, 3)))
    <class 'float'>

    >>> try:
    ...     try_float_int_div(10, 0.5)
    ... except TypeError as te:
    ...     print(te)
    b should be an instance of int but is float, namely '0.5'.

    >>> from math import inf, nan
    >>> try:
    ...     try_float_int_div(1.0, 0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try:
    ...     try_float_int_div(inf, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is inf.

    >>> try:
    ...     try_float_int_div(-inf, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is -inf.

    >>> try:
    ...     try_float_int_div(nan, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is nan.

    >>> try:
    ...     try_float_int_div(1, inf)
    ... except TypeError as te:
    ...     print(te)
    b should be an instance of int but is float, namely 'inf'.

    >>> try:
    ...     try_float_int_div("y", 1)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is str, namely 'y'.

    >>> try:
    ...     try_float_int_div(1, "x")
    ... except TypeError as te:
    ...     print(te)
    b should be an instance of int but is str, namely 'x'.
    """
    if not isinstance(b, int):
        raise type_error(b, "b", int)
    a = try_int(a)
    if isinstance(a, int):
        return try_int_div(a, b)
    return __try_int(a / b)


#: the maximum value of a root that can be computed with floats exactly
__MAX_I_ROOT: Final[int] = __DBL_INT_LIMIT_P_I * __DBL_INT_LIMIT_P_I


def try_int_sqrt(value: int) -> int | float:
    """
    Try to compute the square root of a potentially large integer.

    :param value: the value
    :return: the square root
    :raises ValueError: if `value` is negative
    :raises TypeError: if `value` is not an integer

    >>> try_int_sqrt(0)
    0

    >>> try_int_sqrt(1)
    1

    >>> try_int_sqrt(2)
    1.4142135623730951

    >>> try_int_sqrt(3)
    1.7320508075688772

    >>> try_int_sqrt(4)
    2

    >>> try_int_sqrt(5)
    2.23606797749979

    >>> try_int_sqrt(6)
    2.449489742783178

    >>> try_int_sqrt(7)
    2.6457513110645907

    >>> try_int_sqrt(8)
    2.8284271247461903

    >>> try_int_sqrt(9)
    3

    # exact result: 67108864.0000000074505805969238277
    >>> try_int_sqrt(4503599627370497)
    67108864
    >>> 67108864 * 67108864
    4503599627370496
    >>> sqrt(4503599627370497)
    67108864.0
    >>> sqrt(4503599627370497) * sqrt(4503599627370497)
    4503599627370496.0

    # exact result: 1592262918131443.14115595358963
    >>> try_int_sqrt(2535301200456458802993406410753)
    1592262918131443.2
    >>> sqrt(2535301200456458802993406410753)
    1592262918131443.2

    # exact result: 6369051672525772.564623814
    >>> try_int_sqrt(40564819207303340847894502572033)
    6369051672525773
    >>> sqrt(40564819207303340847894502572033)
    6369051672525773.0

    # exact result: 50952413380206180.51699051486817387
    >>> try_int_sqrt(2596148429267413814265248164610049)
    50952413380206181
    >>> sqrt(2596148429267413814265248164610049)
    5.0952413380206184e+16

    # exact result: 47695509376267.99690952215843525
    >>> try_int_sqrt(2274861614661668407597778085)
    47695509376267.99
    >>> sqrt(2274861614661668407597778085)
    47695509376267.99

    # exact result: 9067560306493833.1123015448971368313360
    >>> try_int_sqrt(82220649911902536690031728766315)
    9067560306493833
    >>> sqrt(82220649911902536690031728766315)
    9067560306493832.0

    >>> try_int_sqrt(1156)
    34
    >>> 34 * 34
    1156
    >>> sqrt(1156)
    34.0
    >>> 34.0 * 34.0
    1156.0

    >>> try_int_sqrt(1005)
    31.701734968294716
    >>> 31.701734968294716 * 31.701734968294716
    1005.0
    >>> sqrt(1005)
    31.701734968294716
    >>> 31.701734968294716 * 31.701734968294716
    1005.0

    exact result: 1098367625620897554397104127853022914763109648022\
928865503114153469686909343624968339609542505832728796367409822636937\
28593951807995466301001184452657840914432
    >>> try_int_sqrt(int("1206411441012088169768424908631547135410050\
450349701156359323012992324468898745458674194715627653148741645085002\
880167432962708099995812635821183919553390204438671018341579206970136\
807811815836079357669821219116858017489215282754293788095448310134150\
6291035205862448784848059094859987648259778470316291228729945882624"))
    10983676256208975543971041278530229147631096480229288655031141534\
696869093436249683396095425058327287963674098226369372859395180799546\
6301001184452657840914432

    # exact result: 112519976.73369080909552361
    >>> try_int_sqrt(12660745164150321)
    112519976.73369081
    >>> 112519976.73369081 * 112519976.73369081
    1.2660745164150322e+16
    >>> sqrt(12660745164150321)
    112519976.7336908
    >>> 112519976.7336908 * 112519976.7336908
    1.2660745164150318e+16

    >>> try_int_sqrt(12369445361672285)
    111218008.26157734
    >>> sqrt(12369445361672285)
    111218008.26157734

    # exact result: 94906265.624251558157461955425
    >>> try_int_sqrt(9007199254740993)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0
    >>> sqrt(9007199254740993)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0

    # exact result: 126969687.206733737782866
    >>> try_int_sqrt(16121301469375805)
    126969687.20673373
    >>> 126969687.20673373 * 126969687.20673373
    1.6121301469375804e+16
    >>> sqrt(16121301469375805)
    126969687.20673373
    >>> 126969687.20673373 * 126969687.20673373
    1.6121301469375804e+16

    # exact result: 94906265.6242515686941740831
    # here we are off a bit!
    >>> try_int_sqrt(9007199254740995)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0
    >>> sqrt(9007199254740995)
    94906265.62425157
    >>> 94906265.62425157 * 94906265.62425157
    9007199254740996.0

    # exact result: 102406758.28296330267545316
    >>> try_int_sqrt(10487144142025273)
    102406758.2829633
    >>> 102406758.2829633 * 102406758.2829633
    1.0487144142025274e+16
    >>> sqrt(10487144142025273)
    102406758.28296329
    >>> 102406758.28296329 * 102406758.28296329
    1.048714414202527e+16

    # exact result: 101168874.5492688823358
    >>> try_int_sqrt(10235141177565705)
    101168874.54926889
    >>> 101168874.54926889 * 101168874.54926889
    1.0235141177565706e+16
    >>> sqrt(10235141177565705)
    101168874.54926887
    >>> 101168874.54926887 * 101168874.54926887
    1.0235141177565702e+16

    # exact result: 123961449.976073299398431984
    >>> try_int_sqrt(15366441080170523)
    123961449.9760733
    >>> 123961449.9760733 * 123961449.9760733
    1.5366441080170522e+16
    >>> sqrt(15366441080170523)
    123961449.97607331
    >>> 123961449.97607331 * 123961449.97607331
    1.5366441080170526e+16

    # exact result: 4760418939079673.01527272985
    >>> try_int_sqrt(22661588475548439582669426672241)
    4760418939079673
    >>> 4760418939079673 * 4760418939079673
    22661588475548439437260241786929
    >>> sqrt(22661588475548439582669426672241)
    4760418939079673.0
    >>> 4760418939079673.0 * 4760418939079673.0
    2.266158847554844e+31

    # exact result: 5712179292532910.79362200453777547
    >>> try_int_sqrt(32628992270041785263905793906381)
    5712179292532911
    >>> 5712179292532911 * 5712179292532911
    32628992270041787621642018133921
    >>> sqrt(32628992270041785263905793906381)
    5712179292532911.0
    >>> 5712179292532911.0 * 5712179292532911.0
    3.2628992270041787e+31

    >>> try:
    ...     try_int_sqrt(-1)
    ... except ValueError as ve:
    ...     print(ve)
    Compute the root of -1 ... really?

    >>> try:
    ...     try_int_sqrt(1.0)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of int but is float, namely '1.0'.
    """
    if not isinstance(value, int):
        raise type_error(value, "value", int)
    if value < 0:
        raise ValueError(f"Compute the root of {value} ... really?")

    # First, let's compute the integer root. This is basically the
    # rounded-down version of the actual root. The integer root (isqrt) is the
    # lower limit for the result.
    # In the odd chance that this is already the correct result, we can
    # directly stop and return it.
    result_low: Final[int] = isqrt(value)
    diff_low: Final[int] = value - (result_low * result_low)
    if diff_low <= 0:
        # Notice: If we get here, then seemingly `isqrt(value) == sqrt(value)`
        # in Python's implementation if `value` the result fits into the
        # float range (I think).
        return result_low

    # First, we use the floating point sqrt for all numbers that can exactly
    # be represented as floating point numbers. Of course we try to convert
    # the result to integers.
    if value <= __DBL_INT_LIMIT_P_I:  # default to the normal Python sqrt.
        return __try_int(sqrt(value))  # we can compute the exact square root

    # `value` is bigger than 2 ** 53 and definitely does not fit into a float
    # without losing precision.
    # We cannot accurately compute the root of value, because transforming
    # value to an int will already lead to a loss of precision.
    # However, what if sqrt(value) < 2 ** 53?
    # In this case, we *could* represent some fractional digits in the
    # result. But we cannot get them using `sqrt`. So we do a trick:
    # `root(a) = root(a * mul * mul) / mul`.
    # We compute the integer square root of `value` times some value `mul`.
    # We pick `mul` just large enough so that the result of
    # `isqrt(mul * mul * value)` will still be `<= __DBL_INT_LIMIT_P_I` and
    # thus fits into a `float` nicely. We then get the approximate fractional
    # part by dividing by `mul`.
    if result_low < __DBL_INT_LIMIT_P_I:
        mul: int = __DBL_INT_LIMIT_P_I // result_low
        if mul > 1:
            # We can proceed like before, just do the integer root at a higher
            # resolution. In this high resolution, we compute both the upper
            # and the lower bound for the root. We then pick the one closer to
            # the actual value, rounding up on draw situations. This value is
            # then divided by the multiplier to give us the maximum precision.
            new_value: Final[int] = value * mul * mul
            new_low: Final[int] = isqrt(new_value)
            new_diff_low: Final[int] = new_value - (new_low * new_low)
            new_high: Final[int] = new_low + 1
            new_diff_high: Final[int] = (new_high * new_high) - new_value
            return try_int_div(
                new_high if new_diff_high <= new_diff_low else new_low, mul)

    #: If we get here, then there is just no way to get useful fractional
    #: parts. We then just check if we should round up the result or return
    #: the rounded-down result.
    result_up: Final[int] = (result_low + 1)
    diff_up: int = (result_up * result_up) - value
    return result_up if diff_up <= diff_low else result_low


def try_int_add(a: int, b: int | float) -> int | float:
    """
    Try to add a floating point number to an integer.

    :param a: the integer
    :param b: the floating point number
    :return: `a + b` or the best possible approximation thereof
    :raises TypeError: if `a` is not an integer or if `b` is neither a
        float nor an integer
    :raises ValueError: if `b` or the result is not finite

    >>> try_int_add(0, -8670.320148166094)
    -8670.320148166094
    >>> 0 + -8670.320148166094
    -8670.320148166094

    >>> try_int_add(-63710, 100.96227261264141)
    -63609.03772738736
    >>> -63710 + 100.96227261264141
    -63609.03772738736

    >>> try_int_add(77, 12975.955050422272)
    13052.955050422272
    >>> 77 + 12975.955050422272
    13052.955050422272

    >>> try_int_add(-308129344193738, 62995516.01169562)
    -308129281198222
    >>> -308129344193738 + 62995516.01169562
    -308129281198222.0

    >>> try_int_add(-2158504468760619, -1.3773316665252534e+16)
    -1.5931821134013152e+16
    >>> -2158504468760619 + -1.3773316665252534e+16
    -1.5931821134013152e+16

    >>> try_int_add(-960433622582960, 1.491132239895968e+16)
    1.395088877637672e+16
    >>> -960433622582960 + 1.491132239895968e+16
    1.395088877637672e+16

    # exact result: 10796862382206072.70684135
    >>> try_int_add(10796862236149287, 146056785.70684135)
    10796862382206073
    >>> 10796862236149287 + 146056785.70684135
    1.0796862382206074e+16

    # exact result: -11909678744561796.5206623
    >>> try_int_add(-11909677351933537, -1392628259.5206623)
    -11909678744561797
    >>> -11909677351933537 + -1392628259.5206623
    -1.1909678744561796e+16

    # exact result: 8991519996993845.25
    >>> try_int_add(9257476766666634, -265956769672788.75)
    8991519996993845
    >>> 9257476766666634 + -265956769672788.75
    8991519996993845.0

    >>> v = int("-9166650131241408540833319855375552663116961087945581\
6489173691561634548053405237489064")
    >>> try_int_add(v, 6.147962494740932e+217)
    6.147962494740932e+217
    >>> v + 6.147962494740932e+217
    6.147962494740932e+217

    exact result: 2060196266381720280000783609573994641953401509142\
0431778715465940577471030.192914550695235
    >>> v = int("2060196266381720280000783609573994641953401509142043\
1778715465940577470980")
    >>> try_int_add(v, 50.192914550695235)
    20601962663817202800007836095739946419534015091420431778715465940\
577471030
    >>> v + 50.192914550695235
    2.0601962663817203e+73

    >>> try:
    ...     try_int_add(2.0, 1)
    ... except TypeError as te:
    ...     print(te)
    a should be an instance of int but is float, namely '2.0'.

    >>> try:
    ...     try_int_add(2, "1")
    ... except TypeError as te:
    ...     print(te)
    b should be an instance of any in {float, int} but is str, namely '1'.

    >>> from math import inf
    >>> try:
    ...     try_int_add(2, inf)
    ... except ValueError as ve:
    ...     print(ve)
    b=inf is not finite
    """
    if not isinstance(a, int):
        raise type_error(a, "a", int)
    if isinstance(b, int):
        return a + b
    if not isinstance(b, float):
        raise type_error(b, "b", (int, float))
    if not isfinite(b):
        raise ValueError(f"b={b} is not finite")

    # First we attempt to turn b into an integer, because that would solve all
    # of our problems.
    b = __try_int(b)
    if isinstance(b, int):
        return a + b  # We are lucky, the result is an integer

    b_num, b_denom = float_to_frac(b)
    int_num: Final[int] = b_num // b_denom
    int_res: Final[int] = a + int_num

    a_exact: Final[bool] = __DBL_INT_LIMIT_N_I < a < __DBL_INT_LIMIT_P_I
    b_exact: Final[bool] = __DBL_INT_LIMIT_N_I < b < __DBL_INT_LIMIT_P_I
    res_exact: Final[bool] = \
        __DBL_INT_LIMIT_N_I < int_res < __DBL_INT_LIMIT_P_I
    if a_exact and b_exact and res_exact:
        # We know that the result should fit well into the float range.
        # So we can just compute it normally
        return __try_int(a + b)

    if not b_exact:
        # Now if we get here, we are in a strange territory.
        # The floating point character of `b` will definitely pollute the
        # result. Regardless of what we do, we will not just have a rounding
        # error that costs us a fractional part, but it will cost decimals.
        # The right thing to do may be to return a float here, because we do
        # know that floats have a limited resolution and the returned value
        # may be biased.
        float_res: Final[float] = a + b
        if isfinite(float_res):
            return __try_int(float_res)

    # If we get here, then b is either an exactly representable float or the
    # result of adding a to b would no longer be finite.
    # If `b` is an exactly represented float, this means that the result does
    # not fit into a float. So we just try to round the result.
    # We will lose a fractional part, but the integer part will be exact.
    # `a` is an integer, so it is exact anyway. The integer part of `b`
    # can be represented as exact integer as well. So this means that we
    # will lose the fractional part only.
    # We can do the same thing if the result of the computation would not be
    # finite. Although it would be a bit pretentious to round in such a
    # situation ... well ... why not.
    b_num -= int_num * b_denom
    round_up: Final[bool] = abs(b_num + b_num) >= b_denom
    return (int_res - 1) if (round_up and (b_num < 0)) else (
        (int_res + 1) if round_up and (b_num > 0) else int_res)


def try_int_mul(a: int, b: int | float) -> int | float:
    """
    Try to multiply an integer with an int or float as exactly as possible.

    :param a: the integer
    :param b: the int or float to multiply `a` with
    :return: `a * b`
    :raises ValueError: if `b` or the result is not finite
    :raises TypeError: if `a` is not an integer or if `b` is neither an
        integer nor a float

    # exact result: -111038109230780524.216538356
    >>> try_int_mul(197262324754, -562895.673916714)
    -111038109230780524
    >>> 197262324754 * -562895.673916714
    -1.1103810923078053e+17

    >>> try_int_mul(4, -2493374.0)
    -9973496
    >>> 4 * -2493374.0
    -9973496.0

    # exact result: -805144077682.7549712841791
    >>> try_int_mul(609329061, -1321.3616897926931)
    -805144077682.755
    >>> 609329061 * -1321.3616897926931
    -805144077682.755

    # exact result: -88939650274621002534.99
    >>> try_int_mul(-6548165, 13582377700412.406)
    -88939650274621004172
    >>> -6548165 * 13582377700412.406
    -8.8939650274621e+19

    >>> try_int_mul(4, 0.687279486538305)
    2.74911794615322
    >>> 4 * 0.687279486538305
    2.74911794615322

    # exact result: -2236563847561524626.733
    >>> try_int_mul(21396228, -104530754091.86725)
    -2236563847561524627
    >>> 21396228 * -104530754091.86725
    -2.2365638475615245e+18

    # exact result: -92649832027598387270282.5408
    >>> try_int_mul(29187432758, -3174305626527.0176)
    -92649832027598386631807
    >>> 29187432758 * -3174305626527.0176
    -9.264983202759838e+22

    # exact result: 47954872443652456553018463.12996
    >>> try_int_mul(-317420410641789, -151076839534.96564)
    47954872443652455666473176
    >>> -317420410641789 * -151076839534.96564
    4.795487244365246e+25

    # exact result: 369200712310299349798.80066193866
    >>> try_int_mul(8136505182920565, 45375.834465796564)
    369200712310299353646
    >>> 8136505182920565 * 45375.834465796564
    3.6920071231029936e+20

    # exact result: 431520767093145743090.73845486
    >>> try_int_mul(40196153594795, 10735374.619252708)
    431520767093145743091
    >>> 40196153594795 * 10735374.619252708
    4.315207670931457e+20

    # exact result: -250242005217172713.52783326
    >>> try_int_mul(27941562579, -8955905.90217194)
    -250242005217172703
    >>> 27941562579 * -8955905.90217194
    -2.502420052171727e+17

    # exact result: -6563728914129924.848948421
    >>> try_int_mul(-672426819, 9761253.906991959)
    -6563728914129925
    >>> -672426819 * 9761253.906991959
    -6563728914129925.0

    >>> try_int_mul(14059, 1.0673811010650016e+16)
    1.5006310899872858e+20
    >>> 14059 * 1.0673811010650016e+16
    1.5006310899872858e+20

    # exact result: 14493050353163113.126430160675
    >>> try_int_mul(240712887635, 60208.867483403505)
    14493050353163113
    >>> 240712887635 * 60208.867483403505
    1.4493050353163114e+16

    # exact result: 805460953505875910367.5205722154
    >>> try_int_mul(1812115257906061, 444486.6020479314)
    805460953505875915662
    >>> 1812115257906061 * 444486.6020479314
    8.054609535058759e+20

    # exact result: -1384354228892504466.5554728510606
    >>> try_int_mul(6815245310862468, -203.12610416033795)
    -1384354228892504435
    >>> 6815245310862468 * -203.12610416033795
    -1.3843542288925043e+18

    # exact result: -572028608656496.423924280629596728
    >>> try_int_mul(11587431214834713, -0.049366300265425656)
    -572028608656496.4
    >>> 11587431214834713 * -0.049366300265425656
    -572028608656496.4

    # exact result: 1128618866534760.28918431873755142
    >>> try_int_mul(16354919666787217, 0.06900791257487526)
    1128618866534760.2
    >>> 16354919666787217 * 0.06900791257487526
    1128618866534760.2

    # exact result: -2507326755278071.50624700782133248
    >>> try_int_mul(13217245192529664, -0.18970116077556032)
    -2507326755278071.5
    >>> 13217245192529664 * -0.18970116077556032
    -2507326755278071.5

    # exact result: 696151526057376.88027486041356184
    >>> try_int_mul(-10333677547666606, -0.06736725844658964)
    696151526057376.9
    >>> -10333677547666606 * -0.06736725844658964
    696151526057376.9

    # exact result: -958450150333374.5128889837837098
    >>> try_int_mul(12016909016999122, -0.0797584594322509)
    -958450150333374.6
    >>> 12016909016999122 * -0.0797584594322509
    -958450150333374.6

    >>> aa = int("1318537368301039863303586092319665276843530233302383387022\
8761465225501763768872549741384158750496877681759291226540877199284501122993\
0897105528797412214008383330709731057075605034370259681835287681493225337651\
3905721656778533145739528500419884652958325779506781860934858448618309985340\
2653730863759125601710698375950989559971436924737005754922330642277477754688\
4919382044527420457991975491785609852030831998308070776211565814942350933642\
672902063132158594646597242361650005228312919254855")
    >>> try_int_mul(aa, -2.6624992899981142e+135)
    -351060480693750064453835292428076534998065626248205859394224131928297807\
37557248636560809666436142921728329271829636053027677161961750893317035607449\
88120284425121093171262696954695038088240282639132134536157970777415620680544\
77787260819949647198753734696904695444416894546646340086090596255528370630342\
39912680252313956743223994856279867123453950294756395973723697089090287742438\
42755397630769057958666859505455598999506335122025009809406354300546655548757\
03308334026066509069233835834019214049819194441000000000000000000000000000000\
00000000000000000000000000000000000000000000000000000000000000000000000000000\
0000000000000

    # exact result: 5115993211447460900.43715653698
    >>> try_int_mul(45247701671134, 113066.36630145647)
    5115993211447460734
    >>> 45247701671134 * 113066.36630145647
    5.115993211447461e+18

    # exact result: -125197981872321984234
    >>> try_int_mul(-15606149727, 8022349142.0)
    -125197981872321984234
    >>> -15606149727 * 8022349142.0
    -1.2519798187232199e+20

    # exact result: -348481045.61578014504
    >>> try_int_mul(6636, -52513.71995415614)
    -348481045.6157802
    >>> 6636 * -52513.71995415614
    -348481045.6157802

    # exact result: -339789407482572717.3787168852228
    >>> try_int_mul(6921658507965838, -49.0907500119406)
    -339789407482572714
    >>> 6921658507965838 * -49.0907500119406
    -3.3978940748257274e+17

    >>> try_int_mul(2366231432701, 9061910680864392.0)
    2.1442577893390244e+28
    >>> 2366231432701 * 9061910680864392.0
    2.1442577893390244e+28

    >>> try_int_mul(11382697409900285, 7338977711.446167)
    8.35373625873942e+25
    >>> 11382697409900285 * 7338977711.446167
    8.35373625873942e+25

    >>> try_int_mul(34207518885, -6554.28955920917)
    -224205983874406
    >>> 34207518885 * -6554.28955920917
    -224205983874406.0

    >>> try_int_mul(35107, -165228482913.08173)
    -5800676349629560
    >>> 35107 * -165228482913.08173
    -5800676349629560.0

    >>> try_int_mul(0, 2.4281702332336544e+16)
    0
    >>> 0 * 2.4281702332336544e+16
    0.0

    >>> try_int_mul(12299117359251193, 9482167930204820.0)
    1.1662229619371705e+32
    >>> 12299117359251193 * 9482167930204820.0
    1.1662229619371705e+32

    >>> try_int_mul(-11025104822925196, 0.20926918490209712)
    -2307214699753735.5
    >>> -11025104822925196 * 0.20926918490209712
    -2307214699753735.5

    >>> try_int_mul(9772540954912922, -0.46316069211643107)
    -4526256832413637
    >>> 9772540954912922 * -0.46316069211643107
    -4526256832413637.0

    >>> a = -5687274133508874816611305835797802819969961090128107452007652532\
73368270677846755602944621609056451583453036433989268229052391280449456056415\
35305434613932448168719851117464179317780697744165312772461358166814824851088\
55666554914988361150741132171265507858468795070096289596042533878836544303330\
51629205606376256678385083639086123757879299418359388159156263956657201968562\
31234444965574888174813926197455099511160764637390234826490840919289969902451\
19032766058028744
    >>> try_int_mul(a, 1.6152587208080178e+161)
    -91864191417760728566594708387860610684587465634907240089126522260899489\
4868393273335550289848260675410562832758047321131061871920910825594187776263\
3813438746416917351911213760538943029477664003307403545581300547688099127531\
5980188627547208265662112980855054467534738906286741579697000621904552812416\
9446067183418151530080010856381487158544646128107795979443668739119314808361\
7661789396847122441264057280246286323595226375142154153566223973380730500186\
0346809116255685129263413549101637215712126487779567515862772796494902477027\
4283909310368263635531679756438464790102625606997105530169121933171318181638\
719123552835758718976000

    >>> a = 3765608478313035700785399638168771339557519363527174997097642640\
6101495713891805694367423527904175961734525627539554843115375392781571623329\
2447297269149929791925360073769054144096521088071580437368293552550840688369\
2608265449974834262318405099511472680054858496169995743896513251354009716226\
2514585220536136586004979988630733951340879593101821106230203914627052267837\
1572821101974821796182780210158355368107881592427373376547394885537235348770\
037983728077456443610490231815763426207048140659081123096064113083255321
    >>> try_int_mul(a, 3.4397561272117625e+192)
    129527748359578257806492201438402698334484205908662618646067106845154998\
2115342535199421721007878815369298874224123455721441548991298088516366970587\
6954884520363675490158067710598514210872880348223211816340777337079830796450\
1538806420032828931583145759690145309074737296451653410762104587461282286330\
5613446806304563553562786109972723062095583351926917494446975708601932868972\
8706300360490387733148782540598727225279861244661365412091714003810616131531\
4481842956460108582107814498584521025354908493431977057047306288665587544613\
6391274648488448957696316691763417067525251280127682030399365602278708061765\
1082290234901228437827481292269177791129383042667337751797004896760132865057\
19242926784445427888800399360

    >>> a = 129139500057625933922412781529753661193714022177289159193286727\
341869510538391068183373334814894358463049932698275602586001788553855337370\
614701810798567624656761308982494637834371899037091828942757328272879402878\
026516716840890321410558877108818475215456025987413249018189775618174448780\
086119164868545066265500186250891155310591180702358002
    >>> try_int_mul(a, 1107055232.6334295)
    14296455927845986412272147350433876910362542595277171600320805129204174\
701824227341993224688128568101787206140720134279287421051283535763162532066\
1082072819079131257940844247255813910836282210665242651249270543058782206016\
0195030665164058974557661094866963676618764040698636345181586979396240926480\
38619836809751492028454165243512720617990761805723389

    >>> try_int_mul(1202489289292969, 2.1583639585424923e+306)
    259540954254332074038246669681477283939748496620440148998643367300751188\
2740876153253237092741716795754997976766921219000512012754932543147420651232\
5520218655906535605653525109031074378131051185629676951714011087271116671446\
0899827404105545452888405653019460560445425746060708059494631661799648373661\
5341276121474415984640

    # exact result: -7952338024951495584.4756757
    >>> try_int_mul(-131722798246, 60371766.54947795)
    -7952338024951495584
    >>> -131722798246 * 60371766.54947795
    -7.952338024951496e+18

    # exact result: 374987726685442496656857448.375
    >>> try_int_mul(-197846874313873, -1895343194002.375)
    374987726685442496656857448
    >>> -197846874313873 * -1895343194002.375
    3.749877266854425e+26

    # exact result: 10775411722410520324.9
    >>> try_int_mul(187295, 57531763914736.22)
    10775411722410520091
    >>> 187295 * 57531763914736.22
    1.077541172241052e+19
    """
    if not isinstance(a, int):
        raise type_error(a, "a", int)
    if isinstance(b, int):
        return a * b
    if not isinstance(b, float):
        raise type_error(b, "b", (int, float))
    if not isfinite(b):
        raise ValueError(f"b={b} is not finite")

    # First we attempt to turn b into an integer, because that would solve all
    # of our problems.
    b = __try_int(b)
    if isinstance(b, int):
        return a * b  # We are lucky, the result is an integer

    minus: bool = False
    if a < 0:
        a = -a
        minus = True
    if b < 0:
        b = -b
        minus = not minus

    # Try to get the result as floating point number
    float_res: int | float | None = None
    with suppress(ArithmeticError):
        float_res = a * b
        float_res = __try_int(float_res) if isfinite(float_res) else None

    # pylint: disable=R0916
    if (float_res is not None) and (isinstance(float_res, int) or (
            a >= __DBL_INT_LIMIT_P_I) or (b >= __DBL_INT_LIMIT_P_I) or (
            (a <= __DBL_INT_LIMIT_P_I) and (b <= __DBL_INT_LIMIT_P_I) and (
            float_res <= __DBL_INT_LIMIT_P_F))):
        # If float_res could be transformed to an int, then we are good.
        # If either a or b are outside of the range where we can represent
        # digits exactly, then there is nothing that we can do and we may
        # as well return the result of the floating point computation.
        # Trying to use integers would suggest a precision that we cannot
        # offer.
        # Alternatively, if everything falls into the range where we do not
        # have a loss of precision, then trying anything would be odd.
        # Using integer precision would be pretentious.
        return -float_res if minus else float_res  # pylint: disable=E1130

    num, denom = float_to_frac(b)
    result = try_int_div(a * num, denom)
    return -result if minus else result
