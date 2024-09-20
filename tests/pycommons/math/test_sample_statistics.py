"""Test the integer mathmatics."""

from contextlib import suppress
from itertools import product
from math import inf, log2, nextafter, sqrt
from random import expovariate, randint, shuffle, uniform
from statistics import geometric_mean as statgeomean
from statistics import mean as statmean
from statistics import median as statmedian
from statistics import stdev as statstddev
from sys import float_info
from typing import Callable, Final, Iterable

import pytest

from pycommons.io.csv import csv_read, csv_write
from pycommons.math.sample_statistics import (
    KEY_N,
    CsvReader,
    CsvWriter,
    SampleStatistics,
    from_samples,
)

#: the maximum n
MAX_N: Final[int] = 1000
#: the maximum 2 power
MAX_2_POWER: Final[int] = int(log2(sqrt(float_info.max) / (MAX_N + 1)))


def __check(data: SampleStatistics) -> SampleStatistics:
    """
    Check a sample statistics.

    :param data: the data
    :return: the data
    """
    if not isinstance(data, SampleStatistics):
        raise TypeError(f"{type(data)}")
    if data.n < 1:
        raise ValueError(f"n={data.n}")
    if data.minimum > data.maximum:
        raise ValueError(f"{data.minimum} > {data.maximum}")
    if not (data.minimum <= data.mean_arith <= data.maximum):
        raise ValueError(
            f"not {data.minimum} <= {data.mean_arith} <= {data.maximum}")

    if not (data.minimum <= data.median <= data.maximum):
        raise ValueError(
            f"not {data.minimum} <= {data.median} <= {data.maximum}")

    if not ((data.mean_geom is None) or (
            data.minimum <= data.mean_geom <= data.mean_arith)):
        raise ValueError(
            f"not {data.minimum} <= {data.mean_geom} <= {data.mean_arith}")

    if not ((data.n == 1) == (data.stddev is None)):
        raise ValueError(f"{data.n} <-> {data.stddev}")

    if not ((data.stddev is None) or ((data.stddev == 0) == (
            data.minimum >= data.maximum))):
        raise ValueError(
            f"{data.stddev} <-> [{data.minimum}, {data.maximum}]")
    return data


def __enforce_same(a: int | float, b: int | float,
                   data: tuple[int | float, ...]) -> None:
    """
    Enforce that two values are about the same.

    :param a: the first value
    :param b: the second value
    :param data: the source data
    """
    if a == b:
        return
    if a == 0:
        raise ValueError(f"a={a}=0, b={b}, data={data!r}")
    if b == 0:
        raise ValueError(f"a={a}, b={b}=0, data={data!r}")
    if (a < 0) != (b < 0):
        raise ValueError(f"a={a}<0 != b={b}<0, data={data!r}")
    orig_a: Final[int | float] = a
    orig_b: Final[int | float] = b
    if a < 0:
        a = -a
        b = -b
    if a > b:
        a, b = b, a
    with suppress(OverflowError):
        if (a / b) > 0.999:
            return
    with suppress(OverflowError):
        if ((int(b) - int(a)) * 100000) < int(a):
            return
    raise ValueError(f"!(a={orig_a} == b={orig_b}, data={data!r}")


def __check_with_data(stat: SampleStatistics,
                      data: tuple[int | float, ...]) -> SampleStatistics:
    """
    Check the sample statistics with respect to the data.

    :param stat: the statistics
    :param data: the data
    :return: the statistics
    """
    if not isinstance(stat, SampleStatistics):
        raise TypeError(f"{type(stat)}")
    if not isinstance(data, tuple):
        raise TypeError(f"{type(data)}")

    stat = __check(stat)

    mi = min(data)
    if mi != stat.minimum:
        raise ValueError(f"min: {mi} != {stat.minimum}, data={data!r}")

    ma = max(data)
    if ma != stat.maximum:
        raise ValueError(f"max: {ma} != {stat.maximum}, data={data!r}")

    mm: int | float | None = None
    with suppress(BaseException):
        mm = statmean(data)
    if mm is not None:
        __enforce_same(stat.mean_arith, mm, data)

    mm = None
    with suppress(BaseException):
        mm = statmedian(data)
    if mm is not None:
        __enforce_same(stat.median, mm, data)

    if stat.mean_geom is not None:
        mm = None
        with suppress(BaseException):
            mm = statgeomean(data)
        if mm is not None:
            __enforce_same(stat.mean_geom, mm, data)

    if stat.stddev is not None:
        mm = None
        with suppress(BaseException):
            mm = statstddev(data)
        if mm is not None:
            __enforce_same(stat.stddev, mm, data)

    return stat


