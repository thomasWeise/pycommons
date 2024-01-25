"""Come string splitting and processing routines."""

from re import Match, search
from re import compile as _compile
from typing import (
    Any,
    Final,
    Pattern,
    cast,
)
from urllib.parse import urlparse

from pycommons.strings.tools import REGEX_WHITESPACE_OR_NEWLINE
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
    No white space allowed in string, but got ' 1 1 ' which contains ' '.
    >>> try:
    ...     enforce_non_empty_str_without_ws("a\tb")
    ... except ValueError as ve:
    ...     print(ve)
    No white space allowed in string, but got 'a\tb' which contains '\t'.
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
    the_match: Match | None = search(REGEX_WHITESPACE_OR_NEWLINE, value)
    if the_match is not None:
        raise ValueError(
            f"No white space allowed in string, but got {value!r} which "
            f"contains {the_match.group()!r}.")
    return value


#: text that is forbidden in a URL
__URL_FORBIDDEN: Final[Pattern] = _compile(
    REGEX_WHITESPACE_OR_NEWLINE.pattern[:-1]
    + r"|@.*@|://.*://|\.\.|/\./|[\\%*])")


def __check_url_part(part: Any) -> str:
    """
    Check an url part.

    :param part: the part
    :return: the url as str
    """
    if not (0 < str.__len__(part) < 255):
        raise ValueError(f"Url part {part!r} has invalid length {len(part)}.")
    if part in (".", ".."):
        raise ValueError(f"Url part {part!r} is invalid.")
    the_match: Final[Match | None] = search(__URL_FORBIDDEN, part)
    if the_match is not None:
        raise ValueError(f"Url {part!r} contains the forbidden "
                         f"part {the_match.group()!r}.")
    url: Final[str] = cast(str, part)
    if not url.isascii():
        raise ValueError(f"{url!r} contains non-ASCII characters.")
    return url


def enforce_simple_url(value: Any) -> str:
    r"""
    Enforce that a string is a valid url without any shenanigans.

    This function is a very crude method used to ensure that a string is
    a very simple and valid URL as it may occur in a GitHub page. We do not
    permit white spaces, '*'s, `%`s, backslashes, `.` directories, or `..`
    elements in the URL. '://' is only allowed to occur once.

    Also, only `http`, `https`, and `ssh` are permitted as schema.
    '@' is only permitted in urls starting with 'ssh://' and must only occur
    at most once. URLs must be less than 255 characters long.

    As a result of these tight limitations, the URLs which pass this method
    should be relatively safe.

    :param value: the url string (any type)
    :return: the url string, but definitely as string

    >>> enforce_simple_url("https://1.2.com/abc")
    'https://1.2.com/abc'
    >>> try:
    ...     enforce_simple_url("https://1.2.com/abcä/23")
    ... except ValueError as ve:
    ...     print(ve)
    'https://1.2.com/abcä/23' contains non-ASCII characters.
    >>> try:
    ...     enforce_simple_url("https://1.2.com/abc/./23")
    ... except ValueError as ve:
    ...     print(ve)
    Url 'https://1.2.com/abc/./23' contains the forbidden part '/./'.
    >>> try:
    ...     enforce_simple_url(r"https://1.2.com/abc\./23")
    ... except ValueError as ve:
    ...     print(ve)
    Url 'https://1.2.com/abc\\./23' contains the forbidden part '\\'.
    >>> try:
    ...     enforce_simple_url("https://1.2.com/abc/23/../r")
    ... except ValueError as ve:
    ...     print(ve)
    Url 'https://1.2.com/abc/23/../r' contains the forbidden part '..'.
    >>> try:
    ...     enforce_simple_url("https://1 2.com")
    ... except ValueError as ve:
    ...     print(ve)
    Url 'https://1 2.com' contains the forbidden part ' '.
    >>> try:
    ...     enforce_simple_url("ftp://12.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:73])
    Invalid scheme 'ftp' in url 'ftp://12.com', only ssh, http, and https are
    >>> try:
    ...     enforce_simple_url("ftp://12.com%32")
    ... except ValueError as ve:
    ...     print(str(ve))
    Url 'ftp://12.com%32' contains the forbidden part '%'.
    >>> try:
    ...     enforce_simple_url("ftp://12.com*32")
    ... except ValueError as ve:
    ...     print(str(ve))
    Url 'ftp://12.com*32' contains the forbidden part '*'.
    >>> try:
    ...     enforce_simple_url("http://12.com/https://h")
    ... except ValueError as ve:
    ...     print(str(ve)[:74])
    Url 'http://12.com/https://h' contains the forbidden part '://12.com/https
    >>> try:
    ...     enforce_simple_url("http://user@12.com")
    ... except ValueError as ve:
    ...     print(ve)
    Non-ssh URL must not contain '@', but 'http://user@12.com' does.
    >>> try:
    ...     enforce_simple_url("http://" + ("a" * 250))
    ... except ValueError as ve:
    ...     print(str(ve)[-30:])
    aaaaa' has invalid length 257.
    >>> try:
    ...     enforce_simple_url("http://.")
    ... except ValueError as ve:
    ...     print(ve)
    Url part '.' is invalid.
    >>> try:
    ...     enforce_simple_url("http://user@git.com/@1")
    ... except ValueError as ve:
    ...     print(ve)
    Url 'http://user@git.com/@1' contains the forbidden part '@git.com/@'.
    """
    url = __check_url_part(value)
    res = urlparse(url)
    if res.scheme != "ssh":
        if res.scheme not in ("http", "https"):
            raise ValueError(f"Invalid scheme {res.scheme!r} in url {url!r}, "
                             "only ssh, http, and https are permitted.")
        if "@" in url:
            raise ValueError(
                f"Non-ssh URL must not contain '@', but {url!r} does.")
    __check_url_part(res.netloc)
    __check_url_part(res.path)
    return __check_url_part(res.geturl())
