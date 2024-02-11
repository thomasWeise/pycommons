"""Test the simple cache."""
from pycommons.ds.cache import str_is_new


def test_str_is_new() -> None:
    """Test the str_is_new function."""
    str_is_new_1 = str_is_new()
    assert str_is_new_1 is not None
    assert callable(str_is_new_1)
    str_is_new_2 = str_is_new()
    assert str_is_new_2 is not None
    assert str_is_new_1 is not str_is_new_2
    assert callable(str_is_new_2)

    assert str_is_new_1("a")
    assert str_is_new_2("a")

    assert str_is_new_1("b")
    assert str_is_new_1("c")
    assert str_is_new_2("c")

    assert not str_is_new_1("a")
    assert not str_is_new_2("c")
    assert not str_is_new_1("b")
    assert not str_is_new_1("c")

    assert str_is_new_2("b")
    assert not str_is_new_2("b")

    str_is_new_3 = str_is_new()
    assert str_is_new_3("b")
    assert str_is_new_3("c")
    assert str_is_new_3("a")
    assert not str_is_new_3("b")
    assert not str_is_new_3("c")
    assert not str_is_new_3("a")
