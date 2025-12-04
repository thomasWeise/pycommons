"""Test the integer mathmatics."""

from contextlib import suppress
from itertools import product
from math import inf, nextafter
from random import expovariate, randint, shuffle, uniform
from statistics import mean as statmean
from statistics import stdev as statstddev
from typing import Final, Iterable

import pytest

from pycommons.io.csv import CsvReader as CsvReaderBase
from pycommons.io.csv import CsvWriter as CsvWriterBase
from pycommons.math.sample_statistics import SampleStatistics
from pycommons.math.stream_statistics import (
    KEY_N,
    CsvReader,
    CsvWriter,
    StreamStatistics,
)

#: the maximum n
MAX_N: Final[int] = 1000
#: the maximum 2 power
MAX_2_POWER: Final[int] = 30


def __check(data: StreamStatistics) -> StreamStatistics:
    """
    Check a sample statistics.

    :param data: the data
    :returns: the data
    """
    if not isinstance(data, StreamStatistics):
        raise TypeError(f"{type(data)}")
    if data.n < 1:
        raise ValueError(f"n={data.n}")
    if data.minimum > data.maximum:
        raise ValueError(f"{data.minimum} > {data.maximum}")
    if not (data.minimum <= data.mean_arith <= data.maximum):
        raise ValueError(
            f"not {data.minimum} <= {data.mean_arith} <= {data.maximum}")
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


def __check_with_data(stat: StreamStatistics,
                      data: tuple[int | float, ...]) -> StreamStatistics:
    """
    Check the sample statistics with respect to the data.

    :param stat: the statistics
    :param data: the data
    :returns: the statistics
    """
    if not isinstance(stat, StreamStatistics):
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

    if stat.stddev is not None:
        mm = None
        with suppress(BaseException):
            mm = statstddev(data)
        if mm is not None:
            __enforce_same(stat.stddev, mm, data)

    return stat


