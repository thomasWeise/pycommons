"""Test all the links in."""
from os import environ
from random import randint
from time import sleep
from typing import Final, cast

# noinspection PyPackageRequirements
from certifi import where

# noinspection PyPackageRequirements
from urllib3 import PoolManager  # type: ignore

# noinspection PyPackageRequirements
from urllib3.response import HTTPResponse  # type: ignore

from pycommons.io.console import logger
from pycommons.io.path import UTF8, Path, file_path
from pycommons.net.url import URL
from pycommons.strings.tools import replace_str
from pycommons.types import check_int_range, type_error

#: The hosts that somtimes are unreachable from my local machine.
#: When the test is executed in a GitHub workflow, all hosts should be
#: reachable.
__SOMETIMES_UNREACHABLE_HOSTS: Final[set[str]] = \
    {"iao.hfuu.edu.cn"} if "GITHUB_JOB" in environ else \
    {"iao.hfuu.edu.cn", "img.shields.io", "pypi.org", "docs.python.org"}

#: URLs that we never need to check because they are OK
__CORRECT_URLS: Final[set[str]] = {
    "https://example.com", "http://example.com",
    "https://github.com", "http://github.com",
    "https://www.acm.org/publications/policies/artifact-review"
    "-and-badging-current"}


def __ve(msg: str, text: str, idx: int) -> ValueError:
    """
    Raise a value error for the given text piece.

    :param msg: the message
    :param text: the string
    :param idx: the index
    :returns: a :class:`ValueError` ready to be raised
    :raises TypeError: if either argument is of the wrong type

    >>> try:
    ...     __ve(None, " ", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __ve(1, " ", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __ve("bla", None, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __ve("bla", 1, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __ve("bla", "txt", None)
    ... except TypeError as te:
    ...     print(te)
    idx should be an instance of int but is None.

    >>> try:
    ...     __ve("bla", "txt", "x")
    ... except TypeError as te:
    ...     print(te)
    idx should be an instance of int but is str, namely 'x'.

    >>> print(repr(__ve("", "txt", 1)))
    ValueError('Empty message!')

    >>> print(repr(__ve("msg", "", 1)))
    ValueError("Empty text '' for message 'msg'.")

    >>> print(repr(__ve("msg", "txt", 5)))
    ValueError("Index 5 is outside of text of length 3 for message 'msg'.")

    >>> print(repr(__ve("msg", "long text", 2)))
    ValueError("msg: '...long text...'")
    """
    if str.__len__(msg) == 0:
        return ValueError("Empty message!")
    len_text: Final[int] = str.__len__(text)
    if len_text <= 0:
        return ValueError(f"Empty text {text!r} for message {msg!r}.")
    if not isinstance(idx, int):
        raise type_error(idx, "idx", int)
    if len_text <= idx:
        return ValueError(f"Index {idx} is outside of text of length"
                          f" {len_text} for message {msg!r}.")
    piece = text[max(0, idx - 32):min(len_text, idx + 64)].strip()
    return ValueError(f"{msg}: '...{piece}...'")


def __make_headers() -> tuple[None | dict[str, str], ...]:
    """
    Make the headers.

    :returns: the headers
    """
    headers: list[None | dict[str, str]] = [None]
    headers.extend(
        {"User-Agent": ua} for ua in (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:106.0) Gecko/20100101"
            " Firefox/106.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
            "Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0."
            "1518.55",
            "Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 "
            "Version/12.16.2",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) "
            "like Gecko",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/"
            "537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
            "Mozilla/5.0 (PLAYSTATION 3; 3.55)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ("
            "KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/114.0.1823"
            ".901",
            "mozilla/5.0 (windows nt 10.0; win64; x64) applewebkit/537.36 ("
            "khtml, like gecko) chrome/80.0.3987.87 safari/537.36 edg/80.0."
            "361.502",
            "Mozilla/5.0 (X11; Linux i686; rv:13.0) Gecko/13.0 Firefox/13.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
            "Gecko) Ubuntu Chromium/80.0.3987.149 HeadlessChrome/80.0.3987."
            "149 Safari/537.36"))
    return tuple(headers)


#: The headers to use for the HTTP requests.
#: It seems that some websites may throttle requests.
#: Maybe by using different headers, we can escape this.
__HEADERS: Final[tuple[None | dict[str, str], ...]] = __make_headers()
del __make_headers