def __make_sample_statistics(
        multiple_samples: bool = True,
        all_samples_same: bool = False,
        has_geometric_mean: bool = True,
        all_samples_int: bool = False,
        all_samples_float: bool = False) -> SampleStatistics:
    """
    Create random sample statistics.

    :param multiple_samples: are there multiple samples?
    :param all_samples_same: are all the sampled values the same?
    :param has_geometric_mean: do we have a geometric mean?
    :param all_samples_int: should we use only integer numbers?
    :param all_samples_float: should we use only floating point numbers?
    :returns: the sample statistics and the data it was created from
    """
    if not isinstance(multiple_samples, bool):
        raise TypeError(f"{type(multiple_samples)}")
    if not isinstance(all_samples_same, bool):
        raise TypeError(f"{type(all_samples_same)}")
    if not isinstance(has_geometric_mean, bool):
        raise TypeError(f"{type(has_geometric_mean)}")
    if not isinstance(all_samples_int, bool):
        raise TypeError(f"{type(all_samples_int)}")
    if not isinstance(all_samples_float, bool):
        raise TypeError(f"{type(all_samples_float)}")
    if not ((not all_samples_int) or (not all_samples_float)):
        raise ValueError(f"{all_samples_int} <-> {all_samples_float}")

    n_samples: Final[int] = max(2, min(MAX_N, int(expovariate(0.01)))) \
        if multiple_samples else 1
    if multiple_samples != (n_samples > 1):
        raise ValueError(f"{multiple_samples} vs. {n_samples}")
    if (not multiple_samples) and (not all_samples_same):
        raise ValueError(f"{multiple_samples} <-> {all_samples_same}")

    range_min: int = max(1, int(2 ** randint(0, MAX_2_POWER)))
    range_max: int = max(1, int(2 ** randint(0, MAX_2_POWER)))
    if range_min > range_max:
        range_min, range_max = range_max, range_min

    if not has_geometric_mean:
        if randint(0, MAX_2_POWER) <= 0:
            range_min = 0
        if randint(0, MAX_2_POWER) <= 0:
            range_max = 0
        if randint(0, 1) <= 0:
            range_min = -range_min
        if randint(0, 1) <= 0:
            range_max = -range_max

    if range_min > range_max:
        range_min, range_max = range_max, range_min
    if range_min >= range_max:
        range_max += 1

    data: Final[list[int | float]] = []
    while list.__len__(data) != n_samples:
        if all_samples_same and (list.__len__(data) > 0):
            data.append(data[0])
            continue
        sample_func = uniform if all_samples_float else (
            randint if all_samples_int else (
                uniform if randint(0, 1) <= 0 else randint))
        data.append(sample_func(range_min, range_max))

    changed: bool = True
    while changed:
        changed = False
        all_pos: bool = all(x > 0 for x in data)
        if has_geometric_mean:
            if not all_pos:
                raise ValueError(f"{has_geometric_mean} vs. {all_pos}")
        elif all_pos:
            if all_samples_same:
                for i in range(n_samples):
                    data[i] = -data[i]
                    changed = True
            else:
                data[-1] = -randint(0, 5)
                changed = True
        if (not all_samples_same) and all(x == data[0] for x in data):
            dv = data[-1]
            data[-1] = dv + 1 if isinstance(dv, int) \
                else nextafter(dv, inf)
            changed = True

    shuffle(data)
    use_data: Final[tuple[int | float, ...]] = tuple(data)
    if tuple.__len__(use_data) != n_samples:
        raise ValueError(f"{tuple.__len__(use_data)} != {n_samples}")
    result: Final[SampleStatistics] = __check(from_samples(use_data))

    if has_geometric_mean != (result.mean_geom is not None):
        raise ValueError(f"{has_geometric_mean} -> {result.mean_geom}")
    if tuple.__len__(use_data) != result.n:
        raise ValueError(f"{tuple.__len__(use_data)} != {result.n}")
    if result.n <= 0:
        raise ValueError(f"{result.n}")
    if result.n != n_samples:
        raise ValueError(f"{result.n} != {n_samples}")
    if (tuple.__len__(use_data) > 1) != multiple_samples:
        raise ValueError(
            f"{tuple.__len__(use_data) > 1} != {multiple_samples}")
    if ((all_samples_same or (not multiple_samples))
            != (result.minimum == result.maximum == data[0])):
        raise ValueError(f"{all_samples_same}, {multiple_samples}, "
                         f"{result.minimum}, {result.maximum}, {data[0]}")
    if not (multiple_samples == (result.n > 1) == (
            result.stddev is not None)):
        raise ValueError(f"{multiple_samples}, {result.n}, {result.stddev}")

    if all_samples_int:
        if not isinstance(result.minimum, int):
            raise TypeError(f"{type(result.minimum)}")
        if not isinstance(result.maximum, int):
            raise TypeError(f"{type(result.maximum)}")
    return __check_with_data(result, use_data)


def test_sample_stats() -> None:
    """Test the sample statistics."""
    for _ in range(1000):
        all_int: bool = True
        all_float: bool = True
        while all_int and all_float:
            all_int = randint(0, 1) <= 0
            all_float = randint(0, 1) <= 0

        multi: bool = False
        all_same: bool = False
        while (not multi) and (not all_same):
            multi = randint(0, 1) <= 0
            all_same = randint(0, 1) <= 0

        result = __make_sample_statistics(
            multi, all_same, randint(0, 1) <= 0, all_int, all_float)
        if result is None:
            raise TypeError(f"{result}??")


def __make_sample_statistics_list(
        more_than_one_statistics: bool = True,
        all_settings_different: bool = False,
        multiple_samples_per_stat: bool = True,
        all_samples_same_per_stat: bool = False,
        has_geometric_mean_per_stat: bool = True,
        all_int_per_stat: bool = False,
        all_float_per_stat: bool = False) -> list[SampleStatistics]:
    """
    Make a list of random sample statistics.

    :param more_than_one_statistics: is there more than one statistics
        instance in the list?
    :param all_settings_different: if `True`, then the other parameters except
        `multiple_samples` are ignored and random values are used
    :param multiple_samples_per_stat: are there multiple samples?
    :param all_samples_same_per_stat: are all the sampled values the same?
    :param has_geometric_mean_per_stat: do we have a geometric mean?
    :param all_int_per_stat: do we only have integers?
    :param all_float_per_stat: do we only have floats?
    :returns: the sample statistics list
    """
    result: Final[list[SampleStatistics]] = []
    n_stats: Final[int] = randint(2, 100) if more_than_one_statistics else 1
    if n_stats < 1:
        raise ValueError(f"n_stats={n_stats}")
    if (n_stats > 1) != more_than_one_statistics:
        raise ValueError(f"{n_stats} <-> {multiple_samples_per_stat}")
    if (all_int_per_stat and all_float_per_stat) and (
            not all_settings_different):
        raise ValueError(f"{all_int_per_stat} {all_float_per_stat} "
                         f"{all_settings_different}")
    if (not multiple_samples_per_stat) and (
            not all_samples_same_per_stat) and (
            not all_settings_different):
        raise ValueError(
            f"{multiple_samples_per_stat} "
            f"{all_samples_same_per_stat} {all_settings_different}")

    for _ in range(n_stats):
        while True:
            all_int: bool = (randint(0, 1) <= 0) \
                if all_settings_different else all_int_per_stat
            all_float: bool = (randint(0, 1) <= 0) \
                if all_settings_different else all_float_per_stat
            if not (all_int and all_float):
                break

        while True:
            multi: bool = (randint(0, 1) <= 0) \
                if all_settings_different else multiple_samples_per_stat
            all_same: bool = (randint(0, 1) <= 0) \
                if all_settings_different else all_samples_same_per_stat
            if not ((not multi) and (not all_same)):
                break

        result.append(__make_sample_statistics(multi, all_same, (
            randint(0, 1) <= 0) if all_settings_different
            else has_geometric_mean_per_stat, all_int, all_float))
    shuffle(result)
    assert list.__len__(result) == n_stats
    return result


