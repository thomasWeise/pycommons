"""Test the type."""
from pytest import raises

from pycommons.io.path import Path
from pycommons.types import type_name, type_name_of


class Outer:
    """The outer class."""

    class Middle:
        """The middle class."""

        class Inner:
            """The inner class."""

            def a(self) -> None:
                """Do nothing."""


def test_type_name() -> None:
    """Test the type name."""
    assert type_name(str) == "str"
    assert type_name(int) == "int"
    assert type_name(type(None)) == "None"
    assert type_name(float) == "float"
    assert type_name(bool) == "bool"
    assert type_name(type) == "type"
    assert type_name(type([])) == "list"
    assert type_name(type(())) == "tuple"
    assert type_name(type(i for i in range(1))) == "generator"
    assert type_name(type(range(1))) == "range"
    assert type_name(type({})) == "dict"
    assert type_name(type(set())) == "set"
    assert type_name(type(test_type_name)) == "function"
    assert type_name(type(print)) == "builtin_function_or_method"
    assert type_name(Outer) == "test_types.Outer"
    assert type_name(Outer.Middle) == "test_types.Outer.Middle"
    assert type_name(Outer.Middle.Inner) == "test_types.Outer.Middle.Inner"
    with raises(TypeError) as excinfo:
        type_name(None)  # noqa
    assert str(excinfo.value) == "type cannot be None."
    assert type_name(Path) == "pycommons.io.path.Path"


def test_type_name_of() -> None:
    """Test the type name of an object."""
    assert type_name_of("") == "str"
    assert type_name_of(1) == "int"
    assert type_name_of(int) == "type"
    assert type_name_of(None) == "None"
    assert type_name_of(1.2) == "float"
    assert type_name_of(True) == "bool"
    assert type_name_of(type) == "type"
    assert type_name_of([]) == "list"
    assert type_name_of(()) == "tuple"
    assert type_name_of(i for i in range(1)) == "generator"
    assert type_name_of(range(1)) == "range"
    assert type_name_of({}) == "dict"
    assert type_name_of(set()) == "set"
    assert type_name_of(test_type_name) == "function"
    assert type_name_of(Outer) == "type"
    assert type_name_of(print) == "builtin_function_or_method"
    assert type_name_of(Outer()) == "test_types.Outer"
    assert type_name_of(Outer.Middle()) == "test_types.Outer.Middle"
    assert (type_name_of(Outer.Middle.Inner())
            == "test_types.Outer.Middle.Inner")
    assert type_name_of(None) == "None"
    assert type_name_of(Path("/bla/")) == "pycommons.io.path.Path"
    assert type_name_of(Outer.Middle.Inner.a) == "function"