def __needs_body(url: URL) -> bool:
    """
    Check whether we need the body of the given url.

    If the complete body of the document needs to be downloaded, this function
    returns `True`. This is the case, for example, if we are talking about
    html documents. In this case, we need to (later) scan for internal
    references, i.e., for stuff like `id="..."` attributes. However, if the
    url does not point to an HTML document, maybe a PDF, then we do not need
    the whole body and return `False`. In the latter case, it is sufficient to
    do a `HEAD` HTTP request, in the former case we need a full `GET`.

    :param url: the url string
    :returns: `True` if the body is needed, `False` otherwise
    :raises TypeError: if `base_url` is not a string

    >>> __needs_body(URL("http://www.github.com/"))
    True
    >>> __needs_body(URL("http://www.github.com"))
    True
    >>> __needs_body(URL("http://www.github.com/1.htm"))
    True
    >>> __needs_body(URL("http://www.github.com/1.html"))
    True
    >>> __needs_body(URL("http://www.github.com/1.jpg"))
    False
    >>> __needs_body(URL("http://www.github.com/1"))
    True

    >>> try:
    ...     __needs_body(None)
    ... except TypeError as te:
    ...     print(str(te)[:59])
    url should be an instance of pycommons.net.url.URL but is N

    >>> try:
    ...     __needs_body(1)
    ... except TypeError as te:
    ...     print(str(te)[:59])
    url should be an instance of pycommons.net.url.URL but is i
    """
    if not isinstance(url, URL):
        raise type_error(url, "url", URL)
    return (url.path is None) or str.endswith(
        url.path, (".html", ".htm", "/")) or ("." not in url.path)


def __find_fragment_html(body: str, fragment: str, url: URL) -> None:
    r"""
    Check whether the fragment is contained in the body as ID.

    :param body: the body that was loaded
    :param fragment: the fragment
    :param url: the url from which the body was loaded
    :raises TypeError: if `body`, `fragment`, or `url` are not all strings
    :raises ValueError: if `body` does not contain `fragment` as an ID
        somewhere

    >>> __find_fragment_html("<p id='1'>bla</p>", "1",
    ...                      URL("http://example.com#1"))
    >>> __find_fragment_html("<p id=\"1\">bla</p>", "1",
    ...                      URL("http://example.com#1"))
    >>> __find_fragment_html("<p id=1>bla</p>", "1",
    ...                      URL("http://example.com#1"))

    >>> try:
    ...     __find_fragment_html(None, "1", URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __find_fragment_html(1, "1", URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", None,
    ...                          URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", 1,
    ...                          URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", None,
    ...                          URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", 1,
    ...                          URL("http://example.com#1"))
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", "1", None)
    ... except TypeError as te:
    ...     print(te)
    url should be an instance of pycommons.net.url.URL but is None.

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", "1", 1)
    ... except TypeError as te:
    ...     print(te)
    url should be an instance of pycommons.net.url.URL but is int, namely '1'.

    >>> try:
    ...     __find_fragment_html("", "1",
    ...                          URL("http://example.com#1"))
    ... except ValueError as ve:
    ...     print(ve)
    Empty body: ''.

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", "",
    ...                          URL("http://example.com"))
    ... except ValueError as ve:
    ...     print(ve)
    Empty fragment: ''.

    >>> try:
    ...     __find_fragment_html("<p id='1'>bla</p>", "1",
    ...                          URL("http://example.com"))
    ... except ValueError as ve:
    ...     print(ve)
    Url 'http://example.com' does not end in fragment '1'.

    >>> try:
    ...     __find_fragment_html("<p id='x1'>bla</p>", "1",
    ...                          URL("http://example.com#1"))
    ... except ValueError as ve:
    ...     print(str(ve)[:-4])
    Did not find id='1' of 'http://example.com#1' in body "<p id='x1'>bla</
    """
    if str.__len__(body) <= 0:
        raise ValueError(f"Empty body: {body!r}.")
    if str.__len__(fragment) <= 0:
        raise ValueError(f"Empty fragment: {fragment!r}.")
    if not isinstance(url, URL):
        raise type_error(url, "url", URL)
    if not url.endswith(fragment):
        raise ValueError(
            f"Url {url!r} does not end in fragment {fragment!r}.")

    for qt in ("", "'", '"'):
        if f"id={qt}{fragment}{qt}" in body:
            return

    raise ValueError(
        f"Did not find id={fragment!r} of {url!r} in body {body!r}.")


