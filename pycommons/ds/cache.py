"""A factory for functions checking whether argument values are new."""
from typing import Callable, Final, TypeVar


def str_is_new() -> Callable[[str], bool]:
    """
    Create a function returning `True` when seeing new `str` values.

    Creates a function which returns `True` only the first time it receives a
    given string argument and `False` all subsequent times.
    This is based on https://stackoverflow.com/questions/27427067

    :returns: a function `str_is_new(xx)` that will return `True` the first
        time it encounters any value `xx` and `False` for all values it has
        already seen

    >>> check = str_is_new()
    >>> print(check("a"))
    True
    >>> print(check("a"))
    False
    >>> print(check("b"))
    True
    >>> print(check("b"))
    False
    """
    setdefault: Final[Callable] = {}.setdefault
    n = 0  # noqa

    def __add(x) -> bool:
        nonlocal n
        n += 1
        return setdefault(x, n) == n

    return __add


#: a type variable for the representation-base cache
#: :func:`pycommons.ds.cache.repr_cache`.
T = TypeVar("T")


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

    >>> cache: Callable[[object], object] = repr_cache()

    >>> a = f"{1 * 5}"
    >>> b = "5"
    >>> a is b
    False

    >>> cache(a)
    '5'
    >>> cache(b) is a
    True

    >>> x = 5.78
    >>> y = 578 / 100
    >>> y is x
    False

    >>> cache(y)
    5.78
    >>> cache(x) is y
    True

    >>> class Dummy:
    ...     def __repr__(self):
    ...         return "22222"
    >>> _ = cache(Dummy())
    >>> try:
    ...     cache(22222)
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