def test_csv_1() -> None:
    """Test the CSV abilities from actual random data."""
    s: Final[list[bool]] = [True, False]
    for (more_than_one_statistics, all_settings_different,
         multiple_samples_per_stat, all_samples_same_per_stat,
         has_geometric_mean_per_stat, all_int_per_stat,
         all_float_per_stat) in product(s, s, s, s, s, s, s):
        if all_settings_different and (
                multiple_samples_per_stat or all_samples_same_per_stat
                or has_geometric_mean_per_stat or all_int_per_stat
                or all_float_per_stat):
            continue
        if (not all_settings_different) and (
                not multiple_samples_per_stat) and (
                not all_samples_same_per_stat):
            continue
        if ((not all_settings_different) and all_int_per_stat
                and all_float_per_stat):
            continue
        for _ in range(10):
            data: list[SampleStatistics] = (
                __make_sample_statistics_list(
                    more_than_one_statistics, all_settings_different,
                    multiple_samples_per_stat, all_samples_same_per_stat,
                    has_geometric_mean_per_stat, all_int_per_stat,
                    all_float_per_stat))
            text: list[str] = []
            csv_write(
                data=data, consumer=text.append,
                setup=CsvWriter().setup,
                get_column_titles=CsvWriter.get_column_titles,
                get_row=CsvWriter.get_row,
                get_footer_comments=CsvWriter.get_footer_comments,
                get_header_comments=CsvWriter.get_header_comments)
            output: list[SampleStatistics] = []
            csv_read(rows=text,
                     setup=CsvReader,
                     parse_row=CsvReader.parse_row,
                     consumer=output.append)
            assert len(output) == len(data)
            assert output == data


def test_csv_2() -> None:
    """Test the CSV abilities from hand-made data."""
    text: list[str] = [
        "n;min;max;mean;med;geom;sd",
        "5;1;;;;;",
        "4;;2;;;;",
        "2;;;3;;;",
        "7;;;;4;;",
        "1;;;;;5;",
        "9;1;1;;;;0",
        "9;0;0;;;;0",
    ]
    parsed: list[SampleStatistics] = []
    csv_read(rows=text,
             setup=CsvReader,
             parse_row=CsvReader.parse_row,
             consumer=parsed.append)
    assert len(parsed) == 7
    assert parsed[0].minimum == parsed[0].maximum == parsed[0].mean_geom == 1
    assert parsed[0].stddev == 0
    assert parsed[1].minimum == parsed[1].maximum == parsed[1].mean_geom == 2
    assert parsed[1].stddev == 0
    assert parsed[2].minimum == parsed[2].maximum == parsed[2].mean_geom == 3
    assert parsed[2].stddev == 0
    assert parsed[3].minimum == parsed[3].maximum == parsed[3].mean_geom == 4
    assert parsed[3].stddev == 0
    assert parsed[4].minimum == parsed[4].maximum == parsed[4].mean_geom == 5
    assert parsed[4].stddev is None
    assert parsed[5].minimum == parsed[5].maximum == parsed[5].mean_geom == 1
    assert parsed[5].stddev == 0
    assert parsed[6].minimum == parsed[6].maximum == 0
    assert parsed[6].mean_geom is None
    assert parsed[6].stddev == 0


def test_csv_3() -> None:
    """Test cover some features of the CSV Writer."""
    CsvWriter(what_short="a")
    CsvWriter(what_long="b")
    CsvWriter(what_short="a", what_long="b")

    data: list[SampleStatistics] = [
        __make_sample_statistics(all_samples_same=False),
        __make_sample_statistics(all_samples_same=False),
        __make_sample_statistics(all_samples_same=False),
        __make_sample_statistics(all_samples_same=False)]
    w: CsvWriter = CsvWriter()
    w.setup(data)
    error: bool = False
    try:
        w.setup(data)
        error = True
    except ValueError:
        pass
    if error:
        raise ValueError("Unexpected!")

    data_2 = [__make_sample_statistics(all_samples_same=True),
              __make_sample_statistics(all_samples_same=True),
              __make_sample_statistics(all_samples_same=True),
              __make_sample_statistics(all_samples_same=True)]
    w = CsvWriter()
    w.setup(data_2)
    try:
        w.get_row(data[0], [].append)  # type: ignore
        error = True
    except ValueError:
        pass
    if error:
        raise ValueError("Unexpected!")


