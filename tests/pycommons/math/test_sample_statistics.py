"""Test the integer mathmatics."""


from math import inf, log2, nextafter, sqrt
from random import expovariate, randint, uniform
from sys import float_info
from typing import Callable, Final, cast

from pycommons.io.csv import csv_read, csv_write
from pycommons.math.sample_statistics import (
    CsvReader,
    CsvWriter,
    SampleStatistics,
    from_sample,
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
    assert isinstance(data, SampleStatistics)
    assert data.n >= 1
    assert data.minimum <= data.maximum
    assert data.minimum <= data.mean_arith <= data.maximum
    assert data.minimum <= data.median <= data.maximum
    assert (data.mean_geom is None) or (
        data.minimum <= data.mean_geom <= data.mean_arith)
    assert (data.n == 1) == (data.stddev is None)
    assert (data.stddev is None) or ((data.stddev == 0) == (
        data.minimum >= data.maximum))
    return data


def __make_sample_statistics(
        multiple_samples: bool, all_same: bool, has_geom: bool) \
        -> SampleStatistics:
    """
    Create random sample statistics.

    :param multiple_samples: are there multiple samples?
    :param all_same: are all the sampled values the same?
    :param has_geom: do we have a geometric mean?
    :returns: the sample statistics
    """
    is_int: Final[bool] = randint(0, 1) <= 0
    func: Final[Callable[[int | float, int | float], int | float]] = cast(
        Callable[[int | float, int | float], int | float],
        randint if is_int else uniform)

    n: Final[int] = max(2, min(MAX_N, int(expovariate(0.01)))) \
        if multiple_samples else 1

    range_min: int = int(2 ** randint(0, MAX_2_POWER))
    range_max: int = int(2 ** randint(0, MAX_2_POWER))
    if has_geom:
        if range_min > range_max:
            range_min, range_max = range_max, range_min
        range_min = max(range_min, 1 if is_int else 1e-20)
        range_max = max(range_max, (range_min + 1) if is_int else
                        nextafter(1.000001 * range_min, inf))
    else:
        range_min = -range_min

    value: Final[int | float] = func(range_min, range_max)
    data: Final[list[int | float]] = [value]
    while list.__len__(data) < n:
        data.append(value if all_same else func(range_min, range_max))

    return __check(from_sample(data))


def test_sample_stats() -> None:
    """Test the sample statistics."""
    for _ in range(1000):
        __make_sample_statistics(
            randint(0, 1) <= 0, randint(0, 1) <= 0, randint(0, 1) <= 0)


def test_csv() -> None:
    """Test the CSV abilities."""
    for all_same in [-1, 0, 1]:
        for multi in [-1, 0, 1]:
            for has_gm in [-1, 0, 1]:
                for _ in range(10):
                    data: list[SampleStatistics] = []
                    for _ in range(randint(1, 100)):
                        data.append(__check(__make_sample_statistics(
                            False if multi < 0 else (True if multi > 0 else (
                                    randint(0, 1) <= 0)),
                            False if all_same < 0 else (
                                True if all_same > 0 else (
                                    randint(0, 1) <= 0)),
                            False if has_gm < 0 else (
                                True if has_gm > 0 else (
                                    randint(0, 1) <= 0)))))
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
