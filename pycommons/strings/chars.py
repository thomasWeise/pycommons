"""Constants for common characters."""

from typing import Final

#: A constant for non-breaking space
NBSP: Final[str] = "\u00a0"
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
