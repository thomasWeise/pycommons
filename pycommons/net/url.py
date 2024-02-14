"""Come string splitting and processing routines."""

from re import Match, search
from re import compile as _compile
from typing import (
    Any,
    Final,
    Pattern,
    cast,
)
from urllib.parse import ParseResult, urljoin, urlparse

from pycommons.strings.chars import WHITESPACE_OR_NEWLINE
from pycommons.types import check_int_range

#: text that is forbidden in a URL
__URL_FORBIDDEN_1: Final[Pattern] = _compile(
    f"@.*@|[{WHITESPACE_OR_NEWLINE}"
    r"\\%*?&+\"'=$§!,;|<>\[\](){}²³°^]+|://.*://")
#: text that is forbidden in a URL
__URL_FORBIDDEN_2: Final[Pattern] = _compile(
    __URL_FORBIDDEN_1.pattern + r"|\.\.|\/\.+\/|\A\.+\Z")


def __check_url_part(part: Any, forbidden: Pattern) -> str:
    """
    Check an url part.

    :param part: the part
    :param forbidden: the pattern of forbidden text
    :return: the url as str

    >>> try:
    ...     __check_url_part("", __URL_FORBIDDEN_1)
    ... except ValueError as ve:
    ...     print(ve)
    Url part '' has invalid length 0.

    >>> try:
    ...     __check_url_part(" ", __URL_FORBIDDEN_1)
    ... except ValueError as ve:
    ...     print(ve)
    Url part ' ' contains the forbidden text ' '.

    >>> try:
    ...     __check_url_part("Äquator", __URL_FORBIDDEN_1)
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'Äquator' contains non-ASCII characters.

    >>> try:
    ...     __check_url_part("2" * 260, __URL_FORBIDDEN_1)
    ... except ValueError as ve:
    ...     print(str(ve)[:60])
    Url part '22222222222222222222222222222222222222222222222222

    >>> try:
    ...     __check_url_part(None, __URL_FORBIDDEN_1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __check_url_part(2, __URL_FORBIDDEN_1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> isinstance(__check_url_part("123", __URL_FORBIDDEN_1), str)
    True
    """
    if not (0 < str.__len__(part) < 255):
        raise ValueError(f"Url part {part!r} has invalid length {len(part)}.")
    the_match: Final[Match | None] = search(forbidden, part)
    if the_match is not None:
        raise ValueError(f"Url part {part!r} contains the forbidden "
                         f"text {the_match.group()!r}.")
    url: Final[str] = cast(str, part)
    if not url.isascii():
        raise ValueError(f"URL part {url!r} contains non-ASCII characters.")
    return url


#: the mailto scheme
__MAILTO_1: Final[str] = "mailto"
#: the mailto prefix
__MAILTO_2: Final[str] = __MAILTO_1 + ":"
#: the mailto full prefix
__MAILTO_3: Final[str] = __MAILTO_2 + "//"
#: the ssh scheme
__SSH: Final[str] = "ssh"

#: the permitted URL schemes without '@'
__ALLOWED_SCHEMES: Final[set] = {"http", "https", __MAILTO_1, __SSH}

#: the schemes that require usernames
__REQUIRE_USER_NAME_SCHEMES: Final[set] = {__MAILTO_1, __SSH}