def test_special_cases() -> None:
    """
    Test some pre-defined cases.

    The goal of these tests is to cover as many of the branches of the
    :func:`from_sample` code as possible.
    """
    for case in [
            (4503599627370498.0, 4503599627370497),
            (32940767.586947955, 57729835, 32490888.319228098, 1907042,
             4182374, 26708100, 1447085, 63934420, 45696552,
             17522830.98384079),
            (-61150665536,),
            (-6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826),
            (874080429.9288498, 365383979.85986924, -3, 1045541493.9970537,
             382003401.57206744, 135877768.18182534, 665227480.7501322,
             309296826.70937634, 1486000852.9067705, 858454523.0467283),
            (4839.743333210951, 7495, 1714.2649640346826, 3939.7817751474545,
             2696, 7216.514988731088, 1954, 6483, 622, 401),
            (860378799, 565728184, 148137872, 224630554, 361914966, 0,
             739501304, 267746120),
            (945099740753.1964, 306542914888.53, 603373921895.0829,
             982206472858.9705, 831271149518.0499, 485220506259.3286,
             390200614359.8139, 205913110645.98294, 567290126883.982,
             982688940757.7454),
            (49126398.09083965, 23540194.82371754, -5, 113211339,
             23508868.850696992, 102779713.51407853, 28919217,
             16699249.840516366, 98040260.58801918, 126651727.5572017),
            (-5, 39254, 80491),
            (260107304, 523341884, 462126862, 343846945, 253417406, 62786515,
             318617332, 417633770, 56143427, 94294894),
            (-5, 32803893385),
            (-1, 4519532),
            (59376625.16287131, 114141741.58784416, 124596023.84470825,
             127184357.98965803, 11347945.007376743, 127817299.04781677,
             53280315.21295824),
            (1220291472, 1110858232),
            (1237432, 117038878, 171070285, 302342217, 258458007, 296608812,
             449581621, 67676155, 47177674, 203464900),
            (212223218, 84785539, 71120916, 200062755, 220799567, 123649341,
             223311268, 99772494, 191529405, 205781921),
            (1888196555, 14559900624.045185, 4681315483, 4449133754.519277,
             2036238994.648712, 14964121047, 14699723231.872793,
             6862744653.891714, 1206963824, 17142060078),
            (3336944686, 21179575814.125153, 3523184494, 7770969621,
             16458546368.156565, 30875517343, 21707644314, 33306287953,
             14779807051.803564, 16371559418.83981),
            (-365832568744, -289754611490, -329685803735, -231879890022,
             -86860516032, -275272955151, -274952659633, -70518302279,
             -23951403573, -79063083381),
            (736499882, 1049442130, 394231934, 158796944, 128830073, -1,
             581647954, 951480311, 101557664, 957761395),
            (1365939, 968841, 1927036, 1261585, 80193, 296247, 1721213,
             1044964, 805879, 1386957),
            (-159894840556, -272803466841, -30411028328, -84632890995,
             -248379097709, -176529794288, -260423441183, -245470648970,
             -145605238940, -71780027152),
            (864250721740, 413267669742, 214800252249, 353605957716,
             643460311295, 939150468045, 300134514406, 414318666080,
             927799326369, 1042920621825),
            (-51374, -90642, -30417, -23602, -19096, -2411, -99150,
             -119074, -61377, 8540),
            (2977827131, 2959733758, 576881741, 6912821843, 5276602280,
             5076955971, 1559959161, 2116895865, 808408487, 1590590230),
            (2521106301, 3795030946),
            (48832266564, 66988391320, 25354605489, 46926370291,
             30031966734, 67804599390, 56779474526, 6255914617, 48379089944,
             20514446331),
            (28, 4, 2, 31, 21),
            (2795618007, 89333364, 740547717),
            (611759480, 1412201968, 184580928, 480365450, 1048628454,
             1964242982, 1060943318, 463605712, 543674512, 623073570),
            (22972433374, 26138961134),
            (100, 80, 60, 120, 300),
            (32273981501, 13082451168, 29800542898, 5970622806, 102061471553,
             25578428028, 20903804891, 13658864622, 115448358022,
             136972102994),
            (876068726, 1061141668, 30770255, 740182117, 162889910,
             801714661, 660278283, 510809503, 722368501, 733615327),
            (158456325028528675187087900672, 158456325028528675187087900672,
             158456325028528675187087900673, 158456325028528675187087900672,
             158456325028528675187087900672, 158456325028528675187087900673,
             158456325028528675187087900672, 158456325028528675187087900672,
             158456325028528675187087900672, 158456325028528675187087900673),
            (int("144366693639338206490211644774667871680162601262082"
                 "425826616303352993"),
             int("3110799314244257320510497898976744206047138354613981"
                 "5291547548992982997"),
             int("1055370232025031288139999337991702692524487215999269"
                 "3057997574289772612"),
             int("4765722724647027538078115443384705697658617645831907"
                 "2144832158298685591"),
             int("1910140978470887904284115216589858461903272618554626"
                 "8613186975674825575"),
             int("1897762347779501236068301408307838210157346940359738"
                 "034288013599386088"),
             int("2218145719343233147851852276200902943343734018933221"
                 "8738970992964216166"),
             int("7026522203668062913375476144798901624082118471012009"
                 "548545387476138550"),
             int("1640901136731838699387185047202793852336568601693480"
                 "5614658152115133932"),
             int("6026317109941477269683813493891802847643321683821732"
                 "580989763067379491")),
            (int("6732743542884147402888721701761213369270930481994554"
                 "1512597156338557366105166498941399317463070381434506"
                 "3392949229301931578296373046997631496680927265379"),
             int("3863403633599022711889287451491962320227717127457334"
                 "3166481920228269573858329548401162893504595886970370"
                 "5646016141014188916851860707533423367507315700104"),
             int("6442384846101544243594026546245453297655697394930995"
                 "8246622985598161291654429506670953239748194634582429"
                 "216371454798652772711415760195506233727141977839")),
            (int("460607494855769404728613104129888403413352010414302"
                 "865293332084931092968493505252227208569966897035600"
                 "92513652659781926707057443081689099319"),
             int("209142281047462574772785672855077129521043688363059"
                 "086459500649406935461516847489125287605341040930799"
                 "84978004342718190084758298204799448257"),
             int("103285361232561374394193195957666950587710700770579"
                 "177988462865503157552162213139382220542331982901021"
                 "184027588610410184439528438600545729007"),
             int("143037618359232425648020285778807132986823551616425"
                 "183090620111298253845223760303496855433581865691774"
                 "272041820719835159540799092932829130062"),
             int("265481097017388112874761444503134854758816458934035"
                 "573574538017657545140858833254329597910561942330555"
                 "07807064874516498591836123824363024378"),
             int("293276247686460281819335652471211617706110120820777"
                 "320903473165931788461618480872562135739785819878768"
                 "24206960940708806828753110416637111355"),
             int("699972643794510368451388912513316477129351331971160"
                 "996696936846501670544202984896988932781258307563284"
                 "31803590638010342386505120523086332795"),
             int("164886352545254679555011504050666822959111546423802"
                 "496545300425976697349506106971597372993174457894804"
                 "003039916293954919694508880302315542549"),
             int("164927391479140477445062463451235693232562778922741"
                 "770085591841647654378775364313694602684021619655269"
                 "337290722805471915629299944785953634289"),
             int("79848819365027203784664797729432482197388919642714"
                 "63893777694250934976642487034302015487252014819551"
                 "1746797845611523655728556095967162398987")),
            (int("16096423879511760173769824677758412028932266011524"
                 "74053791695364030387063430568808506996222448803882"
                 "486553791997775942"),
             int("680279132061174437962144977573379198722171934671310"
                 "742627845247505520371510001218236831468830964451321"
                 "292563734123492")),
            (2854495385411919762116571938898990272765493250,
             2854495385411919762116571938898990272765493249),
            (int("667495948725284400748444283177985035813345163236453"
                 "99060845050244444366430645017188217565216768"),
             int("667495948725284400748444283177985035813345163236453"
                 "99060845050244444366430645017188217565216769")),
            (int("833800703226546805563376734402798533922684928289915"
                 "285793017784388794216571248947851262376668819847231"
                 "8274804333434910163647682240888486810"),
             int("115535918504711555111590330838934201550725155632805"
                 "480570704950387920130792204221115707920971398786507"
                 "7013558695228164440693279654946073691467")),
            (int("547707450050160846991176883912171989356088889011563"
                 "786410130501822545135291643448572514839247388908213"
                 "71238968176074742042123369235900194"),
             int("148379721747682465633787386767514075751003063702305"
                 "931152916637391734188927765076072577594244390200476"
                 "9431755241887927400973444177771010620")),
            (int("535655614507168342679759365301764264730828017006655"
                 "588958028821117855"),
             int("198474740589786478917477926977203532347878701558649"
                 "1470778609439813552"),
             int("183020370659374175403058105830372941332087807564727"
                 "146642355101965490"),
             int("625237617490266221629174725299202941143935630920185"
                 "183049309479921455")),
            (216749105217568743892, 143996067070746126595,
             125971435343296704645, 276394180278399736894,
             19064242554302545372, 195872137983104859808,
             190825820750865277144, 175829526452052065163,
             242593450523816785419, 199787562049073144935),
            (int("456614677985220321265696276303095564760845442685867"
                 "918289636137448177902520401740010576408615823994061"
                 "04198734165634141981046059816874599363906041"),
             int("14315612327073354027817376125723939477956548385366"
                 "58745320551189052835028187428625335626029811893374"
                 "69170653364640257051361813486218646003693084404")),
            (5459941607138759202919488201, 66043054905997702206440816652,
             66471212207210471408666720458, 55555441658051705719494479580,
             44948561138034415279462680429, 51012613762724213322106137149,
             51492446244752869835054093839, 75352744848094855097739023265,
             5065161803303133198921223416, 76591210210346839566343766107),
            (1187542283948417194789878844471, 793197295092626209357861452990,
             244880123707720043957183641621, 162070243265441030253555682108,
             1097335181089383708007334661888, 969357223517946552442032165791,
             773769509087754013545891741728, 932877171146860074450166975145,
             941110849830107581077269912557, 623157861381808875353436309390),
            (398162741930250399796, 398482006457058451152,
             43758697342773891678, 543686385531729593571,
             497388725853686778387, 560703955913232843433,
             169862741805260893051, 10254565269163865621,
             129787284828827655483, 389482213965982551003),
            (int("405819325250517415120025501553364279811984656884080"
                 "59447043807463971155969361330816808805816663999030"),
             int("180854421882927592684947567916602152672576432476175"
                 "27128679623970206095633441088059919776544624635155")),
            (14062025551327277816344085, 15946978958239995206962414,
             27529891282989876870263973, 10912311805988320139682849,
             27597899416515682109090765, 29232836805159553936793968,
             31617897795474474331434182, 1503830608465632372953659,
             26993665263798301479436097, 3266293247135959228159919),
            (58955972002072730052, 75056163489846014019, 42650155939738402484,
             2.7639065267460093e+20, 8.450776565724905e+18,
             2.2559661235044142e+20, -2, 1.2873350363107931e+20,
             1.817169192843514e+20, 12258899618206622449),
            (2.1556493633548668e+20, 2.628039385769499e+20,
             2.1618204259705743e+20, 2.021945142831666e+20,
             1.753853284790433e+20, 1.1628670280808453e+20,
             1.2661328289694908e+20, 1.291088636919534e+20,
             1.509249602159816e+20, 2.062858126542266e+20),
            (666518202373.9465, 896632431712.2753, 58104356020.070274,
             2042794715201.452, 793253508273.445, 955828028024.6907,
             1938766266062.6912, 1849112313836.5364, 1617865758425.2454,
             1450551267474.1255),
            (6.637400379703297e+21, 12753243587706397063183,
             1.1833620721701635e+22, 1.098811721842031e+22,
             12031152201174412045430, 1.6833366370693623e+22,
             9830734035163762084133, 2.0698505839961938e+21,
             10423246773224340156083, 4304260568800788966185),
            (1.8014398509481984e+16, 18014398509481985,
             1.8014398509481984e+16, 1.8014398509481984e+16,
             1.8014398509481984e+16, 18014398509481985,
             1.8014398509481984e+16, 18014398509481985,
             1.8014398509481984e+16, 18014398509481984),
            (1.4757395258967641e+20, 1.4757395258967641e+20,
             1.4757395258967641e+20, 1.4757395258967641e+20,
             1.4757395258967645e+20, 1.4757395258967641e+20,
             1.4757395258967641e+20, 1.4757395258967641e+20,
             1.4757395258967641e+20, 1.4757395258967641e+20),
            (26115187644764, 277460813035491, 254145722972353.2,
             170025505817946.4, 194883577410730, 201173831400917.56),
            (1252771639194294, 1923990418039027, 2245647559372604),
            (int("3541978931453128001379636385009848896741365284355939696"
                 "6809084378209249572230769978722506086004789822138169219"
                 "481357139860480913107427690432"), 2.1683152289785633e+139,
             int("15155915963500415755419191147488517385365055455542318001"
                 "67377175516855687191232676126200514708921315297352206296"
                 "5202338363653235536526768881"),
             int("10476477853298930577940811438746451249460181657328747871"
                 "13248102074337796672339049028524146083002309827704994588"
                 "023732199930901254263661958"), 1.1864377071785887e+139,
             int("14429044897564822303725493281210985416871719131212842936"
                 "82335284481908758116358008763969549189458333431214111149"
                 "2922359238144498482809682322"),
             int("30315286377289339875296186211307486516329286012898555602"
                 "24886754697153967103074871532304093297530145581621193977"
                 "6076585955856344118471459158"), 6.83542300139941e+138,
             2.1187988881151288e+138,
             int("42421606886778331932517079502608159269202903366511824162"
                 "76820382721998941517232688319163122237041668093480293560"
                 "70428215945013095136016693"),
             int("39224766458141841787946124159177389871238514892347330638"
                 "80540246546312081830371500232664280898605773127153773181"
                 "7730371364115356392814472396"), 3.7227989608878533e+139,
             3.1055576953924045e+139, 2.0376105972700568e+139,
             int("47466566332727028410891218526762681525610673785206271511"
                 "59647189222045365843482520140533037249967839409486297896"
                 "7843868044921440113326227148"), 3.1538597664759873e+139),
            (int("36511138528313120809709892286344350473107557231246301434"
                 "03794249412872912109926319301232961433081913268215648178"
                 "855738891"),
             int("14311968773332761996304240772619563942345897345603068507"
                 "01750445438349624254090563584079523909461429566355994895"
                 "931897398")),
            (1298841476138, 7213815809697, 6075068525162, 6669625077844,
             5286621664947, 3243997190699, 2013442249736, 56365976584,
             7106904355357, 903874499716.297, 2882633755308.439,
             3063650885336, 7100853378486.1875, 8026584060331,
             3103424425875.636, 3215380460002.9077, 8677907218539.107,
             2594745292515.1274, 285004314307.50977, 5222182766078.417,
             6510206089672.385, 7667084569650.394, 8746054171246,
             1941205486419, 1992951803717, 8410174931539.193,
             6768207326519.599, 6548571577071.875, 1043659490357.6865,
             38422714423, 3045267203541, 949804929510, 2723899572413.0483,
             4569691243205, 1413825402359.4055, 6242994217277.75,
             6729654152895.759, 2699005918526, 1753722496650.234,
             7146809116399.066, 1280249400440, 4664420329416.117,
             4434795041934, 161641410469.02893, 5192259358776.308,
             7656326325082.481, 2246039413216, 6114047951577,
             4457320581517.935, 7991236849154.0205, 6909373535914.735,
             7368694523069.411, 2028148992405.9905, 5748925317492,
             7333500468940.78, 644088333919.0411, 2115743490936,
             3679978601926.591, 5538932040573, 7374035738849, 2262931633632,
             4395616671918),
            (14555, 5082.301583235545, 4560.46258294141, 11689,
             8069.38212682205, 6174.885498875937, 14635, 1908, 12046, 5574,
             669.9965056625248, 14257.2768392485, 11726.170626408955,
             13576.537109023384, 2888.24448327073, 837, 12046,
             12658.866057175503, 2816, 3254.7803484814463,
             2525.06046012716, 2773, 2697.3876911224093, 11958.138540123899,
             12996, 14757, 1624.1286680918754, 10295.681534667301,
             9275.597453105634, 15877, 6077.837063881088, 6657, 1070, 5137,
             11171, 12748.132564335652, 1676, 10765, 6210, 15493,
             7619.960095875653, 11766, 15938.632199241114, 1928,
             13080.139267020706, 15076, 569, 13943, 9024, 8542, 15689,
             14596, 10071.526389926117, 9941.816911747475, 5676, 1742,
             14176, 15011, 755.9434999220407, 5233, 1620.68028624615,
             1304.9746213624246, 3119, 533.0385199134098, 4311, 11662,
             16152, 8391.207189716897, 7110, 2774, 7255, 5876, 14491,
             4519, 932.5276242215975, 5360, 14009, 370, 4577, 4498,
             8168.960297947485, 4650, 15940, 9732.287876881883, 14321,
             5573, 13699.478298586093, 8577.303289477892, 4082,
             2074.0910878843642, 14405, 7957, 1652.8001603406874, 10437,
             5716.767008582477, 3240.7328377038343, 11943.80134484178,
             11042, 3526, 6046, 1590, 8000, 9436.864600490873, 5325,
             7230.305381358316, 14234, 10023.299013503458, 16037,
             1446.552294335285, 4476, 7108, 12968, 12388,
             8928.03130846948, 10608, 15856, 593.075359958616,
             15414.297032364288, 10217.80462868231, 6386.687416783583,
             2500.1846636201894, 10195, 4811, 16243.649198087589, 6826,
             6599.457547756643, 7519, 2635.366203858418, 8520, 14025, 5228,
             16248, 2269.017526359597, 15366.269283299795, 11371,
             14555.972556933793, 3817, 11543, 5992, 5695.810078344193,
             14191.645666369353, 13893, 10551.95488881721,
             10790.162250416448, 8343, 6849, 2445, 8836, 8816.186148641807,
             15376, 4085.659994339038, 11311, 12124, 7460, 468,
             15177.198105902742, 9358, 10223.00341710908),
            (5491435030, 8270637675),
            (372959117635314.75, 545124525499863, 348159189743951.6,
             213369499545314.25, 374432214908800.2, 352621723076185.5,
             218998953244576, 194481415451700.03, 317645979974098.4,
             336650575265195.6, 368707353267764, 488213978525332.44,
             535396328280602, 395290323644334.7, 376937964085533.94,
             559367644121964, 261687130384297, 502359394462472,
             303351973127100, 322598897457325.4, 539832486305088.06,
             313720097774693, 498110810415402.5, 184048430652361.34,
             197643654753928, 232874331468930, 265986503854776.6,
             185195573869733.7, 477316973785238, 187449741800851,
             402083937270616, 438935702992980, 463084833957122,
             437050438417971.4, 233952237756310, 175095022452415.5,
             391144659041513.0, 336337133754794, 237934212899204,
             473845383344645.6, 260219694223583.0, 430292500723940,
             313086260105688, 248142333590485.62, 528108796760748,
             387276428514951, 496604071495173.9, 430802697586559.4,
             440982173222185.1, 185777015325848, 325382384169495.1,
             286606839887958.4, 247366423761753, 421285564691008,
             180687978065171, 473635180276243.0, 425775386044285.94,
             213654544973212, 284323388759269, 151913045381716,
             268116122293135, 290243597597741.6, 311690244817001.4,
             509456967283537.5, 287037736700731, 152812887978832,
             480431223278858.25, 145678239213498.25, 373446461259419,
             307492666635032.94, 216324799234053, 370665384460430,
             237906996803154.03, 249208884937095, 214540195050746,
             258146702017660, 276586700620008, 546538656734164,
             374420288166061, 540816838229597, 174248743951515,
             272723770125586.2, 274353225553379.12, 347425983156838,
             266539333017927, 497564310715885, 520842515142004,
             521090629600796.9, 301846630533113.2, 453347663037211.4,
             555378464033477.94, 201467807573173, 354539097197214.6,
             210249187573140, 405600995320858, 455315523051476,
             553275958891823, 200079622728822, 491502052189483.56,
             540153874942477.5, 235860937127224, 149772690752460,
             272841433005004.0, 206158511481847.5, 340533911272941.75,
             496356345324301, 340397428633315.1, 333689388475943,
             539462284961874.2, 332636033721961, 437384313369295.06,
             233041669260230, 354005777664762, 466766492217542.75,
             412229512614406, 253466862188470.2, 428445844637292.4,
             446265073766123.1, 548013021177072.5, 382141841747677.5,
             194727586983080.56, 541604886893828.0, 186628418470179,
             199165433324131, 217439885424259, 406937078973018.4,
             470928645320534, 142088960539390, 254341714500818.84,
             528459095744517.2, 507102315399732, 275045772706101,
             321991485191890.1, 470508113364219, 364249138830272,
             249313516244513.84, 427429211385350.44, 186193376832245.12,
             313260567242068, 195840785981546, 467251979565577,
             227339997220809, 436470534450872, 415588286006740.3,
             293929818569068.8, 339013121531215, 407673839086037,
             325815171773115.9, 278925006292222.9, 345217382247993,
             375972038874260, 333624165572875, 220540593680772.8,
             510338715133877, 390696014616443.6, 425262306526678,
             292850437534508, 362102917015164, 534979584553716.2,
             373265583815016, 278210674243330, 346108414908882,
             325535565605825.4, 226647977172526.94, 377757453750890,
             513997506942737.25, 372393798153088.6, 379986952445396,
             207867854516161, 485050215867244, 199605656838141.06,
             141087212105448, 389621502866985.9, 238937478563772.06,
             524112305478316, 387331629971638, 336348263741445,
             261598349937875.7, 506739021563748, 322206673776868,
             278657719604865, 147470249414142.3),
            (17025714763, 4484451977),
            (380845064196368, 307065081586578, 756949304669076.0,
             398778493474850, 468727541312951, 825946131914051,
             1113265861630887, 896280316587998, 934019029152857,
             630633092139215, 925243499505580, 951412851557978),
            (330449774993, 701451318661, 958073689675, 1057826950054,
             455298521451),
            (4217856987517, 2251105086857, 308613917851, 123751995107),
            (137338165187367, 286837332911880.3, 381786958150017.25,
             395562947634279.75, 280773899973624, 500492000826038.44,
             125046677136150, 554663595888699, 391103213471835,
             101817902192637, 332964353713848.56, 21236425438832,
             309230941691181.7, 23390968685967, 73088898899705.98,
             237336068506657.2),
            (int("319667051552357604493475556330820229708656449808893"
                 "045847977672665638066055143999500319344953701577846"
                 "7662777468320381844938727095591204153641140226"),
             int("319667051552357604493475556330820229708656449808893"
                 "045847977672665638066055143999500319344953701577846"
                 "7662777468320381844938727095591204153641140225"),
             int("319667051552357604493475556330820229708656449808893"
                 "045847977672665638066055143999500319344953701577846"
                 "7662777468320381844938727095591204153641140225"))]:
        __check_with_data(from_samples(case), case)


