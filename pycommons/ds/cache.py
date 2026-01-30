"""A factory for functions checking whether argument values are new."""
from typing import Callable, Final, TypeVar

#: a type variable for the representation-base cache
#: :func:`pycommons.ds.cache.repr_cache`.
T = TypeVar("T")


def is_new() -> Callable[[str], bool]:
    """
    Create a function returning `True` when seeing new values.

    Creates a function which returns `True` only the first time it receives a
    given  argument and `False` all subsequent times.
    This is based on https://stackoverflow.com/questions/27427067

    :returns: a function `is_new(xx)` that will return `True` the first
        time it encounters any value `xx` and `False` for all values it has
        already seen

    >>> check1: Callable[[str], bool] = is_new()
    >>> print(check1("a"))
    True
    >>> print(check1("a"))
    False
    >>> print(check1("b"))
    True
    >>> print(check1("b"))
    False

    >>> check2: Callable[[int], bool] = is_new()
    >>> print(check2(1))
    True
    >>> print(check2(1))
    False
    >>> print(check2(3))
    True
    >>> print(check2(4))
    True
    >>> print(check2(3))
    False
    """
    setdefault: Final[Callable] = {}.setdefault
    n = 0  # noqa

    def __add(x) -> bool:
        nonlocal n
        n += 1
        return setdefault(x, n) == n

    return __add


def repr_cache() -> Callable[[T], T]:
    """
    Create a cache based on the string representation of an object.

    In this type of cache is that the `repr`-representations of objects
    are used as keys. The first time an object with a given representation is
    encountered, it is stored in the cache and returned. The next time an
    object with the same representation is put into this method, the original
    object with that representation is returned instead.

    This can be used to still cache and canonically retrieve objects which by
    themselves are not hashable, like numpy arrays. While the cache itself is
    not memory-friendly, it can be used to build data structures that re-use
    the same objects again and again. If these data structures are heavily
    used, then this can improve the hardware-cache-friendliness of the
    corresponding code.

    :return: the cache function
    :raises TypeError: if the type of a cached object is incompatible with the
        type of a requested object

    >>> cache1: Callable[[str], str] = repr_cache()
    >>> a = f"{1 * 5}"
    >>> b = "5"
    >>> a is b
    False

    >>> cache1(a)
    '5'
    >>> cache1(b) is a
    True

    >>> cache2: Callable[[float], float] = repr_cache()
    >>> x = 5.78
    >>> y = 578 / 100
    >>> y is x
    False
    >>> cache2(y)
    5.78
    >>> cache2(x) is y
    True

    >>> cache3: Callable[[dict[int, str]], dict[int, str]] = repr_cache()
    >>> a = {1: '1', 3: '3', 7: '7'}
    >>> b = {1: '1', 3: '3', 7: '7'}
    >>> print(cache3(a))
    {1: '1', 3: '3', 7: '7'}
    >>> print(cache3(a) is a)
    True
    >>> print(cache3(b) is a)
    True
    >>> print(cache3(b) is b)
    False

    >>> class Dummy:
    ...     def __repr__(self):
    ...         return "22222"
    >>> cache4: Callable[[Dummy], Dummy] = repr_cache()
    >>> _ = cache4(Dummy())
    >>> try:
    ...     cache4(22222)
    ... except TypeError as te:
    ...     s = str(te)
    >>> print(s[:34])
    Cache yields element of wrong type
    >>> "Dummy" in s
    True
    >>> "int" in s
    True
    """
    setdefault: Final[Callable] = {}.setdefault

    def __add(x: T) -> T:
        z: Final[T] = setdefault(repr(x), x)
        tpe = type(x)
        if not isinstance(z, tpe):
            raise TypeError("Cache yields element of wrong type "
                            f"{type(z)}, should be {tpe}.")
        return z

    return __add
