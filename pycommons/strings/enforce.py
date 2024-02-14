"""Some string splitting and processing routines."""

from typing import (
    Any,
)

from pycommons.strings.chars import WHITESPACE_OR_NEWLINE
from pycommons.types import type_error


def enforce_str(value: Any) -> str:
    """
    Return the input if it is a string, otherwise throw an error.

    :param value: the value
    :return: `value` if `isinstance(value, str)`
    :raises TypeError: if not `isinstance(value, str)`

    >>> enforce_str("1")
    '1'
    >>> enforce_str("")
    ''

    >>> try:
    ...     enforce_str(1)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is int, namely '1'.

    >>> try:
    ...     enforce_str(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is None.
    """
    if not isinstance(value, str):
        raise type_error(value, "value", str)
    return value


def enforce_non_empty_str(value: Any) -> str:
    """
    Enforce that a text is a non-empty string.

    :param value: the text
    :returns: the text
    :raises TypeError: if `text` is not a `str`
    :raises ValueError: if `text` is empty

    >>> enforce_non_empty_str("1")
    '1'
    >>> enforce_non_empty_str(" 1 1 ")
    ' 1 1 '

    >>> try:
    ...     enforce_non_empty_str("")
    ... except ValueError as ve:
    ...     print(ve)
    Non-empty str expected, but got ''.

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
    if str.__len__(value) == 0:
        raise ValueError(f"Non-empty str expected, but got {value!r}.")
    return value


def enforce_non_empty_str_without_ws(value: Any) -> str:
    r"""
    Enforce that a text is a non-empty string without white space.

    :param value: the text
    :returns: the text, if everything does well
    :raises TypeError: if `text` is not a `str`
    :raises ValueError: if `text` is empty or contains any white space
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
    ...     enforce_non_empty_str_without_ws("")
    ... except ValueError as ve:
    ...     print(ve)
    Non-empty str expected, but got ''.

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
    if str.__len__(value) == 0:
        raise ValueError(f"Non-empty str expected, but got {value!r}.")
    if any(map(value.__contains__, WHITESPACE_OR_NEWLINE)):
        raise ValueError(
            f"No white space allowed in string, but got {value!r}.")
    return value
