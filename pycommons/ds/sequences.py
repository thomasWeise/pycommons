"""Tools for working with sequences."""

from heapq import merge
from itertools import chain
from typing import Callable, Final, Generator, Iterable, Iterator, TypeVar

from pycommons.types import type_error

#: the type of the element of the sequences to process
T = TypeVar("T")


class __Reiterator(Iterable[T]):
    """The internal class for re-iteration."""

    def __init__(self, source: Iterator[T], can_unpack: bool) -> None:
        """
        Create the re-iterator.

        :param source: the source
        """
        #: the original source
        self.__source: Final[Iterator[T]] = source
        #: we store all elements from source for re-iteration
        self.__more: Final[list[T]] = []
        #: the unpacking state
        self._unpack_state: int = 1 if can_unpack else 0

    def __iter__(self) -> Generator[T, None, None]:
        """
        Generate the sequence of elements.

        :returns: the generator
        """
        if self._unpack_state > 1:
            raise ValueError("Reiterator has been unpacked!")
        get_length: Callable[[], int] = self.__more.__len__
        get: Callable[[int], T] = self.__more.__getitem__
        append: Final[Callable[[T], None]] = self.__more.append
        nexter: Final[Callable[[], T]] = self.__source.__next__
        pos: int = 0  # The next position in __more.
        skip: int = -1  # The last element in __more we took from __source.
        try:  # noqa: PLW0717  # We always get to StopIteration of __source.
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

    def _unpack(self) -> Iterator[T]:
        """
        Unpack the re-iterable.

        :return: the unpacked re-iterable.
        """
        if self._unpack_state <= 0:
            raise ValueError("This re-iterable cannot be unpacked.")
        if self._unpack_state > 1:
            raise ValueError("Re-iterable has already been unpacked!")
        self._unpack_state = 2
        return chain(self.__more, self.__source) if self.__more \
            else self.__source


