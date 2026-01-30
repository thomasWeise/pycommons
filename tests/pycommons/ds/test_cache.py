"""Test the simple cache."""
from pycommons.ds.cache import is_new, repr_cache


def test_is_new() -> None:
    """Test the is_new function."""
    is_new_1 = is_new()
    assert is_new_1 is not None
    assert callable(is_new_1)
    is_new_2 = is_new()
    assert is_new_2 is not None
    assert is_new_1 is not is_new_2
    assert callable(is_new_2)

    assert is_new_1("a")
    assert is_new_2("a")

    assert is_new_1("b")
    assert is_new_1("c")
    assert is_new_2("c")

    assert not is_new_1("a")
    assert not is_new_2("c")
    assert not is_new_1("b")
    assert not is_new_1("c")

    assert is_new_2("b")
    assert not is_new_2("b")

    is_new_3 = is_new()
    assert is_new_3("b")
    assert is_new_3("c")
    assert is_new_3("a")
    assert not is_new_3("b")
    assert not is_new_3("c")
    assert not is_new_3("a")


def test_repr_cache() -> None:
    """Test the `repr_cache` function."""
    cache_1 = repr_cache()
    cache_2 = repr_cache()
    assert cache_1 is not cache_2
    a = {1: "2", 2: "3", 3: "4"}
    b = {1: "2", 2: "3", 3: "4"}
    c = {1: "2", 2: "3", 3: "5"}
    d = a
    assert cache_1(a) is a
    assert cache_1(b) is a
    assert cache_1(c) is not a
    assert cache_1(c) is c
    assert cache_1(d) is a

    assert cache_2(b) is b
    assert cache_2(b) is not a
    assert cache_2(a) is b
    assert cache_2(c) is c
    assert cache_2(d) is b
