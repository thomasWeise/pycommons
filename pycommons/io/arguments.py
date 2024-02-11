"""The parser for command line arguments."""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from datetime import datetime, timezone
from typing import Final

from pycommons.processes.python import python_command
from pycommons.strings import NBDASH, NBSP
from pycommons.types import check_int_range, type_error

#: The default argument parser for latexgit executables.
__DEFAULT_ARGUMENTS: Final[ArgumentParser] = ArgumentParser(
    add_help=False,
    formatter_class=ArgumentDefaultsHelpFormatter,
)


def make_argparser(file: str, description: str, epilog: str) -> ArgumentParser:
    r"""
    Create an argument parser with default settings.

    :param file: the `__file__` special variable of the calling script
    :param description: the description string
    :param epilog: the epilogue string
    :returns: the argument parser

    >>> ap = make_argparser(__file__, "This is a test program.",
    ...                     "This is a test.")
    >>> isinstance(ap, ArgumentParser)
    True

    >>> from contextlib import redirect_stdout
    >>> from io import StringIO
    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     ap.print_usage()
    >>> print(s.getvalue())
    usage: python3 -m pycommons.io.arguments [-h]
    <BLANKLINE>

    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     ap.print_help()
    >>> print(s.getvalue())
    usage: python3 -m pycommons.io.arguments [-h]
    <BLANKLINE>
    This is a test program.
    <BLANKLINE>
    options:
      -h, --help  show this help message and exit
    <BLANKLINE>
    This is a test.
    <BLANKLINE>

    >>> ap = make_argparser(__file__, "This is a test program.",
    ...     make_epilog("This program computes something",
    ...                 2022, 2023, "Thomas Weise",
    ...                 url="https://github.com/thomasWeise/pycommons",
    ...                 email="tweise@hfuu.edu.cn"))
    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     ap.print_help()
    >>> v = ('usage: python3 -m pycommons.io.arguments [-h]\n\nThis is '
    ...      'a test program.\n\noptions:\n  -h, --help  show this help '
    ...      'message and exit\n\nThis program computes something Copyright'
    ...      '\xa0©\xa02022\u20112023,\xa0Thomas\xa0Weise,\nGNU\xa0GENERAL'
    ...      '\xa0PUBLIC\xa0LICENSE\xa0Version\xa03,\xa029\xa0June'
    ...      '\xa02007,\nhttps://github.com/thomasWeise/pycommons, '
    ...      'tweise@hfuu.edu.cn\n')
    >>> s.getvalue() == v
    True

    >>> try:
    ...     make_argparser(1, "", "")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     make_argparser(None, "", "")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     make_argparser("te", "", "")
    ... except ValueError as ve:
    ...     print(ve)
    invalid file='te'.

    >>> try:
    ...     make_argparser("test", 1, "")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_argparser("Test", None, "")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     make_argparser("Test", "Bla", "")
    ... except ValueError as ve:
    ...     print(ve)
    invalid description='Bla'.

    >>> try:
    ...     make_argparser("Test", "This is a long test", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_argparser("Test", "This is a long test", None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     make_argparser("Test", "This is a long test", "epi")
    ... except ValueError as ve:
    ...     print(ve)
    invalid epilog='epi'.
    """
    if str.__len__(file) <= 3:
        raise ValueError(f"invalid file={file!r}.")
    description = str.strip(description)
    if str.__len__(description) <= 12:
        raise ValueError(f"invalid description={description!r}.")
    epilog = str.strip(epilog)
    if str.__len__(epilog) <= 10:
        raise ValueError(f"invalid epilog={epilog!r}.")
    return ArgumentParser(
        parents=[__DEFAULT_ARGUMENTS], prog=" ".join(python_command(file)),
        description=description, epilog=epilog,
        formatter_class=__DEFAULT_ARGUMENTS.formatter_class)


