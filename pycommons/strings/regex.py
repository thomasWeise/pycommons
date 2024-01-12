"""Routines for handling strings."""

from re import MULTILINE, sub
from re import compile as _compile
from typing import Pattern

from pycommons.types import type_error


def regex_sub(search: str | Pattern, replace: str, inside: str) -> str:
    r"""
    Replace all occurrences of 'search' in 'inside' with 'replace'.

    :param search: the regular expression to search, either a string or a
        pattern
    :param replace: the regular expression to replace it with
    :param inside: the string in which to search/replace
    :return: the new string after the recursive replacement

    >>> regex_sub('[ \t]+\n', '\n', ' bla \nxyz\tabc\t\n')
    ' bla\nxyz\tabc\n'
    >>> regex_sub('[0-9]A', 'X', '23A7AA')
    '2XXA'
    >>> from re import compile as cpx
    >>> regex_sub(cpx('[0-9]A'), 'X', '23A7AA')
    '2XXA'

    >>> try:
    ...    regex_sub(1, "1", "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub(None, "1", "2")
    ... except TypeError as te:
    ...    print(te)
    search should be an instance of any in {str, typing.Pattern} but is None.
    >>> try:
    ...    regex_sub("x", 2, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str but is int, namely '2'.
    >>> try:
    ...    regex_sub("x", None, "2")
    ... except TypeError as te:
    ...    print(te)
    replace should be an instance of str but is None.
    >>> try:
    ...    regex_sub(1, 1, "2")
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub("yy", "1", 3)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is int, namely '3'.
    >>> try:
    ...    regex_sub("adad", "1", None)
    ... except TypeError as te:
    ...    print(te)
    inside should be an instance of str but is None.
    >>> try:
    ...    regex_sub(1, "1", 3)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    >>> try:
    ...    regex_sub(1, 3, 5)
    ... except TypeError as te:
    ...    print(str(te)[0:60])
    search should be an instance of any in {str, typing.Pattern}
    """
    if not isinstance(search, Pattern):
        if isinstance(search, str):
            search = _compile(search, flags=MULTILINE)
        else:
            raise type_error(search, "search", (str, Pattern))
    if not isinstance(replace, str):
        raise type_error(replace, "replace", str)
    if not isinstance(inside, str):
        raise type_error(inside, "inside", str)
    while True:
        text: str = sub(pattern=search, repl=replace, string=inside)
        if text is inside:
            return inside
        inside = text
