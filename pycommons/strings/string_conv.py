"""Converting stuff to strings-."""

from math import isnan
from typing import Final

from pycommons.math.int_math import __try_int
from pycommons.types import type_error


def float_to_str(value: float) -> str:
    """
    Convert `float` to a string.

    The floating point value `value` is converted to a string.
    A `ValueError` is thrown if `value` is `NaN`.
    A `TypeError` is thrown if `value` is not a `float`.

    :param value: the floating point value
    :return: the string representation

    >>> float_to_str(1.3)
    '1.3'
    >>> float_to_str(1.0)
    '1'
    >>> float_to_str(1e-5)
    '1e-5'
    >>> try:
    ...     float_to_str(1)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of float but is int, namely '1'.
    >>> try:
    ...     float_to_str(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of float but is None.
    >>> from math import nan
    >>> try:
    ...     float_to_str(nan)
    ... except ValueError as ve:
    ...     print(ve)
    nan => 'nan' is not a permitted float.
    >>> from math import inf
    >>> float_to_str(inf)
    'inf'
    >>> float_to_str(-inf)
    '-inf'
    >>> float_to_str(1e300)
    '1e300'
    >>> float_to_str(-1e300)
    '-1e300'
    >>> float_to_str(-1e-300)
    '-1e-300'
    >>> float_to_str(1e-300)
    '1e-300'
    >>> float_to_str(1e1)
    '10'
    >>> float_to_str(1e5)
    '100000'
    >>> float_to_str(1e10)
    '10000000000'
    >>> float_to_str(1e20)
    '1e20'
    >>> float_to_str(1e030)
    '1e30'
    >>> float_to_str(0.0)
    '0'
    >>> float_to_str(-0.0)
    '0'
    """
    if not isinstance(value, float):
        raise type_error(value, "value", float)
    if value == 0.0:
        return "0"
    s = (repr(value).replace("e-0", "e-").replace("e+0", "e")
         .replace("e+", "e"))
    if isnan(value):
        raise ValueError(f"{value!r} => {str(s)!r} is not a permitted float.")
    if s.endswith(".0"):
        return s[:-2]
    return s


def bool_to_str(value: bool) -> str:
    """
    Convert a Boolean value to a string.

    If `value == True`, then `"T"` is returned.
    If `value == False`, then `"F"` is returned.
    Otherwise, a `TypeError` is thrown.
    This function is the inverse of :func:`str_to_bool`.

    :param value: the Boolean value
    :return: the string

    >>> print(bool_to_str(True))
    T
    >>> print(bool_to_str(False))
    F
    >>> try:
    ...     bool_to_str("t")
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of bool but is str, namely 't'.
    >>> try:
    ...     bool_to_str(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of bool but is None.
    """
    if not isinstance(value, bool):
        raise type_error(value, "value", bool)
    return "T" if value else "F"


def str_to_bool(value: str) -> bool:
    """
    Convert a string to a boolean value.

    If `value == "T"`, then `True` is returned.
    If `value == "F"`, then `False` is returned.
    If `value` is a different `str`, a `ValueError` is thrown.
    Otherwise, a `TypeError` is thrown.
    This function is the inverse of :func:`bool_to_str`.

    :param value: the string value
    :return: the boolean value

    >>> str_to_bool("T")
    True
    >>> str_to_bool("F")
    False
    >>> try:
    ...     str_to_bool("x")
    ... except ValueError as v:
    ...     print(v)
    Expected 'T' or 'F', but got 'x'.
    >>> try:
    ...     str_to_bool(1)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is int, namely '1'.
    >>> try:
    ...     str_to_bool(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is None.
    """
    if not isinstance(value, str):
        raise type_error(value, "value", str)
    if value == "T":
        return True
    if value == "F":
        return False
    raise ValueError(f"Expected 'T' or 'F', but got {value!r}.")