class _TCR:
    """A three-CSV-reader."""

    def __init__(self, columns: dict[str, int]) -> None:
        """
        Initialize.

        :param columns: the columns
        """
        super().__init__()

        a_keys: dict[str, str] = {
            k[2:]: k for k in columns if k.startswith("a")}
        b_keys: dict[str, str] = {
            k[2:]: k for k in columns if k.startswith("b")}
        c_keys: dict[str, str] = {
            k[2:]: k for k in columns if k.startswith("c")}
        n_key: str | None = a_keys[KEY_N] if KEY_N in a_keys else (
            b_keys[KEY_N] if KEY_N in b_keys else (c_keys.get(KEY_N)))
        if n_key is None:
            raise ValueError("Huh?")
        if KEY_N not in a_keys:
            a_keys[KEY_N] = n_key
        if KEY_N not in b_keys:
            b_keys[KEY_N] = n_key
        if KEY_N not in c_keys:
            c_keys[KEY_N] = n_key

        #: the first reader
        self.ra: Final[CsvReader] = CsvReader({
            k: columns[v] for k, v in a_keys.items()})
        #: the second reader
        self.rb: Final[CsvReader] = CsvReader({
            k: columns[v] for k, v in b_keys.items()})
        #: the third reader
        self.rc: Final[CsvReader] = CsvReader({
            k: columns[v] for k, v in c_keys.items()})

    def parse_row(self, data: list[str]) -> tuple[
            SampleStatistics, SampleStatistics, SampleStatistics]:
        """
        Parse a row.

        :param data: the row data
        :return: the result
        """
        return (self.ra.parse_row(data), self.rb.parse_row(data),
                self.rc.parse_row(data))


