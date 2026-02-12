"""Test the integer mathmatics."""

from math import gcd
from random import randint

from pycommons.math.int_math import try_int_div


def test_try_int_div() -> None:
    """Test the try-int-div."""
    for i in range(1, 20):
        for j in range(1, 20):
            for _ in range(1000):
                a = randint(1, 10 ** i)
                b = randint(1, 10 ** j)
                c = gcd(a, b)
                r1 = try_int_div(a, b)
                r2 = (a // c) / (b // c)
                if int(r2) == r2:
                    r2 = int(r2)

                diff_a = b * r1
                if int(diff_a) == diff_a:
                    diff_a = int(diff_a)
                diff_a = abs(a - diff_a)
                if int(diff_a) == diff_a:
                    diff_a = int(diff_a)

                diff_b = r2 * b
                if int(diff_b) == diff_b:
                    diff_b = int(diff_b)
                diff_b = abs(a - diff_b)
                if int(diff_b) == diff_b:
                    diff_b = int(diff_b)

                assert diff_a <= diff_b
