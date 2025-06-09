"""Tools for working with prime numbers."""

from collections import deque
from typing import Final, Generator

from pycommons.types import type_error


def primes(maximum: int = 2 ** 32) -> Generator[int, None, None]:
    """
    Provide a sequence of prime numbers.

    This function is a generator that returns the prime numbers in their
    natural order starting at `2`. It will return numbers at most up to
    the given `maximum` value. For this purpose, it iteratively builds
    something like the Sieve of Eratosthenes.

    :param maximum: the maximum number to consider
    :returns: the prime numbers

    >>> list(primes(-1))
    []

    >>> list(primes(0))
    []

    >>> list(primes(1))
    []

    >>> list(primes(2))
    [2]

    >>> list(primes(3))
    [2, 3]

    >>> list(primes(4))
    [2, 3]

    >>> list(primes(5))
    [2, 3, 5]

    >>> list(primes(6))
    [2, 3, 5]

    >>> list(primes(7))
    [2, 3, 5, 7]

    >>> list(primes(8))
    [2, 3, 5, 7]

    >>> list(primes(9))
    [2, 3, 5, 7]

    >>> list(primes(10))
    [2, 3, 5, 7]

    >>> list(primes(11))
    [2, 3, 5, 7, 11]

    >>> list(primes(12))
    [2, 3, 5, 7, 11]

    >>> list(primes(13))
    [2, 3, 5, 7, 11, 13]

    >>> list(primes(14))
    [2, 3, 5, 7, 11, 13]

    >>> list(primes(15))
    [2, 3, 5, 7, 11, 13]

    >>> list(primes(16))
    [2, 3, 5, 7, 11, 13]

    >>> list(primes(17))
    [2, 3, 5, 7, 11, 13, 17]

    >>> list(primes(18))
    [2, 3, 5, 7, 11, 13, 17]

    >>> list(primes(19))
    [2, 3, 5, 7, 11, 13, 17, 19]

    >>> list(primes(20))
    [2, 3, 5, 7, 11, 13, 17, 19]

    >>> list(primes(199))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, \
71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, \
151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199]

    >>> list(primes(200))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, \
71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, \
151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199]

    >>> list(primes(201))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, \
71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, \
151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199]

    >>> list(primes(1000))
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, \
71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, \
151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, \
233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, \
317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, \
419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, \
503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, \
607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, \
701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, \
811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, \
911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983, 991, 997]

    >>> try:
    ...     for t in primes(1.0):
    ...         pass
    ... except TypeError as te:
    ...     print(te)
    maximum should be an instance of int but is float, namely 1.0.
    """
    if not isinstance(maximum, int):
        raise type_error(maximum, "maximum", int)
    if maximum <= 1:
        return

    yield 2
    if maximum <= 2:
        return

    yield 3
    if maximum <= 3:
        return

    current: int = 5
    check_primes: Final[list[int]] = []  # the numbers <= sqrt(current)
    next_primes: Final[deque[int]] = deque([3])   # larger primes
    check_limit: int = 0  # the square of the largest number in check_primes
    while current <= maximum:
        is_prime: bool = True

        # check all odd primes <= sqrt(current)
        for check in check_primes:
            if (current % check) == 0:
                is_prime = False
                break

        # ...well, there might be one more to check, maybe we need to step the
        # sqrt up by one?
        if check_limit <= current:
            check = next_primes.popleft()
            check_limit = check * check
            is_prime &= (current % check) != 0
            check_primes.append(check)

        if is_prime:
            yield current
            next_primes.append(current)
        current += 2
