"""Demonstrate the use of the cache function."""

from typing import Callable

from pycommons.ds.cache import is_new

checker: Callable[[str], bool] = is_new()
print(f"{checker('a')=}")  # True
print(f"{checker('a')=}")  # False
print(f"{checker('b')=}")  # True
print(f"{checker('a')=}")  # False
print(f"{checker('c')=}")  # True
print(f"{checker('a')=}")  # False
print(f"{checker('b')=}")  # False
