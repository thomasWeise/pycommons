"""Tools for working with sequences."""

from heapq import merge
from typing import Generator, Iterable, Iterator, TypeVar

from pycommons.types import type_error

#: the type of the element of the sequences to process
T = TypeVar("T")


def reiterable(source: Iterable[T] | Iterator[T]) -> Iterable[T]:
    """
    Ensure that an :class:`Iterable` can be iterated over multiple times.

    This function will solidify an :class:`Iterator` into an
    :class:`Iterable`. In Python, :class:`Iterator` is a sub-class of
    :class:`Iterable`. This means that if your function accepts instances of
    :class:`Iterable` as input, it may expect to be able to iterate over them
    multiple times. However, if an :class:`Iterator` is passed in, which also
    is an instance of :class:`Iterable` and thus fulfills the function's type
    requirement, this is not the case. A typical example of this would be if
    a :class:`Generator` is passed in. A :class:`Generator` is an instance of
    :class:`Iterator`, which, in turn, is an instance of :class:`Iterable`.
    However, you can iterate over a :class:`Generator` only once.

    :param source: the data source
    :return: the resulting re-iterable iterator
    :raises TypeError: if `source` is neither an :class:`Iterable` nor an
        :class:`Iterator`.

    >>> a = [1, 2, 3]
    >>> reiterable(a) is a
    True

    >>> a = (1, 2, 3)
    >>> reiterable(a) is a
    True

    >>> a = {1, 2, 3}
    >>> reiterable(a) is a
    True

    >>> a = {1: 1, 2: 2, 3: 3}
    >>> reiterable(a) is a
    True

    >>> k = a.keys()
    >>> reiterable(k) is k
    True

    >>> k = a.values()
    >>> reiterable(k) is k
    True

    >>> reiterable((x for x in range(5)))
    (0, 1, 2, 3, 4)

    >>> try:
    ...     reiterable(None)
    ... except TypeError as te:
    ...     print(str(te)[:60])
    source should be an instance of any in {typing.Iterable, typ

    >>> try:
    ...     reiterable(1)
    ... except TypeError as te:
    ...     print(str(te)[:60])
    source should be an instance of any in {typing.Iterable, typ

    >>> type(merge_sorted_and_return_unique([1, 2, 3,], [2, 2]))
    <class 'generator'>

    >>> type(reiterable(merge_sorted_and_return_unique([1, 2, 3,], [2, 2])))
    <class 'tuple'>
    """
    if isinstance(source, Iterator):
        return tuple(source)  # solidify iterators into tuples
    if not isinstance(source, Iterable):
        raise type_error(source, "source", (Iterable, Iterator))
    return source  # iterables can be returned as-is


def merge_sorted_and_return_unique(
        *seqs: Iterable[T]) -> Generator[T, None, None]:
    """
    Merge sorted sequences of integers and return only unique values.

    You can provide multiple sequences, all of which must be sorted.
    This function then merges them into a single sorted sequence which
    contains each elemenet at most once.
    A typical use case would be to combine the result of
    :func:`pycommons.math.primes.primes` with some pre-defined values into
    a sorted sequence.

    Notice that the elements of the sequence must support the less-than
    operator, i.e., have a `__lt__` dunder method. Otherwise this function
    will crash.

    The returned sequence is guaranteed to provide strictly increasing values.

    :param seqs: the sequences, i.e., some instances of :class:`Iterable` or
        :class:`Iterator`
    :return: a merged sequence of integers
    :raises TypeError: if any of the provided iterators or any of their
        elements is `None`, or if any of the elements in `seqs`is not an
        :class:`Iterable`.

    >>> list(merge_sorted_and_return_unique([1, 2, 3,], [2, 2]))
    [1, 2, 3]

    >>> from pycommons.math.primes import primes
    >>> list(merge_sorted_and_return_unique(primes(14), [1, 10]))
    [1, 2, 3, 5, 7, 10, 11, 13]

    >>> list(merge_sorted_and_return_unique(
    ...     primes(14), primes(17), [1, 2, 10, 100]))
    [1, 2, 3, 5, 7, 10, 11, 13, 17, 100]

    >>> try:
    ...     for _ in merge_sorted_and_return_unique(1):
    ...         pass
    ... except TypeError as te:
    ...     print(te)
    'int' object is not iterable

    >>> try:
    ...     for j in merge_sorted_and_return_unique([3], 1):
    ...         print(j)
    ... except TypeError as te:
    ...     print(te)
    'int' object is not iterable

    >>> try:
    ...     for j in merge_sorted_and_return_unique([None], [None]):
    ...         print(j)
    ... except TypeError as te:
    ...     print(te)
    Element must not be None.

    >>> try:
    ...     for j in merge_sorted_and_return_unique([None], [1]):
    ...         print(j)
    ... except TypeError as te:
    ...     print(te)
    '<' not supported between instances of 'NoneType' and 'int'

    >>> try:
    ...     for j in merge_sorted_and_return_unique(None, [1]):
    ...         print(j)
    ... except TypeError as te:
    ...     print(te)
    'NoneType' object is not iterable

    >>> try:
    ...     for j in merge_sorted_and_return_unique([print, len], [repr]):
    ...         print(j)
    ... except TypeError as te:
    ...     print(te)
    '<' not supported between instances of 'builtin_function_or_method' \
and 'builtin_function_or_method'
    """
    last: T | None = None
    for item in merge(*seqs):
        if item is None:
            raise TypeError("Element must not be None.")
        if (last is None) or (last < item):  # type: ignore  # noqa
            yield item
        last = item
