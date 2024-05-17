"""Constants for common characters."""

from typing import Callable, Final

#: A constant for non-breaking space
NBSP: Final[str] = "\xa0"
#: A non-breaking hyphen
NBDASH: Final[str] = "\u2011"

#: A regular expression matching all characters that are non-line breaking
#: white space.
WHITESPACE: Final[str] = (
    "\t\x0b\x0c \xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007"
    "\u2008\u2009\u200a\u202f\u205f\u3000")

#: A regular expression matching all characters that are non-line breaking
#: white space.
NEWLINE: Final[str] = "\n\r\x85\u2028\u2029"

#: A regular expression matching any white space or newline character.
WHITESPACE_OR_NEWLINE: Final[str] = (
    "\t\n\x0b\x0c\r \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000")


#: the internal table for converting normal characters to unicode superscripts
__SUPERSCRIPT: Final[Callable[[str], str]] = {
    # numbers from 0 to 9
    "\x30": "\u2070",  # 0
    "\x31": "\xb9",  # 1
    "\x32": "\xb2",  # 2
    "\x33": "\xb3",  # 3
    "\x34": "\u2074",  # 4
    "\x35": "\u2075",  # 5
    "\x36": "\u2076",  # 6
    "\x37": "\u2077",  # 7
    "\x38": "\u2078",  # 8
    "\x39": "\u2079",  # 9
    # +/-/=/(/)
    "\x2b": "\u207A",  # +
    "\x2d": "\u207b",  # -
    "\x3d": "\u207c",  # =
    "\x28": "\u207d",  # (
    "\x29": "\u207e",  # )
    # upper case letters
    "\x41": "\u1d2c",  # A
    "\x42": "\u1d2e",  # B
    "\x43": "\ua7f2",  # C
    "\x44": "\u1d30",  # D
    "\x45": "\u1d31",  # E
    "\x46": "\ua7f3",  # F
    "\x47": "\u1d33",  # G
    "\x48": "\u1d34",  # H
    "\x49": "\u1d35",  # I
    "\x4a": "\u1d36",  # J
    "\x4b": "\u1d37",  # K
    "\x4c": "\u1d38",  # L
    "\x4d": "\u1d39",  # M
    "\x4e": "\u1d3a",  # N
    "\x4f": "\u1d3c",  # O
    "\x50": "\u1d3e",  # P
    "\x51": "\ua7f4",  # Q
    "\x52": "\u1d3f",  # R
    "\x53": "\ua7f1",  # S
    "\x54": "\u1d40",  # T
    "\x55": "\u1d41",  # U
    "\x56": "\u2c7d",  # V
    "\x57": "\u1d42",  # W
    # lower case letters
    "\x61": "\u1d43",  # a
    "\x62": "\u1d47",  # b
    "\x63": "\u1d9c",  # c
    "\x64": "\u1d48",  # d
    "\x65": "\u1d49",  # e
    "\x66": "\u1da0",  # f
    "\x67": "\u1d4d",  # g
    "\x68": "\u02b0",  # h
    "\x69": "\u2071",  # i
    "\x6a": "\u02b2",  # j
    "\x6b": "\u1d4f",  # k
    "\x6c": "\u1da9",  # l; alternative": "\u2e1
    "\x6d": "\u1d50",  # m
    "\x6e": "\u207f",  # n
    "\x6f": "\u1d52",  # o
    "\x70": "\u1d56",  # p
    "\x71": "\u107a5",  # q
    "\x72": "\u02b3",  # r
    "\x73": "\u02e2",  # s
    "\x74": "\u1d57",  # t
    "\x75": "\u1d58",  # u
    "\x76": "\u1d5b",  # v
    "\x77": "\u02b7",  # w
    "\x78": "\u02e3",  # x
    "\x79": "\u02b8",  # y
    "\x7a": "\u1dbb",  # z
    # white space
    " ": " ",
    "\t": "\t",
    "\n": "\n",
    "\x0b": "\x0b",
    "\x0c": "\x0c",
    "\r": "\r",
    "\x85": "\x85",
    "\xa0": "\xa0",
    "\u1680": "\u1680",
    "\u2000": "\u2000",
    "\u2001": "\u2001",
    "\u2002": "\u2002",
    "\u2003": "\u2003",
    "\u2004": "\u2004",
    "\u2005": "\u2005",
    "\u2006": "\u2006",
    "\u2007": "\u2007",
    "\u2008": "\u2008",
    "\u2009": "\u2009",
    "\u200a": "\u200a",
    "\u2028": "\u2028",
    "\u2029": "\u2029",
    "\u202f": "\u202f",
    "\u205f": "\u205f",
    "\u3000": "\u3000",
}.__getitem__


