"""Test the integer mathmatics."""


from random import randint

from pycommons.math.int_math import try_int_div


def test_try_int_div() -> None:
    """Test the try-int-div."""
    for _ in range(1000):
        a = randint(1, 1_000_000_000_000)
        b = randint(1, 1_000_000_000_000)
        r1 = try_int_div(a, b)
        r2 = a / b
        assert abs(a - (r1 * b)) <= abs(a - (r2 * b))