def __check_url(urlstr: str, valid_urls: dict[str, str | None],
                http: PoolManager = PoolManager(
                    cert_reqs="CERT_REQUIRED", ca_certs=where())) -> None:
    r"""
    Check whether a URL is valid and can be reached.

    :param urlstr: the URL to be checked
    :param valid_urls: the set of valid urls
    :param http: the pool manager
    :raises TypeError: if any of the parameters is of the wrong type
    :raises ValueError: if the url `urlstr` cannot be loaded or if it has a
        fragment part that is not discovered in the body of the loaded
        document.

    >>> vu = dict()
    >>> __check_url("mailto:tweise@hfuu.edu.cn", vu)
    >>> __check_url("mailto:tweise@hfuu.edu.cn", vu)
    >>> __check_url("tweise@hfuu.edu.cn", vu)

    >>> from contextlib import redirect_stdout

    >>> with redirect_stdout(None):
    ...     __check_url("https://thomasweise.github.io/pycommons", vu)
    ...     __check_url("http://iao.hfuu.edu.cn", vu)
    ...     __check_url("http://example.com/", vu)
    ...     __check_url("https://thomasweise.github.io/pycommons/pycommons"
    ...                 ".io.html", vu)
    >>> __check_url("https://thomasweise.github.io/pycommons", vu)
    >>> __check_url(
    ...     "https://thomasweise.github.io/pycommons/pycommons.io.html", vu)

    >>> with redirect_stdout(None):
    ...     __check_url("http://iao.hfuu.edu.cn/", vu)
    >>> __check_url("https://thomasweise.github.io/pycommons/pycommons"
    ...             ".io.html#pycommons.io.path.Path", vu)
    >>> __check_url("http://example.com", vu)

    >>> try:
    ...     __check_url("bwri435//sdfsdf:-@@", vu)
    ... except ValueError as ve:
    ...     print(str(ve)[:50])
    Error in url 'bwri435//sdfsdf:-@@': URL part 'bwri

    >>> with redirect_stdout(None):
    ...     try:
    ...         __check_url(
    ...             "https://thomasweise.github.io/sifwrwruS.jpg#34", vu)
    ...     except ValueError as ve:
    ...         s = str(ve)
    >>> print(s[:61])
    Url 'https://thomasweise.github.io/sifwrwruS.jpg#34' does not

    >>> with redirect_stdout(None):
    ...     try:
    ...         __check_url("ssh://u@thomasweise.github.io/sifwrwruSSXFd", vu)
    ...     except ValueError as ve:
    ...         s = str(ve)
    >>> print(s)
    Invalid scheme for url 'ssh://u@thomasweise.github.io/sifwrwruSSXFd'.

    >>> with redirect_stdout(None):
    ...     try:
    ...         __check_url(
    ...             "https://thomasweise.github.io/sifwrwruSSXFdfDX", vu)
    ...     except ValueError as ve:
    ...         s = str(ve)
    >>> s.endswith("returns code 404.") or s.startswith("Could not load url")
    True

    >>> try:
    ...     __check_url(None, dict())
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     __check_url(1, dict())
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     __check_url("http://example.com", None)
    ... except TypeError as te:
    ...     print(te)
    valid_urls should be an instance of dict but is None.

    >>> try:
    ...     __check_url("http://example.com", 1)
    ... except TypeError as te:
    ...     print(te)
    valid_urls should be an instance of dict but is int, namely '1'.

    >>> try:
    ...     __check_url("http://example.com", dict(), None)
    ... except TypeError as te:
    ...     print(te)
    http should be an instance of urllib3.poolmanager.PoolManager but is None.

    >>> try:
    ...     __check_url("http://example.com", dict(), 1)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    http should be an instance of urllib3.poolmanager.
    """
    if not isinstance(valid_urls, dict):
        raise type_error(valid_urls, "valid_urls", dict)
    if not isinstance(http, PoolManager):
        raise type_error(http, "http", PoolManager)

    if urlstr in valid_urls:
        return

    try:
        url: Final[URL] = URL(urlstr)
    except ValueError as ve:
        raise ValueError(f"Error in url {urlstr!r}: {ve}") from None

    if (url in __CORRECT_URLS) or (url in valid_urls):
        return
    if url.scheme == "mailto":
        return
    if not url.scheme.startswith("http"):
        raise ValueError(f"Invalid scheme for url {url!r}.")

    needs_body: Final[bool] = __needs_body(url)

    base_url: URL = url
    fragment: Final[str | None] = url.fragment
    if fragment is not None:
        base_url = URL(url[:url.index("#")])
        if not needs_body:
            raise ValueError(
                f"Url {url!r} does not need body but has "
                f"fragment {url.fragment!r}?")
        if base_url in valid_urls:
            __find_fragment_html(valid_urls[base_url], fragment, url)
            return

    code: int
    body: str | None = None
    method = "GET" if needs_body else "HEAD"
    error: BaseException | None = None
    response: HTTPResponse | None = None
    headers: Final[list[dict[str, str] | None]] = list(__HEADERS)
    header_count: int = 0

