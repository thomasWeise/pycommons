"""Integer maths routines."""

from contextlib import suppress
from math import gcd, isfinite, isqrt, sqrt
from typing import Final

from pycommons.types import type_error

#: The positive limit for doubles that can be represented exactly as ints.
#: We cannot represent any number `z` with `|z| >= 2 ** 53` as float without
#: losing some digits, because floats have only 52 bits.
#: `float(9007199254740992) == 9007199254740992.0`
#: `float(9007199254740991) == 9007199254740991.0`
#: But:
#: #: `float(9007199254740993) == 9007199254740992.0`.
__DBL_INT_LIMIT_P_I: Final[int] = 9007199254740992
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
    :raises TypeError: if either one of `a` or `b` is neither an integer nor
        a float

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

    >>> try:
    ...     try_float_div("y", 1)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is str, namely 'y'.

    >>> try:
    ...     try_float_div(1, "x")
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is str, namely 'x'.
    """
    ia: Final[int | float] = try_int(a)
    ib: Final[int | float] = try_int(b)
    if isinstance(ia, int) and isinstance(ib, int):
        return try_int_div(ia, ib)
    if not isinstance(a, float | int):
        raise type_error(a, "a", (int, float))
    if not isinstance(b, float | int):
        raise type_error(b, "b", (int, float))
    val: Final[float] = ia / ib
    if not isfinite(val):
        raise ValueError(f"Result must be finite, but is {a}/{b}={val}.")
    return __try_int(val)


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

    >>> try_int_sqrt(4503599627370497)
    67108864
    >>> 67108864 * 67108864
    4503599627370496
    >>> sqrt(4503599627370497)
    67108864.0
    >>> sqrt(4503599627370497) * sqrt(4503599627370497)
    4503599627370496.0

    >>> try_int_sqrt(2535301200456458802993406410753)
    1592262918131443.2
    >>> sqrt(2535301200456458802993406410753)
    1592262918131443.2

    >>> try_int_sqrt(40564819207303340847894502572033)
    6369051672525773
    >>> sqrt(40564819207303340847894502572033)
    6369051672525773.0

    >>> try_int_sqrt(2596148429267413814265248164610049)
    50952413380206181
    >>> sqrt(2596148429267413814265248164610049)
    5.0952413380206184e+16

    >>> try_int_sqrt(2274861614661668407597778085)
    47695509376267.99
    >>> sqrt(2274861614661668407597778085)
    47695509376267.99

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

    >>> try_int_sqrt(int("1206411441012088169768424908631547135410050\
450349701156359323012992324468898745458674194715627653148741645085002\
880167432962708099995812635821183919553390204438671018341579206970136\
807811815836079357669821219116858017489215282754293788095448310134150\
6291035205862448784848059094859987648259778470316291228729945882624"))
    10983676256208975543971041278530229147631096480229288655031141534\
696869093436249683396095425058327287963674098226369372859395180799546\
6301001184452657840914432

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

    >>> try_int_sqrt(9007199254740993)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0
    >>> sqrt(9007199254740993)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0

    >>> try_int_sqrt(16121301469375805)
    126969687.20673373
    >>> 126969687.20673373 * 126969687.20673373
    1.6121301469375804e+16
    >>> sqrt(16121301469375805)
    126969687.20673373
    >>> 126969687.20673373 * 126969687.20673373
    1.6121301469375804e+16

    >>> try_int_sqrt(9007199254740995)
    94906265.62425156
    >>> 94906265.62425156 * 94906265.62425156
    9007199254740994.0
    >>> sqrt(9007199254740995)
    94906265.62425157
    >>> 94906265.62425157 * 94906265.62425157
    9007199254740996.0

    >>> try_int_sqrt(10487144142025273)
    102406758.2829633
    >>> 102406758.2829633 * 102406758.2829633
    1.0487144142025274e+16
    >>> sqrt(10487144142025273)
    102406758.28296329
    >>> 102406758.28296329 * 102406758.28296329
    1.048714414202527e+16

    >>> try_int_sqrt(10235141177565705)
    101168874.54926889
    >>> 101168874.54926889 * 101168874.54926889
    1.0235141177565706e+16
    >>> sqrt(10235141177565705)
    101168874.54926887
    >>> 101168874.54926887 * 101168874.54926887
    1.0235141177565702e+16

    >>> try_int_sqrt(15366441080170523)
    123961449.9760733
    >>> 123961449.9760733 * 123961449.9760733
    1.5366441080170522e+16
    >>> sqrt(15366441080170523)
    123961449.97607331
    >>> 123961449.97607331 * 123961449.97607331
    1.5366441080170526e+16

    >>> try_int_sqrt(22661588475548439582669426672241)
    4760418939079673
    >>> 4760418939079673 * 4760418939079673
    22661588475548439437260241786929
    >>> sqrt(22661588475548439582669426672241)
    4760418939079673.0
    >>> 4760418939079673.0 * 4760418939079673.0
    2.266158847554844e+31

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

    >>> try_int_add(10796862236149287, 146056785.70684135)
    10796862382206073
    >>> 10796862236149287 + 146056785.70684135
    1.0796862382206074e+16

    >>> try_int_add(-11909677351933537, -1392628259.5206623)
    -11909678744561797
    >>> -11909677351933537 + -1392628259.5206623
    -1.1909678744561796e+16

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

    b_int: Final[int] = int(b)
    int_res: Final[int] = a + b_int

    a_exact: Final[bool] = __DBL_INT_LIMIT_N_I < a < __DBL_INT_LIMIT_P_I
    b_exact: Final[bool] = __DBL_INT_LIMIT_N_I < b < __DBL_INT_LIMIT_P_I
    res_exact: Final[bool] = \
        __DBL_INT_LIMIT_N_I < int_res < __DBL_INT_LIMIT_P_I
    if a_exact and b_exact and res_exact:
        # We know that the result should fit well into the float range.
        # So we can just compute it normally
        return __try_int(a + b)

    # OK, so at least one parameter will step out of our comfort zone.
    b_frac: Final[float] = b - b_int
    if b_exact and res_exact:
        # `b` is a float whose integer part is exactly represented.
        # `a` is not.
        # So if we convert `a` to a float by doing `a + b`, we lose precision.
        # So the right thing to do would be to first compute the integer
        # result by adding `a + int(b)`. This result will be exact, because we
        # already know that it fits into the exactly representable range.
        # So we compute it without transforming it to a float.
        # Now we can add the floating point fraction of `b` to it.
        # This will turn the result into a float that is represented as
        # exactly as possible.
        return __try_int(int_res + b_frac)

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
    return (int_res + 1) if (b_frac >= 0.5) else (
        (int_res - 1) if (b_frac <= -0.5) else int_res)