def __make_stream_statistics(
        multiple_samples: bool = True,
        all_samples_same: bool = False,
        has_geometric_mean: bool = True,
        all_samples_int: bool = False,
        all_samples_float: bool = False,
        n: int | None = None) -> StreamStatistics:
    """
    Create random sample statistics.

    :param multiple_samples: are there multiple samples?
    :param all_samples_same: are all the sampled values the same?
    :param has_geometric_mean: do we have a geometric mean?
    :param all_samples_int: should we use only integer numbers?
    :param all_samples_float: should we use only floating point numbers?
    :param n: the number of samples to generate
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

    n_samples: Final[int] = (max(2, min(MAX_N, int(expovariate(0.01))))
                             if multiple_samples else 1) if n is None else n
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
    result: Final[StreamStatistics] = __check(StreamStatistics.from_samples(
        use_data))
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

        result = __make_stream_statistics(
            multi, all_same, randint(0, 1) <= 0, all_int, all_float)
        if result is None:
            raise TypeError(f"{result}??")


def __make_stream_statistics_list(
        more_than_one_statistics: bool = True,
        all_settings_different: bool = False,
        multiple_samples_per_stat: bool = True,
        all_samples_same_per_stat: bool = False,
        has_geometric_mean_per_stat: bool = True,
        all_int_per_stat: bool = False,
        all_float_per_stat: bool = False) -> list[StreamStatistics]:
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
    result: Final[list[StreamStatistics]] = []
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

        result.append(__make_stream_statistics(multi, all_same, (
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
            data: list[StreamStatistics] = (
                __make_stream_statistics_list(
                    more_than_one_statistics, all_settings_different,
                    multiple_samples_per_stat, all_samples_same_per_stat,
                    has_geometric_mean_per_stat, all_int_per_stat,
                    all_float_per_stat))
            text: list[str] = []
            text.extend(CsvWriter.write(data))
            output: list[StreamStatistics] = []
            output.extend(CsvReader.read(rows=text))
            assert len(output) == len(data)
            assert output == data


def test_csv_2() -> None:
    """Test the CSV abilities from hand-made data."""
    text: list[str] = [
        "n;min;max;mean;sd",
        "5;1;;;",
        "4;;2;;",
        "2;;;3;",
        "7;;;4;",
        "1;5;;;",
        "9;1;1;;0",
        "9;0;0;;0",
    ]
    parsed: list[StreamStatistics] = list(CsvReader.read(rows=text))
    assert len(parsed) == 7
    assert parsed[0].minimum == parsed[0].maximum == 1
    assert parsed[0].stddev == 0
    assert parsed[1].minimum == parsed[1].maximum == 2
    assert parsed[1].stddev == 0
    assert parsed[2].minimum == parsed[2].maximum == 3
    assert parsed[2].stddev == 0
    assert parsed[3].minimum == parsed[3].maximum == 4
    assert parsed[3].stddev == 0
    assert parsed[4].minimum == parsed[4].maximum == 5
    assert parsed[4].stddev is None
    assert parsed[5].minimum == parsed[5].maximum == 1
    assert parsed[5].stddev == 0
    assert parsed[6].minimum == parsed[6].maximum == 0
    assert parsed[6].stddev == 0


def test_csv_3() -> None:
    """Test cover some features of the CSV Writer."""
    data: list[StreamStatistics] = [
        __make_stream_statistics(all_samples_same=False),
        __make_stream_statistics(all_samples_same=False),
        __make_stream_statistics(all_samples_same=False),
        __make_stream_statistics(all_samples_same=False)]
    CsvWriter(data, what_short="a")
    CsvWriter(data, what_long="b")
    CsvWriter(data, what_short="a", what_long="b")
    w: CsvWriter = CsvWriter(data)
    data_2 = [__make_stream_statistics(all_samples_same=True),
              __make_stream_statistics(all_samples_same=True),
              __make_stream_statistics(all_samples_same=True),
              __make_stream_statistics(all_samples_same=True)]
    w = CsvWriter(data_2)
    with pytest.raises(ValueError):
        list(w.get_row(data[0]))  # type: ignore


def test_special_cases() -> None:
    """
    Test some pre-defined cases.

    The goal of these tests is to cover as many of the branches of the
    :func:`from_sample` code as possible.
    """
    for case in [
            (32940767.586947955, 57729835, 32490888.319228098, 1907042,
             4182374, 26708100, 1447085, 63934420, 45696552,
             17522830.98384079),
            (-61150665536,),
            (-6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826, -6880975280.107826, -6880975280.107826,
             -6880975280.107826),
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
             -119074, -61377, 8540)]:
        __check_with_data(StreamStatistics.from_samples(
            case), case)


class _TCR(CsvReaderBase):
    """A three-CSV-reader."""

    def __init__(self, columns: dict[str, int]) -> None:
        """
        Initialize.

        :param columns: the columns
        """
        super().__init__(columns)

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
            StreamStatistics, StreamStatistics, StreamStatistics]:
        """
        Parse a row.

        :param data: the row data
        :returns: the result
        """
        return (self.ra.parse_row(data), self.rb.parse_row(data),
                self.rc.parse_row(data))


class _TCW(CsvWriterBase[tuple[
        StreamStatistics, StreamStatistics, StreamStatistics]]):
    """A three-csv-writer."""

    def __init__(self, data: Iterable[tuple[
        StreamStatistics, StreamStatistics, StreamStatistics]],
        scope: str | None = None,
            needs_n: bool = False) -> None:
        """
        Initialize.

        :param data: the data
        :param scope: the scope
        :param needs_n: do we need all n?
        """
        super().__init__(data, scope)
        n_set = 7 if needs_n else randint(1, 7)

        #: the first writer
        self._wa: Final[CsvWriter] = CsvWriter(
            (d[0] for d in data), "a", n_not_needed=(n_set & 1) == 0)
        #: the second writer
        self._wb: Final[CsvWriter] = CsvWriter(
            (d[1] for d in data), "b", n_not_needed=(n_set & 2) == 0)
        #: the third writer
        self._wc: Final[CsvWriter] = CsvWriter(
            (d[2] for d in data), "c", n_not_needed=(n_set & 4) == 0)

    def get_column_titles(self) -> Iterable[str]:
        """
        Get the column titles.

        :returns: the data
        """
        yield from self._wa.get_column_titles()
        yield from self._wb.get_column_titles()
        yield from self._wc.get_column_titles()

    def get_row(self, data: tuple[
            StreamStatistics, StreamStatistics, StreamStatistics]) \
            -> Iterable[str]:
        """
        Render a single sample statistics to a CSV row.

        :param data: the data sample
        :returns: the data
        """
        yield from self._wa.get_row(data[0])
        yield from self._wb.get_row(data[1])
        yield from self._wc.get_row(data[2])

    def get_header_comments(self) -> Iterable[str]:
        """
        Get any possible header comments.

        :returns: the data
        """
        yield from self._wa.get_header_comments()
        yield from self._wb.get_header_comments()
        yield from self._wc.get_header_comments()

    def get_footer_comments(self) -> Iterable[str]:
        """
        Get any possible footer comments.

        :returns: the data
        """
        yield from self._wa.get_footer_comments()
        yield from self._wb.get_footer_comments()
        yield from self._wc.get_footer_comments()


def __do_test_multi_csv(same_n: bool) -> None:
    """
    Test writing and reading multiple CSV formats.

    :param same_n: do all stats have the same n?
    """
    data: list[tuple[
        StreamStatistics, StreamStatistics, StreamStatistics]] = []

    for _ in range(randint(1, 22)):
        a = __make_stream_statistics(has_geometric_mean=randint(0, 1) <= 0)

        if same_n:
            b = __make_stream_statistics(
                has_geometric_mean=randint(0, 1) <= 0,
                n=a.n, multiple_samples=a.n > 1)
        else:
            b = __make_stream_statistics(
                has_geometric_mean=randint(0, 1) <= 0)

        if same_n:
            c = __make_stream_statistics(
                has_geometric_mean=randint(0, 1) <= 0,
                n=a.n, multiple_samples=a.n > 1)
        else:
            c = __make_stream_statistics(
                has_geometric_mean=randint(0, 1) <= 0)
        data.append((a, b, c))

    text: list[str] = list(_TCW.write(data, needs_n=not same_n))
    output: list[tuple[StreamStatistics, ...]] = list(_TCR.read(text))
    assert len(output) == len(data)
    assert output == data


def test_multi_csv() -> None:
    """Test writing and reading multiple CSV formats."""
    for i in range(12):
        __do_test_multi_csv((i & 1) == 0)


def test_csv_4() -> None:
    """Test the CSV abilities from hand-made data."""
    text_1: list[str] = [
        "n;min;max;mean;sd",
        "5;1;;;",
        "4;;2;;",
        "2;;;3;",
        "7;;;4;",
        "1;;;5;",
        "9;1;1;;0",
        "9;0;0;;0",
    ]
    data_1: list[StreamStatistics] = list(CsvReader.read(text_1))
    assert len(data_1) == 7
    text_2: list[str] = list(CsvWriter.write(data_1))
    data_2: list[StreamStatistics] = list(CsvReader.read(text_2))
    assert data_2 == data_1

    reader: CsvReader = CsvReader({
        s: i for i, s in enumerate(text_2[0].split(";"))})
    writer: CsvWriter = CsvWriter(data_2)
    optional: list[str] = list(writer.get_optional_row(1, n=5))
    stat = reader.parse_optional_row(optional)
    assert stat is not None
    assert stat.n == 5
    assert stat.minimum == 1
    assert stat.maximum == 1
    assert stat.stddev == 0

    optional.clear()
    optional.extend(writer.get_optional_row(None))
    assert reader.parse_optional_row(optional) is None

    optional.clear()
    optional.extend(writer.get_optional_row(data_1[0], data_1[0].n))
    assert reader.parse_optional_row(optional) == data_1[0]

    optional.clear()
    with pytest.raises(ValueError):
        optional.extend(writer.get_optional_row(
            data_1[0], data_1[0].n + 1))

    optional.clear()
    optional.extend(writer.get_optional_row(data_1[0], None))
    assert reader.parse_optional_row(optional) == data_1[0]


def test_mixed_csv() -> None:
    """Test what happens if mixed data is written."""
    data: list[StreamStatistics] = [
        StreamStatistics(10, 1, 5, 20, 0.5),
        StreamStatistics(6, 2, 2, 2, 0),
        SampleStatistics(9, 0.1, 5, 6, 5.6, 12, 3)]
    text: list[str] = []
    text.extend(CsvWriter.write(data))
    assert text[0] == "n;min;mean;max;sd"
    assert text[1] == "10;1;5;20;0.5"
    assert text[2] == "6;2;2;2;0"
    assert text[3] == "9;0.1;6;12;3"
