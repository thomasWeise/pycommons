"""Routines for checking whether a value is a non-empty string w/o spaces."""

from typing import Any, Final

from pycommons.strings.chars import WHITESPACE_OR_NEWLINE


def enforce_non_empty_str(value: Any) -> str:
    """
    Enforce that a text is a non-empty string.

    :param value: the value to be checked whether it is a non-empty string
    :returns: the value, but as type `str`
    :raises TypeError: if `value` is not a `str`
    :raises ValueError: if `value` is empty

    >>> enforce_non_empty_str("1")
    '1'
    >>> enforce_non_empty_str(" 1 1 ")
    ' 1 1 '

    >>> try:
    ...     enforce_non_empty_str("")
    ... except ValueError as ve:
    ...     print(ve)
    Non-empty str expected, but got empty string.

    >>> try:
    ...     enforce_non_empty_str(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     enforce_non_empty_str(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'
    """
    if str.__len__(value) <= 0:
        raise ValueError("Non-empty str expected, but got empty string.")
    return value


def enforce_non_empty_str_without_ws(value: Any) -> str:
    r"""
    Enforce that a text is a non-empty string without white space.

    :param value: the value to be checked whether it is a non-empty string
        without any white space
    :returns: the value, but as type `str`
    :raises TypeError: if `value` is not a `str`
    :raises ValueError: if `value` is empty or contains any white space
        characters

    >>> enforce_non_empty_str_without_ws("1")
    '1'

    >>> try:
    ...     enforce_non_empty_str_without_ws(" 1 1 ")
    ... except ValueError as ve:
    ...     print(ve)
    No white space allowed in string, but got ' 1 1 '.

    >>> try:
    ...     enforce_non_empty_str_without_ws("a\tb")
    ... except ValueError as ve:
    ...     print(ve)
    No white space allowed in string, but got 'a\tb'.

    >>> try:
    ...     enforce_non_empty_str_without_ws("012345678901234567890 12345678")
    ... except ValueError as ve:
    ...     print(ve)
    No white space allowed in string, but got '012345678901234567890 12345678'.

    >>> try:
    ...     enforce_non_empty_str_without_ws(
    ...         "012345678901234567890 1234567801234567890123456789012345678")
    ... except ValueError as ve:
    ...     print(str(ve)[10:])
    pace allowed in string, but got '012345678901234567890 12345678...'.

    >>> try:
    ...     enforce_non_empty_str_without_ws("")
    ... except ValueError as ve:
    ...     print(ve)
    Non-empty str expected, but got empty string.

    >>> try:
    ...     enforce_non_empty_str_without_ws(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     enforce_non_empty_str_without_ws(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'
    """
    strlen: Final[int] = str.__len__(value)
    if strlen <= 0:
        raise ValueError("Non-empty str expected, but got empty string.")
    if any(map(value.__contains__, WHITESPACE_OR_NEWLINE)):
        if strlen > 32:  # take care of strings that are too long
            value = str.__getitem__(value, slice(0, 30, 1)) + "..."
        raise ValueError(
            f"No white space allowed in string, but got {value!r}.")
    return value