class _TCW:
    """A three-csv-writer."""

    def __init__(self, needs_n: bool) -> None:
        """
        Initialize.

        :param needs_n: do we need all n?
        """
        n_set = 7 if needs_n else randint(1, 7)

        #: the first writer
        self._wa: Final[CsvWriter] = CsvWriter("a", (n_set & 1) == 0)
        #: the second writer
        self._wb: Final[CsvWriter] = CsvWriter("b", (n_set & 2) == 0)
        #: the third writer
        self._wc: Final[CsvWriter] = CsvWriter("c", (n_set & 4) == 0)

    def setup(self, data: Iterable[tuple[
            SampleStatistics, SampleStatistics, SampleStatistics]]) \
            -> "_TCW":
        """
        Set up this csv writer based on existing data.

        :param data: the data to setup with
        :returns: this writer
        """
        self._wa.setup(d[0] for d in data)
        self._wb.setup(d[1] for d in data)
        self._wc.setup(d[2] for d in data)
        return self

    def get_column_titles(self, dest: Callable[[str], None]) -> None:
        """
        Get the column titles.

        :param dest: the destination
        """
        self._wa.get_column_titles(dest)
        self._wb.get_column_titles(dest)
        self._wc.get_column_titles(dest)

    def get_row(self, data: tuple[
            SampleStatistics, SampleStatistics, SampleStatistics],
            dest: Callable[[str], None]) -> None:
        """
        Render a single sample statistics to a CSV row.

        :param data: the data sample
        :param dest: the destination list
        """
        self._wa.get_row(data[0], dest)
        self._wb.get_row(data[1], dest)
        self._wc.get_row(data[2], dest)

    def get_header_comments(self, dest: Callable[[str], None]) -> None:
        """
        Get any possible header comments.

        :param dest: the destination
        """
        self._wa.get_header_comments(dest)
        self._wb.get_header_comments(dest)
        self._wc.get_header_comments(dest)

    def get_footer_comments(self, dest: Callable[[str], None]) -> None:
        """
        Get any possible footer comments.

        :param dest: the destination
        """
        self._wa.get_footer_comments(dest)
        self._wb.get_footer_comments(dest)
        self._wc.get_footer_comments(dest)