def num_to_str(value: int | float) -> str:
    """
    Transform a numerical type (`int`, `float`, or `bool`) to a string.

    If `value` is an instance of `int`, the result of its conversion via `str`
    will be returned.
    If `value` is an instance of `bool`, a `TypeError` will be raised.
    Otherwise, the result of :func:`~float_to_str` is returned.
    This means that `nan` will yield a `ValueError` and anything that is
    neither an `int`, `bool`, or `float` will incur a `TypeError`.

    :param value: the value
    :return: the string

    >>> num_to_str(1)
    '1'
    >>> num_to_str(1.5)
    '1.5'
    >>> try:
    ...     num_to_str(True)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is bool, \
namely 'True'.
    >>> try:
    ...     num_to_str(False)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is bool, \
namely 'False'.
    >>> try:
    ...     num_to_str("x")
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of float but is str, namely 'x'.
    >>> try:
    ...     num_to_str(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of float but is None.
    >>> from math import inf, nan
    >>> try:
    ...     num_to_str(nan)
    ... except ValueError as ve:
    ...     print(ve)
    nan => 'nan' is not a permitted float.
    >>> num_to_str(inf)
    'inf'
    >>> num_to_str(-inf)
    '-inf'
    """
    if isinstance(value, bool):
        raise type_error(value, "value", (int, float))
    return str(value) if isinstance(value, int) else float_to_str(value)


def num_or_none_to_str(value: int | float | None) -> str:
    """
    Convert a numerical type (`int`, `float`) or `None` to a string.

    If `value is None`, then `""` is returned.
    Otherwise, the result of :func:`~num_to_str` is returned.

    :param value: the value
    :return: the string representation, `""` for `None`

    >>> print(repr(num_or_none_to_str(None)))
    ''
    >>> print(num_or_none_to_str(12))
    12
    >>> print(num_or_none_to_str(12.3))
    12.3
    >>> try:
    ...     num_or_none_to_str(True)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is bool, \
namely 'True'.
    >>> try:
    ...     num_or_none_to_str(False)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of any in {float, int} but is bool, \
namely 'False'.
    >>> from math import nan
    >>> try:
    ...     num_to_str(nan)
    ... except ValueError as ve:
    ...     print(ve)
    nan => 'nan' is not a permitted float.
    """
    return "" if value is None else num_to_str(value)


def int_or_none_to_str(value: int | None) -> str:
    """
    Convert an integer or `None` to a string.

    If `value is None`, `""` is returned.
    If `value` is an instance of `bool`, a `TypeError` is raised.
    If `value` is an `int`, `str(val)` is returned.
    Otherwise, a `TypeError` is thrown.

    :param value: the value
    :return: the string representation, `''` for `None`

    >>> print(repr(int_or_none_to_str(None)))
    ''
    >>> print(int_or_none_to_str(12))
    12
    >>> try:
    ...     int_or_none_to_str(True)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of int but is bool, namely 'True'.
    >>> try:
    ...     int_or_none_to_str(False)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of int but is bool, namely 'False'.
    >>> print(int_or_none_to_str(-10))
    -10
    >>> try:
    ...     int_or_none_to_str(1.0)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of int but is float, namely '1.0'.
    """
    if value is None:
        return ""
    if isinstance(value, bool) or (not isinstance(value, int)):
        raise type_error(value, "value", int)
    return str(value)


