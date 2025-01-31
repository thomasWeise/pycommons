"""Demonstrate the use of the cache function."""

from pycommons.ds.cache import str_is_new

checker = str_is_new()
print(f"{checker("a")=}")  # True
print(f"{checker("a")=}")  # False
print(f"{checker("b")=}")  # True
print(f"{checker("a")=}")  # False
print(f"{checker("c")=}")  # True
print(f"{checker("a")=}")  # False
print(f"{checker("b")=}")  # False