def superscript(s: str) -> str:
    """
    Transform a string into Unicode-based superscript.

    All characters that can be represented as superscript in unicode will be
    translated to superscript. Notice that only a subset of the latin
    characters can be converted to unicode superscropt. If any character
    cannot be translated, it will  raise a :class:`KeyError`. White space is
    preserved.

    :param s: the string
    :returns: the string in subscript
    :raises KeyError: if a character cannot be converted
    :raises TypeError: if `s` is not a string

    >>> superscript("a0 =4(e)")
    '\u1d43\u2070 \u207c\u2074\u207d\u1d49\u207e'

    >>> try:
    ...     superscript("a0=4(e)Y")
    ... except KeyError as ke:
    ...     print(ke)
    'Y'

    >>> try:
    ...     superscript(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__iter__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     superscript(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__iter__' requires a 'str' object but received a 'int'
    """
    return "".join(map(__SUPERSCRIPT, str.__iter__(s)))


#: the internal table for converting normal characters to unicode subscripts
__SUBSCRIPT: Final[Callable[[str], str]] = {
    # numbers from 0 to 9
    "\x30": "\u2080",  # 0
    "\x31": "\u2081",  # 1
    "\x32": "\u2082",  # 2
    "\x33": "\u2083",  # 3
    "\x34": "\u2084",  # 4
    "\x35": "\u2085",  # 5
    "\x36": "\u2086",  # 6
    "\x37": "\u2087",  # 7
    "\x38": "\u2088",  # 8
    "\x39": "\u2089",  # 9
    # +/-/=/(/)
    "\x2b": "\u208a",  # +
    "\x2d": "\u208b",  # -
    "\x3d": "\u208c",  # =
    "\x28": "\u208d",  # (
    "\x29": "\u208e",  # )
    # lower case letters
    "\x61": "\u2090",  # a
    "\x65": "\u2091",  # e
    "\x68": "\u2095",  # h
    "\x69": "\u1d62",  # i
    "\x6a": "\u2c7c",  # j
    "\x6b": "\u2096",  # k
    "\x6c": "\u2097",  # l
    "\x6d": "\u2098",  # m
    "\x6e": "\u2099",  # n
    "\x6f": "\u2092",  # o
    "\x70": "\u209a",  # p
    "\x73": "\u209b",  # s
    "\x74": "\u209c",  # t
    "\x75": "\u1d64",  # u
    "\x76": "\u1d65",  # v
    "\x78": "\u2093",  # x
    "\u018f": "\u2094",  # letter schwa", upside-down "e"
    # white space
    " ": " ",
    "\t": "\t",
    "\n": "\n",
    "\x0b": "\x0b",
    "\x0c": "\x0c",
    "\r": "\r",
    "\x85": "\x85",
    "\xa0": "\xa0",
    "\u1680": "\u1680",
    "\u2000": "\u2000",
    "\u2001": "\u2001",
    "\u2002": "\u2002",
    "\u2003": "\u2003",
    "\u2004": "\u2004",
    "\u2005": "\u2005",
    "\u2006": "\u2006",
    "\u2007": "\u2007",
    "\u2008": "\u2008",
    "\u2009": "\u2009",
    "\u200a": "\u200a",
    "\u2028": "\u2028",
    "\u2029": "\u2029",
    "\u202f": "\u202f",
    "\u205f": "\u205f",
    "\u3000": "\u3000",
}.__getitem__


def subscript(s: str) -> str:
    """
    Transform a string into Unicode-based subscript.

    All characters that can be represented as subscript in unicode will be
    translated to subscript.  Notice that only a subset of the latin
    characters can be converted to unicode subscript. If any character
    cannot be translated, it will  raise a :class:`KeyError`. White space is
    preserved.

    :param s: the string
    :returns: the string in subscript
    :raises KeyError: if a character cannot be converted
    :raises TypeError: if `s` is not a string

    >>> subscript("a0= 4(e)")
    '\u2090\u2080\u208c \u2084\u208d\u2091\u208e'

    >>> try:
    ...     subscript("a0=4(e)Y")
    ... except KeyError as ke:
    ...     print(ke)
    'Y'

    >>> try:
    ...     subscript(None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__iter__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     superscript(1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__iter__' requires a 'str' object but received a 'int'
    """
    return "".join(map(__SUBSCRIPT, str.__iter__(s)))