def add_version(arguments: ArgumentParser, version: str) -> ArgumentParser:
    """
    Add a version string to the given argument parser.

    :param arguments: the argument parser
    :param version: the version string
    :return: the argument parser

    >>> ap = make_argparser(__file__, "This is a test program.",
    ...                     "This is a test.")
    >>> x = add_version(ap, "1.0")
    >>> from contextlib import redirect_stdout
    >>> from io import StringIO
    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     ap.print_usage()
    >>> print(s.getvalue())
    usage: python3 -m pycommons.io.arguments [-h] [--version]
    <BLANKLINE>

    >>> s = StringIO()
    >>> with redirect_stdout(s):
    ...     ap.print_help()
    >>> print(s.getvalue())
    usage: python3 -m pycommons.io.arguments [-h] [--version]
    <BLANKLINE>
    This is a test program.
    <BLANKLINE>
    options:
      -h, --help  show this help message and exit
      --version   show program's version number and exit
    <BLANKLINE>
    This is a test.
    <BLANKLINE>

    >>> try:
    ...     add_version(None, "3.2")
    ... except TypeError as te:
    ...     print(te)
    argparser should be an instance of argparse.ArgumentParser but is None.

    >>> try:
    ...     add_version(1, "3.2")
    ... except TypeError as te:
    ...     print(te)
    argparser should be an instance of argparse.ArgumentParser but is \
int, namely '1'.

    >>> try:
    ...     add_version(ap, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     add_version(ap, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     add_version(ap, "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid version string ''.
    """
    if not isinstance(arguments, ArgumentParser):
        raise type_error(arguments, "argparser", ArgumentParser)
    version = str.strip(version)
    if str.__len__(version) < 1:
        raise ValueError(f"Invalid version string {version!r}.")
    arguments.add_argument("--version", action="version", version=version)
    return arguments