def __str_to_num_or_none(value: str | None,
                         none_is_ok: bool) -> int | float | None:
    """
    Convert a string to an `int` or `float`.

    If `value is None` and `none_is_ok == True`, then `None` is returned.
    If `value` is not an instance of `str`, a `TypeError` will be raised.
    If `value` becomes an empty string after stripping, then `None` is
    returned if `none_is_ok == True` and else an `ValueError` is raised.
    If the value `value` can be converted to an integer without loss of
    precision, then an `int` with the corresponding value is returned.
    If the value `value` can be converted to a `float`, a `float` with the
    appropriate value is returned.
    Otherwise, a `ValueError` is thrown.

    :param value: the string value
    :return: the `int` or `float` or `None` corresponding to `value`

    >>> print(type(__str_to_num_or_none("15.0", False)))
    <class 'int'>
    >>> print(type(__str_to_num_or_none("15.1", False)))
    <class 'float'>
    >>> __str_to_num_or_none("inf", False)
    inf
    >>> __str_to_num_or_none("  -inf  ", False)
    -inf
    >>> try:
    ...     __str_to_num_or_none(21, False)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is int, namely '21'.
    >>> try:
    ...     __str_to_num_or_none("nan", False)
    ... except ValueError as ve:
    ...     print(ve)
    NaN is not permitted, but got 'nan'.
    >>> try:
    ...     __str_to_num_or_none("12-3", False)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '12-3'.
    >>> __str_to_num_or_none("1e34423", False)
    inf
    >>> __str_to_num_or_none("-1e34423", False)
    -inf
    >>> __str_to_num_or_none("-1e-34423", False)
    0
    >>> __str_to_num_or_none("1e-34423", False)
    0
    >>> try:
    ...     __str_to_num_or_none("-1e-34e4423", False)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '-1e-34e4423'.
    >>> try:
    ...     __str_to_num_or_none("T", False)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'T'.
    >>> try:
    ...     __str_to_num_or_none("F", False)
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'F'.
    >>> try:
    ...     __str_to_num_or_none(None, False)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is None.
    >>> try:
    ...     __str_to_num_or_none(" ", False)
    ... except ValueError as ve:
    ...     print(ve)
    Value ' ' becomes empty after stripping, cannot be converted to a number.
    >>> try:
    ...     __str_to_num_or_none("", False)
    ... except ValueError as ve:
    ...     print(ve)
    Value '' becomes empty after stripping, cannot be converted to a number.
    >>> print(__str_to_num_or_none(" ", True))
    None
    >>> print(__str_to_num_or_none("", True))
    None
    >>> print(__str_to_num_or_none(None, True))
    None
    """
    if (value is None) and none_is_ok:
        return None
    if not isinstance(value, str):
        raise type_error(value, "value", str)
    vv: Final[str] = value.strip().lower()
    if len(vv) <= 0:
        if none_is_ok:
            return None
        raise ValueError(f"Value {value!r} becomes empty after stripping, "
                         "cannot be converted to a number.")
    try:
        return int(vv)
    except ValueError:
        pass
    res: float
    try:
        res = float(vv)
    except ValueError as ve:
        raise ValueError(f"Invalid numerical value {value!r}.") from ve
    if isnan(res):
        raise ValueError(f"NaN is not permitted, but got {value!r}.")
    return __try_int(res)


def str_to_num(value: str) -> int | float:
    """
    Convert a string to an `int` or `float`.

    If `value` is not an instance of `str`, a `TypeError` will be raised.
    If the value `value` can be converted to an integer, then an `int` with
    the corresponding value is returned.
    If the value `value` can be converted to a `float`, a `float` with the
    appropriate value is returned.
    Otherwise, a `ValueError` is thrown.

    :param value: the string value
    :return: the `int` or `float`: Integers are preferred to be used whereever
        possible

    >>> print(type(str_to_num("15.0")))
    <class 'int'>
    >>> print(type(str_to_num("15.1")))
    <class 'float'>
    >>> str_to_num("inf")
    inf
    >>> str_to_num("  -inf  ")
    -inf
    >>> try:
    ...     str_to_num(21)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is int, namely '21'.
    >>> try:
    ...     str_to_num("nan")
    ... except ValueError as ve:
    ...     print(ve)
    NaN is not permitted, but got 'nan'.
    >>> try:
    ...     str_to_num("12-3")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '12-3'.
    >>> str_to_num("1e34423")
    inf
    >>> str_to_num("-1e34423")
    -inf
    >>> str_to_num("-1e-34423")
    0
    >>> str_to_num("1e-34423")
    0
    >>> try:
    ...     str_to_num("-1e-34e4423")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '-1e-34e4423'.
    >>> try:
    ...     str_to_num("T")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'T'.
    >>> try:
    ...     str_to_num("F")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'F'.
    >>> try:
    ...     str_to_num(None)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is None.
    >>> try:
    ...     str_to_num("")
    ... except ValueError as ve:
    ...     print(ve)
    Value '' becomes empty after stripping, cannot be converted to a number.
    """
    return __str_to_num_or_none(value, False)


