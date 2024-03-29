"""Integer maths routines."""

from math import gcd, isfinite
from sys import float_info
from typing import Final

from pycommons.types import type_error

#: The positive limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_P_I: Final[int] = 9007199254740992
#: The positive limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_P_F: Final[float] = float(__DBL_INT_LIMIT_P_I)  # = 1 << 53
#: The negative limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_N_I: Final[int] = -__DBL_INT_LIMIT_P_I
#: The negative limit for doubles that can be represented exactly as ints.
__DBL_INT_LIMIT_N_F: Final[float] = float(__DBL_INT_LIMIT_N_I)

#: the maximum float
__MAX_FLOAT: Final[int] = int(float_info.max)


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

    >>> try_int_div(6347580784084238615827, 9508617)
    667560885466754.9

    >>> try_int_div(7410628973168661103, 3869)
    1915386139356076.8

    >>> try_int_div(1230161216449799063065724370370, 4689247521470)
    262336592559346126

    >>> try_int_div(1052870426843577701006624798274, 28)
    37602515244413489321665171367

    >>> try_int_div(218235816140080518429116, 65180391)
    3348182065064331

    >>> try_int_div(542681063252950460111634072, 1417)
    382978873149576894927053

    >>> try_int_div(25864142832167873073008, 8621014)
    3000127691727200

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

    >>> try_int_div(989732710522254024, 870)
    1137623805197993.2

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
    4441663468617187

    >>> try_int_div(29462133006911895, 24943246)
    1181166757.8033707

    >>> try_int_div(93475849985676023, 60673699562)
    1540632.1134276118
    """
    minus: bool = False
    if a < 0:
        minus = True
        a = -a
    if b < 0:
        minus = not minus
        b = -b

    # just in case, try to reduce both values by the gcd
    the_gcd = gcd(a, b)
    use_a = a // the_gcd
    use_b = b // the_gcd

    # if the number is too big, we need to remain in the realm of ints
    int_res: int = use_a // use_b
    int_mult: Final[int] = int_res * use_b
    if int_mult == use_a:
        return -int_res if minus else int_res

    fraction: Final[int] = use_a - int_mult
    if a >= __MAX_FLOAT:  # we cannot compute differences anyway
        fraction_2: Final[int] = (use_b * (int_res + 1)) - use_a
        if fraction_2 <= fraction:
            int_res += 1  # round up if necessary
        return -int_res if minus else int_res

    frac_part: Final[float] = fraction / use_b
    result: float | int = int_res + frac_part
    result_i: Final[int] = int(result)
    if result_i == result:
        result = result_i
    diff: float | int = abs((a - (b * result)) if isinstance(result, int) or (
        a <= __DBL_INT_LIMIT_P_I) else (a - int(round(b * result))))

    if result is not result_i:  # check the actual result for completeness
        result_2: Final[float] = use_a / use_b
        diff_2: Final[float] = abs(a - (b * result_2))
        if diff_2 <= diff:
            result = result_2
            diff = diff_2

    int_res_diff: int = abs(a - (int_res * b))
    overwritten: bool = False
    if int_res_diff <= diff:
        result = int_res
        diff = int_res_diff
        overwritten = True

    int_res += 1
    int_res_diff = abs(a - (b * int_res))
    #  pylint: disable=too-many-boolean-expressions
    if ((not overwritten) and (int_res_diff <= diff)) or (
            overwritten and ((int_res_diff < diff) or (
            (int_res_diff <= diff) and (frac_part >= 0.5)))):
        result = int_res
    #  pylint: enable=too-many-boolean-expressions

    return -result if minus else result


def try_float_div(a: int | float, b: int | float) -> int | float:
    """
    Try to divide two numbers at best precision.

    First, we will check if we can convert the numbers to integers
    without loss of precision via :func:`try_int`. If yes, then
    we go for the maximum-precision integer division via :func:`try_int_div`.
    If no, then we do the normal floating point division and try to convert
    the result to an integer if that can be done without loss of precision.

    :param a: the first number
    :param b: the second number
    :return: `a/b`, but always finite

    :raises ValueError: if either one of the arguments or the final result
        would not be finite

    >>> try_float_div(1e180, 1e60)
    1.0000000000000001e+120
    >>> try_float_div(1e60, 1e-60)
    1e+120
    >>> try_float_div(1e14, 1e-1)
    1000000000000000
    >>> try_float_div(1e14, -1e-1)
    -1000000000000000
    >>> try_float_div(-1e14, 1e-1)
    -1000000000000000
    >>> try_float_div(-1e14, -1e-1)
    1000000000000000
    >>> try_float_div(1e15, 1e-1)
    1e+16
    >>> try_float_div(1e15, -1e-1)
    -1e+16
    >>> try_float_div(-1e15, 1e-1)
    -1e+16
    >>> try_float_div(-1e15, -1e-1)
    1e+16
    >>> try_float_div(1e15, 1e-15)
    9.999999999999999e+29

    >>> print(type(try_float_div(10, 2)))
    <class 'int'>
    >>> print(type(try_float_div(10, 3)))
    <class 'float'>
    >>> print(type(try_float_div(10, 0.5)))
    <class 'int'>

    >>> from math import inf, nan
    >>> try:
    ...     try_float_div(1.0, 0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try:
    ...     try_float_div(1.0, -0.0)
    ... except ZeroDivisionError as zde:
    ...     print(zde)
    integer division or modulo by zero

    >>> try:
    ...     try_float_div(inf, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is inf.

    >>> try:
    ...     try_float_div(-inf, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is -inf.

    >>> try:
    ...     try_float_div(nan, 0)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is nan.

    >>> try:
    ...     try_float_div(1, inf)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is inf.

    >>> try:
    ...     try_float_div(1, -inf)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is -inf.

    >>> try:
    ...     try_float_div(1, nan)
    ... except ValueError as ve:
    ...     print(ve)
    Value must be finite, but is nan.

    >>> try:
    ...     try_float_div(1e300, 1e-60)
    ... except ValueError as ve:
    ...     print(ve)
    Result must be finite, but is 1e+300/1e-60=inf.
    """
    ia: Final[int | float] = try_int(a)
    ib: Final[int | float] = try_int(b)
    if isinstance(ia, int) and isinstance(ib, int):
        return try_int_div(ia, ib)
    val: Final[float] = ia / ib
    if not isfinite(val):
        raise ValueError(f"Result must be finite, but is {a}/{b}={val}.")
    return __try_int(val)