def make_epilog(
        text: str, copyright_start: int | None = None,
        copyright_end: int | None = None, author: str | None = None,
        the_license: str | None =
        "GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007",
        url: str | None = None,
        email: str | None = None) -> str:
    r"""
    Build an epilogue from the given components.

    :param text: the epilog text
    :param copyright_start: the start year of the copyright, or `None` for no
        copyright duration
    :param copyright_end: the end year of the copyright, or `None` for using
        the current year (unless `copyright_start` is `None`, in which case,
        no copyright information is generated).
    :param author: the author name, or `None` for no author
    :param the_license: the license, or `None` for no license
    :param url: the URL, or `None` for no URL
    :param email: the email address(es) of the author, or `None` for no email
        address information
    :return: the copyright information

    >>> cy = datetime.now(tz=timezone.utc).year
    >>> ex = (f"This is a test.\n\nGNU\xa0GENERAL\xa0PUBLIC\xa0LICENSE"
    ...       "\xa0Version\xa03,\xa029\xa0June\xa02007")
    >>> make_epilog("This is a test.") == ex
    True

    >>> make_epilog("This is a test.", 2011, 2030, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[:50]
    'This is a test.\n\nCopyright\xa0©\xa02011\u20112030,\xa0Test\xa0User,'

    >>> ex = (f"This is a test.\n\nCopyright\xa0©\xa02011\u2011{cy},"
    ...        "\xa0Test\xa0User, Test\xa0License, http://testurl, "
    ...        "test@test.com")
    >>> make_epilog("This is a test.", 2011, None, "Test User",
    ...             "Test License", "http://testurl", "test@test.com") == ex
    True

    >>> make_epilog("This is a test.", 2011, 2030, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[50:]
    ' Test\xa0License, http://testurl, test@test.com'

    >>> make_epilog("This is a test.", 2030, 2030, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[:50]
    'This is a test.\n\nCopyright\xa0©\xa02030,\xa0Test\xa0User, Test'

    >>> make_epilog("This is a test.", 2030, 2030, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[50:]
    '\xa0License, http://testurl, test@test.com'

    >>> make_epilog("This is a test.", None, None, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[:50]
    'This is a test.\n\nTest\xa0User, Test\xa0License, http://t'

    >>> make_epilog("This is a test.", None, None, "Test User",
    ...             "Test License", "http://testurl", "test@test.com")[50:]
    'esturl, test@test.com'

    >>> try:
    ...     make_epilog(1, None, None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_epilog(None, None, None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     make_epilog("1", None, None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    Epilog text too short: '1'.

    >>> try:
    ...     make_epilog("This is a test.", "v", None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    copyright_start should be an instance of int but is str, namely 'v'.

    >>> try:
    ...     make_epilog("This is a test.", -2, None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    copyright_start=-2 is invalid, must be in 1970..2500.

    >>> try:
    ...     make_epilog("This is a test.", 3455334, None, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    copyright_start=3455334 is invalid, must be in 1970..2500.

    >>> try:
    ...     make_epilog("This is a test.", 2002, "v", "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    copyright_end should be an instance of int but is str, namely 'v'.

    >>> try:
    ...     make_epilog("This is a test.", 2002, 12, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    copyright_end=12 is invalid, must be in 2002..2500.

    >>> try:
    ...     make_epilog("This is a test.", 2023, 3455334, "Test User",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    copyright_end=3455334 is invalid, must be in 2023..2500.

    >>> try:
    ...     make_epilog("This is a test.", None, None, 2,
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_epilog("This is a test.", None, None, "",
    ...                 "Test License", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    Author too short: ''.

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 23, "http://testurl", "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 "Te", "http://testurl", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    License too short: 'Te'.

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 "GPL", 2, "test@test.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 "GPL", "http", "test@test.com")
    ... except ValueError as ve:
    ...     print(ve)
    Url too short: 'http'.

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 "GPL", "http://www.test.com", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     make_epilog("This is a test.", None, None, "Tester",
    ...                 "GPL", "http://www.test.com", "a@b")
    ... except ValueError as ve:
    ...     print(ve)
    Email too short: 'a@b'.
    """
    text = str.strip(text)
    if str.__len__(text) <= 10:
        raise ValueError(f"Epilog text too short: {text!r}.")
    the_epilog: str = ""
    if copyright_start is not None:
        copyright_start = check_int_range(
            copyright_start, "copyright_start", 1970, 2500)
        if copyright_end is None:
            copyright_end = check_int_range(
                datetime.now(tz=timezone.utc).year, "year", 1970, 2500)
        else:
            copyright_end = check_int_range(
                copyright_end, "copyright_end", copyright_start, 2500)
        the_epilog = f"Copyright \u00a9 {copyright_start}" \
            if copyright_start >= copyright_end \
            else f"Copyright \u00a9 {copyright_start}-{copyright_end}"
    if author is not None:
        author = str.strip(author)
        if str.__len__(author) < 1:
            raise ValueError(f"Author too short: {author!r}.")
        the_epilog = f"{the_epilog}, {author}" \
            if str.__len__(the_epilog) > 0 else author
    if the_license is not None:
        the_license = str.strip(the_license)
        if str.__len__(the_license) < 3:
            raise ValueError(f"License too short: {the_license!r}.")
        the_epilog = f"{the_epilog},\n{the_license}" \
            if str.__len__(the_epilog) > 0 else the_license
    if url is not None:
        url = str.strip(url)
        if str.__len__(url) < 6:
            raise ValueError(f"Url too short: {url!r}.")
        the_epilog = f"{the_epilog},\n{url}" \
            if str.__len__(the_epilog) > 0 else url
    if email is not None:
        email = str.strip(email)
        if str.__len__(email) < 5:
            raise ValueError(f"Email too short: {email!r}.")
        the_epilog = f"{the_epilog},\n{email}" \
            if str.__len__(the_epilog) > 0 else email

    the_epilog = (the_epilog.replace(" ", NBSP)
                  .replace("-", NBDASH).replace("\n", " "))
    return f"{text}\n\n{the_epilog}"