def str_to_num_or_none(value: str | None) -> int | float | None:
    """
    Convert a string to an `int` or `float` or `None`.

    If the value `value` is `None`, then `None` is returned.
    If the vlaue `value` is empty or entirely composed of white space, `None`
    is returned.
    If the value `value` can be converted to an integer, then an `int` with
    the corresponding value is returned.
    If the value `value` can be converted to a `float`, a `float` with the
    appropriate value is returned.
    Otherwise, a `ValueError` is thrown.

    :param value: the string value
    :return: the `int` or `float` or `None`

    >>> print(type(str_to_num_or_none("15.0")))
    <class 'int'>
    >>> print(type(str_to_num_or_none("15.1")))
    <class 'float'>
    >>> str_to_num_or_none("inf")
    inf
    >>> str_to_num_or_none("  -inf  ")
    -inf
    >>> try:
    ...     str_to_num_or_none(21)
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is int, namely '21'.
    >>> try:
    ...     str_to_num_or_none("nan")
    ... except ValueError as ve:
    ...     print(ve)
    NaN is not permitted, but got 'nan'.
    >>> try:
    ...     str_to_num_or_none("12-3")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '12-3'.
    >>> str_to_num_or_none("1e34423")
    inf
    >>> str_to_num_or_none("-1e34423")
    -inf
    >>> str_to_num_or_none("-1e-34423")
    0
    >>> str_to_num_or_none("1e-34423")
    0
    >>> try:
    ...     str_to_num_or_none("-1e-34e4423")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value '-1e-34e4423'.
    >>> try:
    ...     str_to_num_or_none("T")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'T'.
    >>> try:
    ...     str_to_num_or_none("F")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid numerical value 'F'.
    >>> print(str_to_num_or_none(""))
    None
    >>> print(str_to_num_or_none(None))
    None
    >>> print(type(str_to_num_or_none("5.0")))
    <class 'int'>
    >>> print(type(str_to_num_or_none("5.1")))
    <class 'float'>
    """
    return __str_to_num_or_none(value, True)


def str_to_int_or_none(value: str | None) -> int | None:
    """
    Convert a string to an `int` or `None`.

    If the value `value` is `None`, then `None` is returned.
    If the vlaue `value` is empty or entirely composed of white space, `None`
    is returned.
    If the value `value` can be converted to an integer, then an `int` with
    the corresponding value is returned.
    Otherwise, a `ValueError` is thrown.

    :param value: the string value, or `None`
    :return: the int or None

    >>> print(str_to_int_or_none(""))
    None
    >>> print(str_to_int_or_none("5"))
    5
    >>> print(str_to_int_or_none(None))
    None
    >>> print(str_to_int_or_none("  "))
    None
    >>> try:
    ...     print(str_to_int_or_none(1.3))
    ... except TypeError as te:
    ...     print(te)
    value should be an instance of str but is float, namely '1.3'.
    >>> try:
    ...     print(str_to_int_or_none("1.3"))
    ... except ValueError as ve:
    ...     print(ve)
    invalid literal for int() with base 10: '1.3'
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise type_error(value, "value", str)
    vv: Final[str] = value.strip().lower()
    if len(vv) <= 0:
        return None
    return int(vv)