def __do_test_multi_csv(same_n: bool) -> None:
    """
    Test writing and reading multiple CSV formats.

    :param same_n: do all stats have the same n?
    """
    data: list[tuple[
        SampleStatistics, SampleStatistics, SampleStatistics]] = []

    for _ in range(randint(1, 22)):
        a = __make_sample_statistics(has_geometric_mean=randint(0, 1) <= 0)
        while True:
            b = __make_sample_statistics(
                has_geometric_mean=randint(0, 1) <= 0)
            if (not same_n) or (b.n == a.n):
                break
        while True:
            c = __make_sample_statistics(
                has_geometric_mean=randint(0, 1) <= 0)
            if (not same_n) or (c.n == a.n):
                break
        data.append((a, b, c))

    text: list[str] = []
    csv_write(
        data=data, consumer=text.append,
        setup=_TCW(needs_n=not same_n).setup,
        get_column_titles=_TCW.get_column_titles,
        get_row=_TCW.get_row,
        get_footer_comments=_TCW.get_footer_comments,
        get_header_comments=_TCW.get_header_comments)
    output: list[SampleStatistics] = []
    csv_read(rows=text,  # type: ignore
             setup=_TCR,
             parse_row=_TCR.parse_row,
             consumer=output.append)
    assert len(output) == len(data)
    assert output == data


