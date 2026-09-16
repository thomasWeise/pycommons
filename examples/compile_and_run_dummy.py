"""A dummy file for testing for compile-and-run."""

from pycommons.io.path import file_path

path = file_path(__file__)
root = path.up(2)

print(path[str.__len__(root):])
