"""An immutable version of the :class:`typing.Mapping` interface."""
from types import MappingProxyType
from typing import Mapping, TypeVar

from pycommons.types import type_error

#: the type variable for mapping keys
K = TypeVar("K")
#: the type variable for mapping values
V = TypeVar("V")


def immutable_mapping(a: Mapping[K, V]) -> Mapping[K, V]:
    """
    Create an immutable view of a `Mapping`.

    :param a: the input `Mapping`
    :returns: an immutable view on the `Mapping` `a` (the view will change
        if `a` is changed, but you cannot change `a` via the view)

    >>> x = {1: 1, 2: 7, 3: 8}
    >>> y = immutable_mapping(x)
    >>> x is y
    False
    >>> x == y
    True
    >>> x[1] == y[1]
    True
    >>> x[2] == y[2]
    True
    >>> x[3] == y[3]
    True
    >>> z = immutable_mapping(x)
    >>> x is z
    False
    >>> x == z
    True
    >>> y is z
    False
    >>> z = immutable_mapping(y)
    >>> x is z
    False
    >>> y is z
    True
    >>> x == z
    True
    >>> x[9] = 23
    >>> y[9] == x[9]
    True

    >>> try:
    ...     y[1] = 2
    ... except TypeError as te:
    ...     print(te)
    'mappingproxy' object does not support item assignment

    >>> try:
    ...     immutable_mapping(5)
    ... except TypeError as e:
    ...     print(e)
    a should be an instance of typing.Mapping but is int, namely '5'.
    """
    if not isinstance(a, Mapping):
        raise type_error(a, "a", Mapping)
    if isinstance(a, MappingProxyType):
        return a
    return MappingProxyType(a)