def test_multi_csv() -> None:
    """Test writing and reading multiple CSV formats."""
    for i in range(12):
        __do_test_multi_csv((i & 1) == 0)


def test_csv_4() -> None:
    """Test the CSV abilities from hand-made data."""
    text_1: list[str] = [
        "n;min;max;mean;med;geom;sd",
        "5;1;;;;;",
        "4;;2;;;;",
        "2;;;3;;;",
        "7;;;;4;;",
        "1;;;;;5;",
        "9;1;1;;;;0",
        "9;0;0;;;;0",
    ]
    data_1: list[SampleStatistics] = []
    csv_read(rows=text_1,
             setup=CsvReader,
             parse_row=CsvReader.parse_row,
             consumer=data_1.append)
    assert len(data_1) == 7
    text_2: list[str] = []
    writer: CsvWriter = CsvWriter()
    csv_write(data_1, text_2.append, CsvWriter.get_column_titles,
              CsvWriter.get_row, writer.setup)
    data_2: list[SampleStatistics] = []
    csv_read(rows=text_2,
             setup=CsvReader,
             parse_row=CsvReader.parse_row,
             consumer=data_2.append)
    assert data_2 == data_1

    reader: CsvReader = CsvReader({
        s: i for i, s in enumerate(text_2[0].split(";"))})
    optional: list[str] = []
    writer.get_optional_row(1, optional.append, n=5)
    stat = reader.parse_optional_row(optional)
    assert stat is not None
    assert stat.n == 5
    assert stat.minimum == 1
    assert stat.maximum == 1
    assert stat.stddev == 0
    assert stat.mean_geom == 1

    optional.clear()
    writer.get_optional_row(None, optional.append)
    assert reader.parse_optional_row(optional) is None

    optional.clear()
    writer.get_optional_row(data_1[0], optional.append, data_1[0].n)
    assert reader.parse_optional_row(optional) == data_1[0]

    optional.clear()
    with pytest.raises(ValueError):
        writer.get_optional_row(
            data_1[0], optional.append, data_1[0].n + 1)

    optional.clear()
    writer.get_optional_row(data_1[0], optional.append, None)
    assert reader.parse_optional_row(optional) == data_1[0]