def normalize_url(value: Any, base_url: str | None = None) -> str:
    r"""
    Parse a URL and throw errors if any shenanigans occur.

    This is a very strict URL parsing routine. The idea is that it will only
    produce URLs that are safe for use in almost any environment and throw
    exceptions otherwise.

    We limit the URLs to very few different types and allowed schemes.
    Non-ASCII characters are not allowed, and neither are spaces, `'%'`,
    `'*'`, `'?'`, `'+'`, `'&'`, `'<'`, `'>'`, `','`, `'$'`, `'§'`, `"'"`,
    `'"'`, `'['`, `']'`, `'{'`, `'}'`, `'('`, `')'`, ` nor `'\'` and a few
    more.

    We also allow `'@'` to occur at most once. This means that URLs cannot
    have any parameters and also that URL-escaping non-ASCII characters is not
    possible either. We thus limit the URLs to mainly static content pointers.

    We also only permit simple schemes such as `http`, `https`, `mailto`, and
    `ssh`.

    The final URL also cannot contain any `'/./'` or `'/../'` or consist of
    any component that equals `'..'`. No URL or component must be longer than
    255 characters either. It is also not allowed that `'://'` occurs twice.
    If the URL is a `mailto` or `ssh` URL, it must provide a username
    component.

    If a port is provided, it must be greater than 0 and less than 65536.
    If a port is specified, a host must be specified as well.
    Only if a netloc is found, then a port or a host may be specified.

    The URL `value` may be a relative URL that is turned into an absolute URL
    using the base URL `base_url`. Of course, then the same restrictions apply
    to the relative original URL, the base URL, and the final absolute URL.

    :param value: the string to be parsed into a URL.
    :param base_url: the current base URL.
    :return: a tuple with the canonicalzed url, the protocol, the server, and
        the server-local path

    >>> normalize_url("mailto:tweise@hfuu.edu.cn")
    'mailto://tweise@hfuu.edu.cn'
    >>> normalize_url("mailto://tweise@hfuu.edu.cn")
    'mailto://tweise@hfuu.edu.cn'
    >>> normalize_url("https://1.2.com/abc")
    'https://1.2.com/abc'
    >>> normalize_url("ssh://git@1.2.com/abc")
    'ssh://git@1.2.com/abc'
    >>> normalize_url("1.txt", "http://github.com/thomasWeise")
    'http://github.com/1.txt'
    >>> normalize_url("1.txt", "http://github.com/thomasWeise/")
    'http://github.com/thomasWeise/1.txt'
    >>> normalize_url("../1.txt", "http://github.com/thomasWeise/")
    'http://github.com/1.txt'
    >>> normalize_url("https://example.com/1.txt",
    ...               "http://github.com/thomasWeise/")
    'https://example.com/1.txt'
    >>> normalize_url("http://git.com:123/1")
    'http://git.com:123/1'

    >>> try:
    ...     normalize_url("https://1.2.com/abc(/23")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1.2.com/abc(/23' contains the forbidden text '('.

    >>> try:
    ...     normalize_url("https://1.2.com/abc]/23")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1.2.com/abc]/23' contains the forbidden text ']'.

    >>> try:
    ...     normalize_url("https://1.2.com/abcä/23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://1.2.com/abcä/23' contains non-ASCII characters.

    >>> try:
    ...     normalize_url("https://1.2.com/abc/./23")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1.2.com/abc/./23' contains the forbidden text '/./'.

    >>> try:
    ...     normalize_url("https://1.2.com/abc/../1.txt")
    ... except ValueError as ve:
    ...     print(str(ve)[:-1])
    Url part 'https://1.2.com/abc/../1.txt' contains the forbidden text '/../'

    >>> try:
    ...     normalize_url(r"https://1.2.com/abc\./23")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1.2.com/abc\\./23' contains the forbidden text '\\'.

    >>> try:
    ...     normalize_url("https://1.2.com/abc/23/../r")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1.2.com/abc/23/../r' contains the forbidden text '/../'.

    >>> try:
    ...     normalize_url("https://1 2.com")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'https://1 2.com' contains the forbidden text ' '.

    >>> try:
    ...     normalize_url("ftp://12.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:59])
    Invalid scheme 'ftp' of url 'ftp://12.com' under base None,

    >>> try:
    ...     normalize_url("http://12.com%32")
    ... except ValueError as ve:
    ...     print(str(ve))
    Url part 'http://12.com%32' contains the forbidden text '%'.

    >>> try:
    ...     normalize_url("mailto://gmx.net")
    ... except ValueError as ve:
    ...     print(str(ve)[:66])
    'mailto' url 'mailto://gmx.net' must contain '@' and have username

    >>> try:
    ...     normalize_url("ssh://gmx.net")
    ... except ValueError as ve:
    ...     print(str(ve)[:65])
    'ssh' url 'ssh://gmx.net' must contain '@' and have username, but

    >>> try:
    ...     normalize_url("ftp://12.com*32")
    ... except ValueError as ve:
    ...     print(str(ve))
    Url part 'ftp://12.com*32' contains the forbidden text '*'.

    >>> try:
    ...     normalize_url("http://12.com/https://h")
    ... except ValueError as ve:
    ...     print(str(ve)[:74])
    Url part 'http://12.com/https://h' contains the forbidden text '://12.com/

    >>> try:
    ...     normalize_url("http://user@12.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:66])
    'http' url 'http://user@12.com' must not contain '@' and have user

    >>> try:
    ...     normalize_url("http://" + ("a" * 250))
    ... except ValueError as ve:
    ...     print(str(ve)[-30:])
    aaaaa' has invalid length 257.

    >>> try:
    ...     normalize_url("http://.")
    ... except ValueError as ve:
    ...     print(ve)
    Url part '.' contains the forbidden text '.'.

    >>> try:
    ...     normalize_url("http://..")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http://..' contains the forbidden text '..'.

    >>> try:
    ...     normalize_url("http://www.github.com/../1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http://www.github.com/../1' contains the forbidden text '/../'.

    >>> try:
    ...     normalize_url("http://www.github.com/./1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http://www.github.com/./1' contains the forbidden text '/./'.

    >>> try:
    ...     normalize_url("http://user@git.com/@1")
    ... except ValueError as ve:
    ...     print(str(ve)[:-1])
    Url part 'http://user@git.com/@1' contains the forbidden text '@git.com/@'

    >>> try:
    ...     normalize_url("http://:45/1.txt")
    ... except ValueError as ve:
    ...     print(ve)
    Found port but no host in 'http://:45/1.txt'?

    >>> try:
    ...     normalize_url("http://git.com:-3/@1")
    ... except ValueError as ve:
    ...     print(ve)
    Port could not be cast to integer value as '-3'

    >>> try:
    ...     normalize_url("http://git.com:0/@1")
    ... except ValueError as ve:
    ...     print(ve)
    port=0 is invalid, must be in 1..65535.

    >>> try:
    ...     normalize_url("http://git.com:65536/@1")
    ... except ValueError as ve:
    ...     print(ve)
    Port out of range 0-65535

    >>> try:
    ...     normalize_url(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     normalize_url(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     normalize_url("http::/1.txt", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     normalize_url("http::/1.txt?x=1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http::/1.txt?x=1' contains the forbidden text '?'.

    >>> try:
    ...     normalize_url("http::/1.txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http::/1.txt&x=1' contains the forbidden text '&'.

    >>> try:
    ...     normalize_url("http::/1.+txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http::/1.+txt&x=1' contains the forbidden text '+'.

    >>> try:
    ...     normalize_url("http::/1*.+txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    Url part 'http::/1*.+txt&x=1' contains the forbidden text '*'.
    """
    url: str = __check_url_part(
        value, __URL_FORBIDDEN_2 if base_url is None else __URL_FORBIDDEN_1)
    if base_url is not None:
        url = __check_url_part(urljoin(__check_url_part(
            base_url, __URL_FORBIDDEN_2), url), __URL_FORBIDDEN_2)

    # normalize mailto URLs that do not contain //
    is_mailto: Final[bool] = url.startswith(__MAILTO_2)
    if is_mailto and (not url.startswith(__MAILTO_3)):
        url = __MAILTO_3 + url[len(__MAILTO_2):]

    res: Final[ParseResult] = urlparse(url)
    scheme: Final[str] = __check_url_part(res.scheme, __URL_FORBIDDEN_2)
    if scheme not in __ALLOWED_SCHEMES:
        raise ValueError(
            f"Invalid scheme {scheme!r} of url {url!r} under base "
            f"{base_url!r}, only {__ALLOWED_SCHEMES!r} are "
            "permitted.")

    netloc: Final[str] = __check_url_part(res.netloc, __URL_FORBIDDEN_2)

    host: Final[str | None] = res.hostname
    port: Final[int | None] = res.port
    if str.__len__(netloc) > 0:
        if port is not None:
            if host is None:
                raise ValueError(f"Found port but no host in {url!r}?")
            check_int_range(port, "port", 1, 65535)
    elif (port is not None) or (host is not None):
        raise ValueError(  # this should be impossible
            f"No netloc but host={host!r} and port={port!r} in {url!r}?")

    path: Final[str] = res.path
    if str.__len__(path) > 0:
        __check_url_part(path, __URL_FORBIDDEN_2)

    if is_mailto != (scheme == __MAILTO_1):  # this should be impossible
        raise ValueError(f"url {url!r} has scheme {scheme!r}?")
    requires_at: Final[bool] = is_mailto or (
        scheme in __REQUIRE_USER_NAME_SCHEMES)
    has_at: Final[bool] = "@" in netloc
    has_user: Final[bool] = (res.username is not None) and (
        str.__len__(res.username) > 0)
    if requires_at != (has_at and has_user):
        raise ValueError(
            f"{scheme!r} url {url!r} must {'' if requires_at else 'not '}"
            f"contain '@' and have username, but got "
            f"{'@' if has_at else 'no @'} and "
            f"{repr(res.username) if has_user else 'no username'}.")

    if (str.__len__(res.query) != 0) or (str.__len__(res.params) != 0):
        # this should be impossible, as our regex check already picks this up
        raise ValueError(f"Query/parameters found in url {url!r}.")

    return __check_url_part(res.geturl(), __URL_FORBIDDEN_2)