# Sometimes, access to the URLs on GitHub fails.
# I think they probably throttle access from here.
# Therefore, we first do a request with 5s timeout and 0 retries.
# If that fails, we wait 2 seconds and try with timeout 8 and 3 retries.
# If that fails, we wait for 5s, then try with timeout 30 and 3 retries.
# If that fails too, we assume that the URL is really incorrect, which rarely
# should not be the case (justifying the many retries).
    for sleep_time, retries, timeout in (
            (0, 0, 5), (2, 3, 8), (5, 3, 30)):
        if sleep_time > 0:
            sleep(sleep_time)

# We try to get a random header to deal with the problem that some pages
# will not permit certain user agents. To handle this issue, we try to not
# use any user agent twice. We randomly pick a user agent and, if it fails,
# make sure to use all other user agents first before we use that one again.
        if header_count <= 0:
            header_count = len(headers)
        header_idx = randint(0, header_count - 1)  # noqa: S311
        header: dict[str, str] | None = headers[header_idx]
        header_count -= 1
        headers[header_count], headers[header_idx] \
            = header, headers[header_count]
        try:
            response = cast(HTTPResponse, http.request(
                method, base_url, timeout=timeout, redirect=True,
                retries=retries, headers=header))
            if isinstance(response, HTTPResponse) and isinstance(
                    response.status, int) and (response.status == 200):
                error = None
                break
        except BaseException as be:  # noqa: B036
            logger(f"Attempt sleep={sleep_time}, retries={retries}, "
                   f"timeout={timeout}, error={str(be)!r}, and "
                   f"header={header!r} for {base_url!r} gave {be}.")
            error = be

    if error is not None:
        # sometimes, I cannot reach some hosts from here...
        if url.host in __SOMETIMES_UNREACHABLE_HOSTS:
            return  # we will accept this here
        raise ValueError(f"Could not load url {url!r}.") from error

    if not isinstance(response, HTTPResponse):  # should be impossible...
        raise ValueError(f"Response {response} from url={url!r}?")  # noqa

    code = check_int_range(response.status, "response.status", 0, 10000)
    if needs_body:
        try:
            body = str.strip(response.data.decode(UTF8))
        except BaseException as be:    # noqa: B036
            raise ValueError(f"Error in body of url {url!r}: {be}") from be

    body_len: Final[int] = 0 if body is None else str.__len__(body)
    logger(f"Checked url {url!r} got code {code} for method {method!r} and "
           f"{body_len} chars.")
    if code != 200:
        raise ValueError(f"Url {url!r} returns code {code}.")

    if needs_body and ((body is None) or (body_len <= 0)):
        raise ValueError(
            f"Stripped body for {url!r} / {base_url!r} is {body!r}?")

    valid_urls[base_url] = body
    if url is not base_url:
        valid_urls[url] = body

    if fragment is not None:
        __find_fragment_html(body, fragment, url)


