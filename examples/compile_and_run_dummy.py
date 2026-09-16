"""A dummy file for testing for compile-and-run."""

from pycommons.io.path import file_path

print(file_path(__file__).basename())
