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

# noinspection PyPackageRequirements
from pycommons.strings.chars import WHITESPACE_OR_NEWLINE
from pycommons.types import check_int_range

#: text that is forbidden in a URL
_FORBIDDEN_IN_RELATIVE_URL: Final[Pattern] = _compile(
    f"@.*@|[{WHITESPACE_OR_NEWLINE}"
    r"\\%*?&+\"'=$§!,;|<>\[\](){}²³°^]+|://.*://")

#: text that is forbidden in a fully-expanded URL
_FORBIDDEN_IN_FULL_URL: Final[Pattern] = _compile(
    _FORBIDDEN_IN_RELATIVE_URL.pattern + r"|\.\.|\/\.+\/|\A\.+\Z")

#: text that is forbidden in a fragment
_FORBIDDEN_IN_FRAGMENT: Final[Pattern] = _compile(
    _FORBIDDEN_IN_FULL_URL.pattern + r"|#")


def _check_url_part(part: Any, forbidden: Pattern) -> str:
    """
    Check an url part.

    :param part: the part
    :param forbidden: the pattern of forbidden text
    :return: the url as str

    >>> try:
    ...     _check_url_part("", _FORBIDDEN_IN_RELATIVE_URL)
    ... except ValueError as ve:
    ...     print(ve)
    URL part '' has invalid length 0.

    >>> try:
    ...     _check_url_part(" ", _FORBIDDEN_IN_RELATIVE_URL)
    ... except ValueError as ve:
    ...     print(ve)
    URL part ' ' contains the forbidden text ' '.

    >>> try:
    ...     _check_url_part("Äquator", _FORBIDDEN_IN_RELATIVE_URL)
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'Äquator' contains non-ASCII characters.

    >>> try:
    ...     _check_url_part("2" * 260, _FORBIDDEN_IN_RELATIVE_URL)
    ... except ValueError as ve:
    ...     print(str(ve)[:60])
    URL part '22222222222222222222222222222222222222222222222222

    >>> try:
    ...     _check_url_part(None, _FORBIDDEN_IN_RELATIVE_URL)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     _check_url_part(2, _FORBIDDEN_IN_RELATIVE_URL)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> isinstance(_check_url_part("123", _FORBIDDEN_IN_RELATIVE_URL), str)
    True
    """
    if not (0 < str.__len__(part) < 255):
        raise ValueError(f"URL part {part!r} has invalid length {len(part)}.")
    the_match: Final[Match | None] = search(forbidden, part)
    if the_match is not None:
        raise ValueError(f"URL part {part!r} contains the forbidden "
                         f"text {the_match.group()!r}.")
    urlstr: Final[str] = cast(str, part)
    if not urlstr.isascii():
        raise ValueError(
            f"URL part {urlstr!r} contains non-ASCII characters.")
    if urlstr.endswith(("#", "@")):
        raise ValueError(
            f"URL part must not end in {urlstr[-1]!r}, but {urlstr!r} does.")
    return urlstr


#: the mailto scheme
_MAILTO_1: Final[str] = "mailto"
#: the mailto prefix
_MAILTO_2: Final[str] = _MAILTO_1 + ":"
#: the mailto full prefix
_MAILTO_3: Final[str] = _MAILTO_2 + "//"
#: the ssh scheme
_SSH: Final[str] = "ssh"

#: the schemes that require usernames
_REQUIRE_USER_NAME_SCHEMES: Final[set] = {_MAILTO_1, _SSH}

#: the permitted URL schemes without '@'
_ALLOWED_SCHEMES: Final[set] = {"http", "https"}.union(
    _REQUIRE_USER_NAME_SCHEMES)