def reiterable(source: Iterable[T] | Iterator[T],
               unpackable: bool = False) -> Iterable[T]:
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

    The function :func:`unpack_reiterable` can be used to "unpack" the
    reiterable, returning a single-shot iterator of all the data.
    The use case is as follows: Our CSV output facility in
    :mod:`pycommons.io.csv` allows you to turn a sequence of arbitrary
    data elements to a CSV text stream.
    This may require two passes over the data:
    In the first pass, one *may* determine the columns that are needed.
    In some cases, we already know the columns and do not need to pass
    over the data at all.
    In some other cases, we may need one potentially incomplete pass over
    the data, just to check if certain columns are needed.
    For example, when writing out statistical data, we may first want to
    check if there is any record where the geometric mean is defined.
    Once we see the first such record, we know that we need to the
    corresponding column and do not need to check any subsequent elements.
    Then we can write the CSV header with the column names and start the
    actual iteration.
    We thus have one incomplete pass over the data (to find the columns)
    and one complete pass (to write the data).

    During re-iteration, we need to cache all already visited elements.
    Thus, without unpacking, we would necessarily have to cache all the
    elements of the sequence in memory, even if we only need to see them
    once.
    However, what we actually do is that we initialize the columns during
    re-iteration, which may require no pass over the data (no caching), an
    incomplete pass (thus only caching the actually visited elements), or
    a complete pass (caching all elements).
    Then, we unpack the re-iterable for the pass that actually writes the
    data.
    The resulting :class:`Iterable` will first iterate over the cached
    elements and then over the remainder in the original :class:`Iterator`.
    It thus requires the minimum amount of caching.

    For enabling unpacking, you must set `unpackable` to `True`.

    Notice that wrapping pure instances of :class:`Iterable` into re-iterables
    has no effect and neither does unpacking.
    The reason is that if the generation of arbitrarily many iterators is
    already supported anyway, then we do not need to add the ability to do
    this via the caching mechanism offered here.

    :param source: the data source
    :param unpackable: should the iterator be potentially unpackable? (
        see :func:`unpack_reiterable`)
    :returns: the resulting re-iterable iterator
    :raises TypeError: if `source` is neither an :class:`Iterable` nor an
        :class:`Iterator` or if `unpackable` is not a `bool`.
    :raises ValueError: if `source` is a re-iterable that has been unpacked
        via :func:`unpack_reiterable`.

    >>> ri = reiterable(iter(range(4)))
    >>> for i in ri:
    ...     print(i)
    0
    1
    2
    3
    >>> for i in ri:
    ...     print(i)
    0
    1
    2
    3

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

    >>> try:
    ...     reiterable((2, 3), "x")
    ... except TypeError as te:
    ...     print(str(te)[:59])
    unpackable should be an instance of bool but is str, namely

    >>> type(merge_sorted_and_return_unique([1, 2, 3,], [2, 2]))
    <class 'generator'>

    >>> type(reiterable(merge_sorted_and_return_unique([1, 2, 3,], [2, 2])))
    <class 'pycommons.ds.sequences.__Reiterator'>

    >>> def myfunc():
    ...     if hasattr(myfunc, "a"):
    ...         s = getattr(myfunc, "a")
    ...     else:
    ...         s = 0
    ...     for i in range(s, s + 3):
    ...         yield i
    ...     setattr(myfunc, "a", s + 3)
    >>> ri = reiterable(myfunc())
    >>> tuple(ri)
    (0, 1, 2)
    >>> tuple(ri)
    (0, 1, 2)
    >>> ri = reiterable(myfunc())
    >>> tuple(ri)
    (3, 4, 5)
    >>> tuple(ri)
    (3, 4, 5)
    """
    if not isinstance(unpackable, bool):
        raise type_error(unpackable, "unpackable", bool)
    is_reiterator: Final[bool] = isinstance(source, __Reiterator)
    if is_reiterator:
        if source._unpack_state == 0:  # type: ignore
            return source
        if source._unpack_state == 2:  # type: ignore
            raise ValueError("Unsafe operation: The source is a re-"
                             "iterable that has been unpacked.")
    if is_reiterator or isinstance(source, Iterator):
        return __Reiterator(source, unpackable)  # type: ignore
    if not isinstance(source, Iterable):
        raise type_error(source, "source", (Iterable, Iterator))
    return source  # other iterables can be returned as-is


def unpack_reiterable(source: Iterable[T]) -> Iterable[T]:
    """
    Unpack a re-iterable sequence.

    See the documentation of :func:`reiterable` for more details.

    :param source: the source
    :return: the unpacked sequence
    :raises ValueError: if the source is a re-iterable that was created
        using :func:`reiterable` with `unpackable` set to `False` or if
        the re-iterable has already been unpacked.

    >>> x = reiterable(iter(range(5)), unpackable=True)
    >>> y = iter(x)
    >>> next(y)
    0

    >>> next(y)
    1

    >>> z = unpack_reiterable(x)
    >>> for i in z:
    ...     print(i)
    0
    1
    2
    3
    4

    >>> try:
    ...     unpack_reiterable(x)
    ... except ValueError as ve:
    ...     print(ve)
    Re-iterable has already been unpacked!

    >>> try:
    ...     reiterable(x, False)
    ... except ValueError as ve:
    ...     print(ve)
    Unsafe operation: The source is a re-iterable that has been unpacked.

    >>> try:
    ...     unpack_reiterable(reiterable(iter(range(5)), False))
    ... except ValueError as ve:
    ...     print(ve)
    This re-iterable cannot be unpacked.
    """
    return source._unpack() if isinstance(source, __Reiterator) else source


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
    :returns: a merged sequence of integers
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
    for item in merge(*seqs):  # type: ignore
        if item is None:
            raise TypeError("Element must not be None.")
        if (last is None) or (last < item):  # type: ignore  # noqa
            yield item
        last = item