def check_links_in_md(file: str) -> None:
    """
    Test all the links in the given file.

    :param file: the file to check
    """
    # First, we load the file as a single string
    readme: Final[Path] = file_path(file)
    logger(f"Checking all links in the file {readme!r}.")

    text: str = readme.read_all_str()
    text_len: int = str.__len__(text)
    logger(f"Got {text_len} characters from file {readme!r}.")
    if text_len <= 0:
        raise ValueError(f"{readme!r} file is empty?")

    # remove all code blocks
    total_links_checked: int = 0
    start: int = -1
    lines: Final[list[str]] = []
    while True:
        start += 1
        i: int = text.find("\n```", start)
        if i < start:
            lines.append(text[start:].strip())
            break
        j: int = text.find("\n```", i + 1)
        if j < i:
            raise __ve("Multi-line code start without "
                       f"end in file {readme!r}", text, i)
        k: int = text.find("\n", j + 1)
        if k < j:
            raise __ve(f"Code end without newline in file {readme!r}",
                       text, i)
        lines.append(text[start:i].strip())
        start = k

    text = "\n".join(lines).strip()
    lines.clear()

    # these are all urls that have been verified
    valid_urls: Final[dict[str, str | None]] = {}

    # build the map of local reference marks
    start = -1
    while True:
        start += 1
        i = 0 if ((start == 0) and text.startswith("#")) \
            else text.find("\n#", start)
        if i < start:
            break
        j = text.find(" ", i + 1)
        if (j < i) or (text[j - 1] != "#"):
            raise __ve("Headline without space after # "
                       f"in file {readme!r}", text, i)
        k = text.find("\n", j + 1)
        if k < j:
            raise __ve(f"Headline without end in file {readme!r}", text, i)
        rid: str = text[j:k].strip().replace(" ", "-")
        for ch in ".:,()`/":
            rid = rid.replace(ch, "")
        rid = replace_str("--", "-", rid).lower()
        if (str.__len__(rid) <= 2) or ((rid[0] not in "123456789") and (
                start > 0)) or ("-" not in rid):
            raise __ve(f"Invalid id {rid!r} in file {readme!r}", text, i)
        valid_urls[f"#{rid}"] = None
        start = k

    # remove all inline code
    start = -1
    while True:
        start += 1
        i = text.find("`", start)
        if i < start:
            lines.append(text[start:].strip())
            break
        j = text.find("`", i + 1)
        if j < i:
            raise __ve("Multi-line code start "
                       f"without end in file {readme!r}", text, i)
        lines.append(text[start:i].strip())
        start = j
    text = "\n".join(lines).strip()
    lines.clear()

    logger(f"Now checking '![...]()' style urls in file {readme!r}.")

    # now gather the links to images and remove them
    start = -1
    lines.clear()
    while True:
        start += 1
        i = text.find("![", start)
        if i < start:
            lines.append(text[start:])
            break
        j = text.find("]", i + 1)
        if j <= i:
            break
        if "\n" in text[i:j]:
            start = i
        j += 1
        if text[j] != "(":
            raise __ve(f"Invalid image sequence in file {readme!r}", text, i)
        k = text.find(")", j + 1)
        if k <= j:
            raise __ve("No closing gap for image sequence "
                       f"in file {readme!r}", text, i)

        __check_url(text[j + 1:k], valid_urls)
        total_links_checked += 1

        lines.append(text[start:i])
        start = k

    text = "\n".join(lines)
    lines.clear()

    logger(f"Now checking '[...]()' style urls in file {readme!r}.")

    # now gather the links and remove them
    start = -1
    lines.clear()
    while True:
        start += 1
        i = text.find("[", start)
        if i < start:
            lines.append(text[start:])
            break
        j = text.find("]", i + 1)
        if j <= i:
            break
        if "\n" in text[i:j]:
            lines.append(text[start:i])
            start = i
            continue
        j += 1
        if text[j] != "(":
            raise __ve(f"Invalid [...](...) link in file {readme!r}", text, i)
        k = text.find(")", j + 1)
        if k <= j:
            raise __ve("No closing gap for [...](...)"
                       f" link in file {readme!r}", text, i)

        __check_url(text[j + 1:k], valid_urls)
        total_links_checked += 1

        lines.append(text[start:i])
        start = k

    text = "\n".join(lines)
    lines.clear()

    logger(f"Now checking ' href=' style urls in file {readme!r}.")

    # now gather the href links and remove them
    for quot in "'\"":
        start = -1
        lines.clear()
        while True:
            start += 1
            start_str = f" href={quot}"
            i = text.find(start_str, start)
            if i < start:
                lines.append(text[start:])
                break
            j = text.find(quot, i + len(start_str))
            if j <= i:
                break
            if "\n" in text[i:j]:
                lines.append(text[start:i])
                start = i
                continue
            __check_url(text[i + len(start_str):j], valid_urls)
            total_links_checked += 1

            lines.append(text[start:i])
            start = j

        text = "\n".join(lines)
        lines.clear()

    logger(f"Now checking ' src=' style urls in file {readme!r}.")
    # now gather the image links and remove them
    for quot in "'\"":
        start = -1
        lines.clear()
        while True:
            start += 1
            start_str = f" src={quot}"
            i = text.find(start_str, start)
            if i < start:
                lines.append(text[start:])
                break
            j = text.find(quot, i + len(start_str))
            if j <= i:
                break
            if "\n" in text[i:j]:
                lines.append(text[start:i])
                start = i
                continue
            __check_url(text[i + len(start_str):j], valid_urls)
            total_links_checked += 1

            lines.append(text[start:i])
            start = j

        text = "\n".join(lines)
        lines.clear()

    logger(f"Now checking '<...>' style urls in file {readme!r}.")
    start = -1
    lines.clear()
    while True:
        start += 1
        i = text.find("<http", start)
        if i < start:
            lines.append(text[start:])
            break
        j = text.find(">", i + 1)
        if j <= i:
            break
        if "\n" in text[i:j]:
            lines.append(text[start:i])
            start = i
            continue
        __check_url(text[i + 1:j], valid_urls)
        total_links_checked += 1

        lines.append(text[start:i])
        start = j

    if total_links_checked <= 0:
        raise ValueError(f"Found no links in file {readme!r}.")
    logger(f"Finished testing all links {total_links_checked} in "
           f"file {readme!r}.")