class URL(str):
    r"""
    A normalized and expanded URL.

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

    This function tries to detect email addresses and turns them into valid
    `mailto://` urls.
    This function gobbles up single trailing `/` characters.

    An instance of `URL` is also an instance of :class:`str`, so you can use
    it as string whereever you want. It additionally offers the following
    attributes:

    - :attr:`~URL.scheme`: the URL scheme, e.g., `"http"`
    - :attr:`~URL.netloc`: the URL network location, including user (if any),
        host, and port (if any)
    - :attr:`~URL.host`: the host of the URL
    - :attr:`~URL.port`: the port of the URL, or `None` if no port is
        specified
    - :attr:`~URL.path`: the path part of the URL (without the
        :attr:`~URL.fragment` part, if any), or `None` if no path part is
        specified
    - :attr:`~URL.fragment`: the fragment part of the path, or `None` if the
        path has no fragment


    >>> u1 = URL("mailto:tweise@hfuu.edu.cn")
    >>> print(u1)
    mailto://tweise@hfuu.edu.cn
    >>> print(u1.scheme)
    mailto
    >>> print(u1.netloc)
    tweise@hfuu.edu.cn
    >>> print(u1.host)
    hfuu.edu.cn
    >>> print(u1.port)
    None
    >>> print(u1.path)
    None
    >>> print(u1.fragment)
    None

    >>> u = URL("tweise@hfuu.edu.cn")
    >>> print(u)
    mailto://tweise@hfuu.edu.cn
    >>> print(u.scheme)
    mailto
    >>> print(u.netloc)
    tweise@hfuu.edu.cn
    >>> print(u.host)
    hfuu.edu.cn
    >>> print(u.port)
    None
    >>> print(u.path)
    None
    >>> print(u.fragment)
    None

    >>> URL("mailto://tweise@hfuu.edu.cn")
    'mailto://tweise@hfuu.edu.cn'

    >>> u2 = URL("https://example.com/abc")
    >>> print(u2)
    https://example.com/abc
    >>> print(u2.scheme)
    https
    >>> print(u2.netloc)
    example.com
    >>> print(u2.host)
    example.com
    >>> print(u2.port)
    None
    >>> print(u2.path)
    /abc
    >>> print(u2.fragment)
    None
    >>> u1.host != u2.host
    True

    >>> u = URL("https://example.com/abc/")
    >>> print(u)
    https://example.com/abc
    >>> print(u.scheme)
    https
    >>> print(u.netloc)
    example.com
    >>> print(u.host)
    example.com
    >>> print(u.port)
    None
    >>> print(u.path)
    /abc
    >>> print(u.fragment)
    None

    >>> u = URL("https://example.com/")
    >>> print(u)
    https://example.com
    >>> print(u.scheme)
    https
    >>> print(u.netloc)
    example.com
    >>> print(u.host)
    example.com
    >>> print(u.port)
    None
    >>> print(u.path)
    None
    >>> print(u.fragment)
    None

    >>> u = URL("ssh://git@example.com/abc")
    >>> print(u)
    ssh://git@example.com/abc
    >>> print(u.scheme)
    ssh
    >>> print(u.netloc)
    git@example.com
    >>> print(u.host)
    example.com
    >>> print(u.port)
    None
    >>> print(u.path)
    /abc
    >>> print(u.fragment)
    None

    >>> URL("1.txt", "http://example.com/thomasWeise")
    'http://example.com/1.txt'

    >>> URL("1.txt", "http://example.com/thomasWeise/")
    'http://example.com/thomasWeise/1.txt'

    >>> URL("../1.txt", "http://example.com/thomasWeise/")
    'http://example.com/1.txt'

    >>> URL("https://example.com/1.txt",
    ...     "http://github.com/thomasWeise/")
    'https://example.com/1.txt'

    >>> URL("http://example.com:123/1")
    'http://example.com:123/1'

    >>> u = URL("http://example.com:34/index.html#1")
    >>> print(u)
    http://example.com:34/index.html#1
    >>> print(u.scheme)
    http
    >>> print(u.netloc)
    example.com:34
    >>> print(u.host)
    example.com
    >>> print(u.port)
    34
    >>> print(u.path)
    /index.html
    >>> print(u.fragment)
    1

    >>> try:
    ...     URL("tweise@@hfuu.edu.cn")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'tweise@@hfuu.edu.cn' contains the forbidden text '@@'.

    >>> try:
    ...     URL("http://example.com/index.html#")
    ... except ValueError as ve:
    ...     print(ve)
    URL part must not end in '#', but 'http://example.com/index.html#' does.

    >>> try:
    ...     URL("http://example.com/index.html@")
    ... except ValueError as ve:
    ...     print(ve)
    URL part must not end in '@', but 'http://example.com/index.html@' does.

    >>> try:
    ...     URL("https://example.com/abc(/23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://example.com/abc(/23' contains the forbidden text '('.

    >>> try:
    ...     URL("https://example.com/abc]/23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://example.com/abc]/23' contains the forbidden text ']'.

    >>> try:
    ...     URL("https://example.com/abcä/23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://example.com/abcä/23' contains non-ASCII characters.

    >>> try:
    ...     URL("https://example.com/abc/./23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://example.com/abc/./23' contains the forbidden text '/./'.

    >>> try:
    ...     URL("https://example.com/abc/../1.txt")
    ... except ValueError as ve:
    ...     print(str(ve)[:-4])
    URL part 'https://example.com/abc/../1.txt' contains the forbidden text '/.

    >>> try:
    ...     URL(r"https://example.com/abc\./23")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://example.com/abc\\./23' contains the forbidden text '\\'.

    >>> try:
    ...     URL("https://1.2.com/abc/23/../r")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://1.2.com/abc/23/../r' contains the forbidden text '/../'.

    >>> try:
    ...     URL("https://exa mple.com")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'https://exa mple.com' contains the forbidden text ' '.

    >>> try:
    ...     URL("ftp://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:66])
    Invalid scheme 'ftp' of url 'ftp://example.com' under base None, o

    >>> try:
    ...     URL("http://example.com%32")
    ... except ValueError as ve:
    ...     print(str(ve))
    URL part 'http://example.com%32' contains the forbidden text '%'.

    >>> try:
    ...     URL("mailto://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:66])
    'mailto' url 'mailto://example.com' must contain '@' and have user

    >>> try:
    ...     URL("ssh://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:65])
    'ssh' url 'ssh://example.com' must contain '@' and have username,

    >>> try:
    ...     URL("ftp://example.com*32")
    ... except ValueError as ve:
    ...     print(str(ve))
    URL part 'ftp://example.com*32' contains the forbidden text '*'.

    >>> try:
    ...     URL("http://example.com/https://h")
    ... except ValueError as ve:
    ...     print(str(ve)[:74])
    URL part 'http://example.com/https://h' contains the forbidden text '://ex

    >>> try:
    ...     URL("http://user@example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:66])
    'http' url 'http://user@example.com' must not contain '@' and have

    >>> try:
    ...     URL("http://" + ("a" * 250))
    ... except ValueError as ve:
    ...     print(str(ve)[-30:])
    aaaaa' has invalid length 257.

    >>> try:
    ...     URL("http://.")
    ... except ValueError as ve:
    ...     print(ve)
    URL part '.' contains the forbidden text '.'.

    >>> try:
    ...     URL("http://..")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http://..' contains the forbidden text '..'.

    >>> try:
    ...     URL("http://www.example.com/../1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http://www.example.com/../1' contains the forbidden text '/../'.

    >>> try:
    ...     URL("http://www.example.com/./1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http://www.example.com/./1' contains the forbidden text '/./'.

    >>> try:
    ...     URL("http://user@example.com/@1")
    ... except ValueError as ve:
    ...     print(str(ve)[:-9])
    URL part 'http://user@example.com/@1' contains the forbidden text '@exampl

    >>> try:
    ...     URL("http://:45/1.txt")
    ... except ValueError as ve:
    ...     print(ve)
    URL 'http://:45/1.txt' has no host?

    >>> try:
    ...     URL("http://example.com:-3/@1")
    ... except ValueError as ve:
    ...     print(ve)
    Port could not be cast to integer value as '-3'

    >>> try:
    ...     URL("http://example.com:0/@1")
    ... except ValueError as ve:
    ...     print(ve)
    port=0 is invalid, must be in 1..65535.

    >>> try:
    ...     URL("http://example.com:65536/@1")
    ... except ValueError as ve:
    ...     print(ve)
    Port out of range 0-65535

    >>> try:
    ...     URL(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     URL(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     URL("http::/1.txt", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     URL("http::/1.txt?x=1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http::/1.txt?x=1' contains the forbidden text '?'.

    >>> try:
    ...     URL("http::/1.txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http::/1.txt&x=1' contains the forbidden text '&'.

    >>> try:
    ...     URL("http::/1.+txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http::/1.+txt&x=1' contains the forbidden text '+'.

    >>> try:
    ...     URL("http::/1*.+txt&x=1")
    ... except ValueError as ve:
    ...     print(ve)
    URL part 'http::/1*.+txt&x=1' contains the forbidden text '*'.

    >>> try:
    ...     URL("http://example.com#1#2")
    ... except ValueError as ve:
    ...     print(ve)
    URL part '1#2' contains the forbidden text '#'.
    """

    #: the protocol scheme, e.g., `"https"`
    scheme: Final[str]  # type: ignore
    #: the network location, usually of the form `"user@host:port"`, i.e.,
    #: composed of user name (if present), host, and port (if present)
    netloc: Final[str]  # type: ignore
    #: the host str
    host: Final[str]  # type: ignore
    #: the port, if any (else `None`)
    port: Final[int | None]  # type: ignore
    #: the path, if any (else `None`), but without the fragment component
    path: Final[str | None]  # type: ignore
    #: the path fragment, i.e., the part following a `"#"`, if any (else
    #: `None`)
    fragment: Final[str | None]  # type: ignore

    def __new__(cls, value: Any, base_url: Any | None = None):
        """
        Create the URL.

        :param value: either the full absolute URL or a URL that should be
            resolved against the URL `base_url`
        :param base_url: the base URL to resolve `value` against, or `None` if
            `value` is already an absolute URL
        """
        if isinstance(value, URL):
            return cast(URL, value)

        url: str = _check_url_part(
            value, _FORBIDDEN_IN_FULL_URL if base_url is None
            else _FORBIDDEN_IN_RELATIVE_URL)
        if base_url is not None:
            url = _check_url_part(urljoin(_check_url_part(
                base_url, _FORBIDDEN_IN_FULL_URL), url),
                _FORBIDDEN_IN_FULL_URL)

        if url.endswith("/"):  # strip trailing '/'
            url = url[:-1]

        # normalize mailto URLs that do not contain //
        is_mailto: bool = url.startswith(_MAILTO_2)
        if is_mailto and (not url.startswith(_MAILTO_3)):
            url = _MAILTO_3 + url[str.__len__(_MAILTO_2):]

        res: ParseResult = urlparse(url)
        scheme: str | None = res.scheme
        if ((scheme is None) or (str.__len__(scheme) == 0)) and (
                url.count("@") == 1):
            res = urlparse(_MAILTO_3 + url)
            scheme = res.scheme
            is_mailto = True
        scheme = _check_url_part(scheme, _FORBIDDEN_IN_FULL_URL)

        if scheme not in _ALLOWED_SCHEMES:
            raise ValueError(
                f"Invalid scheme {scheme!r} of url {url!r} under base "
                f"{base_url!r}, only {_ALLOWED_SCHEMES!r} are "
                "permitted.")

        netloc: Final[str] = _check_url_part(
            res.netloc, _FORBIDDEN_IN_FULL_URL)

        host: Final[str] = res.hostname
        if host is None:
            raise ValueError(f"URL {url!r} has no host?")
        _check_url_part(host, _FORBIDDEN_IN_FULL_URL)
        port: Final[int | None] = res.port
        if port is not None:
            check_int_range(port, "port", 1, 65535)

        path: str | None = res.path
        if str.__len__(path) > 0:
            _check_url_part(path, _FORBIDDEN_IN_FULL_URL)
        else:
            path = None

        if is_mailto != (scheme == _MAILTO_1):  # this should be impossible
            raise ValueError(f"url {url!r} has scheme {scheme!r}?")
        requires_at: Final[bool] = is_mailto or (
            scheme in _REQUIRE_USER_NAME_SCHEMES)
        has_at: Final[bool] = "@" in netloc
        has_user: Final[bool] = (res.username is not None) and (
            str.__len__(res.username) > 0)
        if requires_at != (has_at and has_user):
            raise ValueError(
                f"{scheme!r} url {url!r} must {'' if requires_at else 'not '}"
                f"contain '@' and have username, but got "
                f"{'@' if has_at else 'no @'} and "
                f"{repr(res.username) if has_user else 'no username'}.")

        if ((str.__len__(res.query) != 0) or (str.__len__(res.params) != 0)
                or (res.password is not None)):
            # should be impossible, as our regex check already picks this up
            raise ValueError(
                f"Query/parameters/password found in url {url!r}.")

        fragment: str | None = res.fragment
        if str.__len__(fragment) <= 0:
            fragment = None
        else:
            _check_url_part(fragment, _FORBIDDEN_IN_FRAGMENT)

        result = super().__new__(cls, _check_url_part(
            res.geturl(), _FORBIDDEN_IN_FULL_URL))

        #: the protocol scheme
        result.scheme: Final[str] = scheme  # type: ignore
        #: the network location: user@host:port
        result.netloc: Final[str] = netloc  # type: ignore
        #: the host
        result.host: Final[str] = host  # type: ignore
        #: the port, if any (else `None`)
        result.port: Final[int | None] = port  # type: ignore
        #: the path, if any (else `None`)
        result.path: Final[str | None] = path  # type: ignore
        #: the path fragment, if any (else `None`)
        result.fragment: Final[str | None] = fragment  # type: ignore
        return result
