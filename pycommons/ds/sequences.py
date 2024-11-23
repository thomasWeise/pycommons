"""Tools for working with sequences."""

from heapq import merge
from typing import Callable, Final, Generator, Iterable, Iterator, TypeVar

from pycommons.types import type_error

#: the type of the element of the sequences to process
T = TypeVar("T")


class __Reiterator(Iterable[T]):
    """The internal class for re-iteration."""

    def __init__(self, source: Iterator[T]) -> None:
        """
        Create the re-iterator.

        :param source: the source
        """
        #: the original source
        self.__source: Final[Iterator[T]] = source
        #: we store all elements from source for re-iteration
        self.__more: Final[list[T]] = []

    def __iter__(self) -> Generator[T, None, None]:
        """
        Generate the sequence of elements.

        :return: the generator
        """
        get_length: Callable[[], int] = self.__more.__len__
        get: Callable[[int], T] = self.__more.__getitem__
        append: Final[Callable[[T], None]] = self.__more.append
        nexter: Final[Callable[[], T]] = self.__source.__next__
        pos: int = 0  # The next position in __more.
        skip: int = -1  # The last element in __more we took from __source.
        try:  # We always get to the StopITeration of __source.
            while True:  # Until we reached the end of list and end of iter.
                ll: int = get_length()  # Get length (may have changed).
                while pos < ll:  # First, return all elements from __more.
                    if pos != skip:  # Skip = the element we returned last.
                        yield get(pos)  # Yield the __more list element.
                    pos += 1  # Increment position.
                skip = get_length()  # Get the length: May have changed!
                if skip > ll:  # Maybe something changed since yield.
                    skip = -1  # Invalidate skip, we instead return from list.
                    continue
                other = nexter()  # Get next actual iteration element.
                append(other)  # Store the element in the internal list.
                yield other  # Yield the element
        except StopIteration:
            pass


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

    For such single-use objects, a new :class:`Iterable` wrapper is created.
    This wrapper will iterate over the original sequence, but cache all
    elements in an internal :class:`list`. When you iterate over the sequence
    again, the elements in the :class:`list` will be used. This means that
    all elements of the original sequence will be stored in memory. However,
    they are only stored if/when they are actually accessed via the iteration
    sequence. If you do not iterate over them completely, they are not all
    stored.

    This form of re-iterabling is useful if you maybe generate items from a
    slower sequence or do not plan to use all of them. If you want to use
    all elements several times anyway, it may be more efficient to just wrap
    the original source into a :class:`tuple`. But if, for example, your
    sequence is the result of iterating over a directory tree on the file
    system, or maybe if it comes from loading a file, then using
    :func:`reiterable` could be useful.

    This is also true if you actually process the generated sequence in some
    way that may fail or terminate early. Then, first loading all data into
    a :class:`tuple` may be annoying if your first processed element after
    that causes a failure or early termination. The bit of overhead of
    :func:`reiterable` may then well be worth your while.

    Of course, this can only work if the :class:`Iterator` is not otherwise
    used after calling this function. If you extract elements from the
    :class:`Iterator` by yourself otherwise, maybe via :func:`next`, then
    :func:`reiterable` cannot work. However, if you only apply :func:`next`
    or other looping paradigms to the :class:`Iterable` returned by
    :func:`reiterable`, then you can iterate as often as you want over a
    :class:`Generator`, for example.

    :param source: the data source
    :return: the resulting re-iterable iterator
    :raises TypeError: if `source` is neither an :class:`Iterable` nor an
        :class:`Iterator`.

    >>> g = (i ** 2 for i in range(5))
    >>> r = reiterable(g)
    >>> tuple(r)
    (0, 1, 4, 9, 16)
    >>> tuple(r)
    (0, 1, 4, 9, 16)
    >>> tuple(r)
    (0, 1, 4, 9, 16)
    >>> tuple(r)
    (0, 1, 4, 9, 16)
    >>> tuple(g)
    ()

    >>> g = (i ** 2 for i in range(5))
    >>> r = reiterable(g)
    >>> i1 = iter(r)
    >>> i2 = iter(r)
    >>> next(i1)
    0
    >>> next(i2)
    0
    >>> next(i2)
    1
    >>> next(i1)
    1
    >>> next(i1)
    4
    >>> next(i1)
    9
    >>> next(i2)
    4
    >>> next(i2)
    9
    >>> i3 = iter(r)
    >>> next(i3)
    0
    >>> next(i3)
    1
    >>> next(i3)
    4
    >>> next(i3)
    9
    >>> next(i3)
    16
    >>> next(i2)
    16
    >>> try:
    ...     next(i2)
    ... except StopIteration as si:
    ...     print(type(si))
    <class 'StopIteration'>
    >>> try:
    ...     next(i3)
    ... except StopIteration as si:
    ...     print(type(si))
    <class 'StopIteration'>
    >>> next(i1)
    16
    >>> try:
    ...     next(i1)
    ... except StopIteration as si:
    ...     print(type(si))
    <class 'StopIteration'>

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

    >>> tuple(reiterable((x for x in range(5))))
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
    <class 'pycommons.ds.sequences.__Reiterator'>
    """
    if isinstance(source, Iterator):
        return __Reiterator(source)  # solidify iterators into tuples
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
