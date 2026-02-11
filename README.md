[![make build](https://github.com/thomasWeise/pycommons/actions/workflows/build.yml/badge.svg)](https://github.com/thomasWeise/pycommons/actions/workflows/build.yml)
[![pypi version](https://img.shields.io/pypi/v/pycommons)](https://pypi.org/project/pycommons)
[![pypi downloads](https://img.shields.io/pypi/dw/pycommons.svg)](https://pypistats.org/packages/pycommons)
[![coverage report](https://shields.io/badge/pytest-coverage-009000)](https://thomasweise.github.io/pycommons/tc/index.html)
[![https://thomasweise.github.io](https://shields.io/badge/home-thomasweise.github.io-009000)](https://thomasweise.github.io)

# *pycommons:* Common Utility Functions for Python Projects.

Some common utility functionality for Python projects.

- [Introduction](#1-introduction)
- [Installation](#2-installation)
- [Examples](#3-examples)
- [License](#4-license)
- [Contact](#5-contact)


## 1. Introduction

In this project, we combine several utilities and functions that are used in our other projects.

These functions have in common that they are fail-fast.
They usually check the types of all of their inputs and raise exceptions immediately if something looks dodgy.
There is no garbage-in/garbage-out:
Our functions raise descriptive errors as soon as they detect something strange.


## 2. Installation

In order to use this package, you need to first install it using [`pip`](https://pypi.org/project/pip) or some other tool that can install packages from [PyPi](https://pypi.org).
You can install the newest version of this library from [PyPi](https://pypi.org/project/pycommons) using [`pip`](https://pypi.org/project/pip) by doing

```shell
pip install pycommons
```

This will install the latest official release of our package as well as [all dependencies](https://thomasweise.github.io/pycommons/requirements_txt.html).
If you want to install the latest source code version from GitHub (which may not yet be officially released), you can do

```shell
pip install git+https://github.com/thomasWeise/pycommons.git
```

If you want to install the latest source code version from GitHub (which may not yet be officially released) and you have set up a private/public key for GitHub, you can also do:

```shell
git clone ssh://git@github.com/thomasWeise/pycommons
pip install pycommons
```

This may sometimes work better if you are having trouble reaching GitHub via `https` or `http`.

You can also clone the repository and then run a build script, which will automatically install all dependencies, run all the tests, and then install the package on your system, too.
This will work only on Linux, though.
If this build completes successful, you can be sure that [`pycommons`](https://thomasweise.github.io/pycommons) will work properly on your machine.

All dependencies for using and running `pycommons` are listed at [here](https://thomasweise.github.io/pycommons/requirements_txt.html).


## 3. Examples

### 3.1. Unified Build Process: `pycommons.dev.building`
The package [`pycommons.dev.building`](/pycommons/pycommons.dev.building.html) provides unified build steps that I use in all of my Python projects.
After you have installed `pycommons`, the following build steps become available.
You would execute them inside the directory where your Python package's code is.
Let's say your package's name is `mypackage`, then you can do:

- `python3 -m pycommons.dev.building.run_tests --package mypackage` to run the [pytest](https://pytest.org) unit tests and the [doctests](https://docs.python.org/3/library/doctest.html).
  This execution uses a time limit and also collects [coverage](https://coverage.readthedocs.io/en/7.13.2) data.
  The test coverage is rendered to HTML using the documentation generation step&nbsp;(two keypoints down from here).
- `python3 -m pycommons.dev.building.static_analysis --package mypackage` performs a wide range of strict static analyses.
  All of them are used in rather strict settings.
  Thus, if this step succeeds, your code should be quite clean and nice.
  We use tools such as:
  + [`autoflake`](https://pypi.org/project/autoflake), a tool for finding unused imports and variables,
  + [`bandit`](https://pypi.org/project/bandit), a linter for finding security issues,
  + [`dodgy`](https://pypi.org/project/dodgy), for checking for dodgy looking values in the code,
  + [`flake8`](https://pypi.org/project/flake8), a collection of linters,
  + [`flake8-2020`](https://pypi.org/project/flake8-2020), which checks misuse of things like `sys.version`,
  + [`flake8-absolute-import`](https://pypi.org/project/flake8-absolute-import`), which enforces absolute imports,
  + [`flake8-bugbear`](https://pypi.org/project/flake8-bugbear), for finding likely bugs and design problems,
  + [`flake8-builtins`](https://pypi.org/project/flake8-builtins), which checks name clashes with builtins,
  + [`flake8-commas`](https://pypi.org/project/flake8-commas), which checks that commas are put in proper places,
  + [`flake8-comprehensions`](https://pypi.org/project/flake8-comprehensions), a plugin for enforcing proper list/dict/set comprehension,
  + [`flake8-docstrings`](https://pypi.org/project/flake8-docstrings), which applies [`pydocstyle`](https://pypi.org/project/pydocstyle), for checking the format of the docstrings, 
  + [`flake8-eradicate`](https://pypi.org/project/flake8-eradicate), for searching for dead code,
  + [`flake8-length`](https://pypi.org/project/flake8-length), which performs line length validation,
  + [`flake8-mutable`](https://pypi.org/project/flake8-mutable), which checks for mutable default arguments,
  + [`flake8-pie`](https://pypi.org/project/flake8-pie), which searches for miscellaneous errors,
  + [`flake8-printf-formatting`](https://pypi.org/project/flake8-printf-formatting), which detects outdated printf-style formatting,
  + [`flake8-pyi`](https://pypi.org/project/flake8-pyi) for linting type-hinting stub files,
  + [`flake8-pytest-style`](https://pypi.org/project/flake8-pytest-style), for checking common style issues or inconsistencies with pytest-based tests,
  + [`flake8-use-fstring`](https://pypi.org/project/flake8-use-fstring), for checking the correct use of f-strings,
  + [`mypy`](https://pypi.org/project/mypy), for checking types and type annotations,
  + [`pycodestyle`](https://pypi.org/project/pycodestyle), for checking the formatting and coding style of the source,
  + [`pydocstyle`](https://pypi.org/project/pydocstyle), for checking the format of the docstrings,
  + [`pyflakes`](https://pypi.org/project/pyflakes), for detecting some errors in the code,
  + [`pylint`](https://pypi.org/project/pylint), another static analysis tool,
  + [`pyroma`](https://pypi.org/project/pyroma), for checking whether the code complies with various best practices,
  + [`ruff`](https://pypi.org/project/ruff), a static analysis tool checking a wide range of coding conventions,
  + [`tryceratops`](https://pypi.org/project/tryceratops), for checking against exception handling anti-patterns,
  + [`unimport`](https://pypi.org/project/unimport), for checking against unused import statements, and
  + [`vulture`](https://pypi.org/project/vulture), for finding dead code.
- `python3 -m pycommons.dev.building.make_documentation --package mypackage` will build the documentation and documentation website.
  It will use [Sphinx](https://www.sphinx-doc.org) for this and automatically links also to external Python libraries if need be.
  It will also render files such as `LICENSE.md` and `requirements.txt` to HTML, include the coverage data&nbsp;(generated by the tests build step) as a subdirectory, will include all source codes as HTML, and will include a list of required packages.
  It uses the same style as the [pycommons](https://thomasweise.github.io/pycommons), [moptipy](https://thomasweise.github.io/moptipy), [moptipyapps](https://thomasweise.github.io/moptipyapps), and [texgit_py](https://thomasweise.github.io/texgit_py) websites.
  It uses the folder `docs/sources` as input and `docs/build` as output.
- `python3 -m pycommons.dev.building.make_dist --package mypackage` will build the distribution file that can be installed with `pip`.
  It will also offer a requirements file with the list of actually used requirements and generate a `tar.xz` archive with the documentation.
  Its output folder is `dist`.
  The files that it puts into this folder are suitable as attachment for a GitHub release.


### 3.2. The Package: `pycommons.io`
The package [`pycommons.io`](/pycommons/pycommons.io.html) offers several utilities to deal with input and output, most importantly with files and text streams.

The class [`Path`](/pycommons/pycommons.io.html#pycommons.io.path.Path) represents canonical, absolute, and fully-qualified paths in the file system.
It inherits from `str`, which means that you can use it in case of normal strings.
It is also constructed from a string, meaning that you can do `Path("my_path")` and get a canonical path.
The class offers some tools for checking whether a path is a file or directory, reading and writing of data, enforcing that one path contains another one&nbsp(and raising an error otherwise), resolving relative paths inside another directory&nbsp;(and raising an error if the result is not actually "inside"), etc.
Such paths are very convenient, as they are very convenient and always give the canonical information.

The module [`pycommons.io.temp`](/pycommons/pycommons.io.html#module-pycommons.io.temp) builds upon [`Path`](/pycommons/pycommons.io.html#pycommons.io.path.Path) and offers two functions: `temp_dir` and `temp_fil`.
Both return an object which is both a `Path` and a `ContextManager`.
The former returns a path to a newly created temporary directory and the latter a path to a newly created temporary file.
Both can be used inside a `with` statement and their correpsonding directory/file will be deleted automatically at the end of the `with` block.
Below, you can see an example for working with both.
Notice that you can create arbitrary many files and sub-folders inside a temporary directory.
All of them will automatically be deleted recursively when the `with` ends.

```python
from pycommons.io.temp import temp_dir, temp_file

with temp_dir() as td:
    print(f"This is a temporary directory: {td!r}.")
    # Inside this block, you can use the temporary directory.
    # Its fully-qualified path is stored in "td".

# Now the temporary directory and everything inside has been deleted.

with temp_file() as tf:
    print(f"This is a temporary file: {tf!r}.")
    # Inside this block, you can use the temporary file.
    # Its fully-qualified path is stored in "tf".
    
# Now the temporary file has been deleted.
```

The module [`pycommons.io.csv`](https://thomasweise.github.io/pycommons/pycommons.io.html#module-pycommons.io.csv) offers support for reading and writing comma-separated-values&nbsp;(CSV) data.
The API it provides uses generators, i.e., produces iterable streams of either CSV data or of objects parsed from CSV.
It is designed to be extensible:
You can create an implementation for one CSV format and then plug on top an implementation for a CSV format that adds additional columns and so on.
You can also have optional columns.


```python
from pycommons.io.csv import CsvReader

class Reader(CsvReader):
    """
    A little parser that creates dictionaries of rows.
  
    You can, of course, return arbitrary datastructures in
    method `parse_row`.    
    """
    def __init__(self, columns: dict[str, int]) -> None:
        """
        Create the csv reader.

        :param columns: the column name + column index pairs
        """
        super().__init__(columns)
        self.cols = columns
       
    def parse_row(self, data: list[str]) -> dict:
        """
        Parse one row of data.
     
        :param data: the list of column values for the current row
        :returns: the data structured generated to represent the row;
            here: a simple dictionary
        """
        return {x: data[y] for x, y in self.cols.items()}

# Let's test this with some data.
text = ["a;b;c;d", "# test comment", " 1; 2;3;4", " 5 ;6 ", ";8;;9",
        "", "10", "# 11;12"]

# Iterate over the data produced from CSV.
for p in Reader.read(text):
    print(p)
```

The code above will print the following output:

```python
{'a': '1', 'b': '2', 'c': '3', 'd': '4'}
{'a': '5', 'b': '6', 'c': '', 'd': ''}
{'a': '', 'b': '8', 'c': '', 'd': '9'}
{'a': '10', 'b': '', 'c': '', 'd': ''}
```

Now let's test the CSV writing ability:

```python
from typing import Iterable
from pycommons.io.csv import CsvWriter

class Writer(CsvWriter):    
    """A little CSV writer that turns dictionaries into CSV rows."""
    
    def __init__(self, data: Iterable[dict[str, int]],
                 scope: str | None = None) -> None:
        """
        Create the writer for an `Iterable` of data.
        
        :param data: in this case, the data items are dictionaries mapping
            integers to strings, but they could also be other things
        :param scope: an optional column name prefix
        """
        super().__init__(data, scope)
        self.rows = sorted({dkey for datarow in data
                                 for dkey in datarow})
    
    def get_column_titles(self) -> Iterable[str]:
        """Get the column titles."""
        return self.rows
    
    def get_row(self, data: dict[str, int]) -> Iterable[str]:
        """Turn a data item into a string iterable with the column data."""
        return map(str, (data.get(key, "") for key in self.rows))
    
    def get_header_comments(self) -> list[str]:
        """Get comments to be printed at the head."""
        return ["This is a header comment.", " We have two of it. "]

    def get_footer_comments(self) -> list[str]:
        """Get comments for the foot of the document."""
        return [" This is a footer comment."]


# The raw data: Dictionaries to be turned into CSV data.
dd = [{"a": 1, "c": 2}, {"b": 6, "c": 8},
      {"a": 4, "d": 12, "b": 3}, {}]

# Iterate over the produced CSV data and print it.
for p in Writer.write(dd):
    print(p)
```

This will print something like

```
# This is a header comment.
# We have two of it.
a;b;c;d
1;;2
;6;8
4;3;;12
;
# This is a footer comment.
#
# This CSV output has been created using the versatile CSV API of pycommons.io.csv, version 0.8.85.
# You can find pycommons at https://thomasweise.github.io/pycommons.
```

### 3.3. The Package: `pycommons.math`
The package [`pycommons.math`](/pycommons/pycommons.math.html) offers several utilities for mathematics.
Most of them are either centered around combinations of integer and floating point mathematics or statistics.

In the module [`pycommons.math.int_math`](https://thomasweise.github.io/pycommons/pycommons.math.html#module-pycommons.math.int_math), for instance, you can find several routines performing such integer/float related computations.
Take the function [`float_to_frac`](https://thomasweise.github.io/pycommons/pycommons.math.html#pycommons.math.int_math.float_to_frac) for example:
Python's [`float.as_integer_ration`](https://docs.python.org/3/library/stdtypes.html#float.as_integer_ratio) converts a floating point number to a ratio of two integer values by working directly on the binary representation of the `float`.
Therefore, `0.1.as_integer_ratio()` will produce `(3602879701896397, 36028797018963968)`, because `0.1` cannot exactly be represented in the dual system and this is what its binary approximation corresponds to.
`float_to_frac(0.1)` however produces `(1, 10)`, because it attempts several different avenues to convert the floating point value and chooses the most compact equivalent representation.
It is slower, but more natural.

There are several routines like [`try_int_add`](https://thomasweise.github.io/pycommons/pycommons.math.html#pycommons.math.int_math.try_int_add), [`try_int_mul`](https://thomasweise.github.io/pycommons/pycommons.math.html#pycommons.math.int_math.try_int_mul), and [`try_int_div`](https://thomasweise.github.io/pycommons/pycommons.math.html#pycommons.math.int_math.try_int_div), which attempt to perform arithmetics as precisely as possible if one (the second) of the two operands is a `float`.
You see, in Python, if you add an `int` and a `float`, the result is always a `float`.
But consider this:

```python
from pycommons.math.int_math import try_int_add

big_int = 1_234_567_890_123_456_789_012_345_678_901_234_567_890_123_456_789

print(f"{big_int + 0.5 = }")
print(f"{try_int_add(big_int, 0.5) = }")
```

This code prints:

```
big_int + 0.5 = 1.2345678901234568e+48
try_int_add(big_int, 0.5) = 1234567890123456789012345678901234567890123456790
```

The expression in the first `print` converted the integer to a floating point number.
`1.2345678901234568e+48` is as exact as a `float` can represent the big integer number.
But it clearly cuts off a lot of decimals.
Actually, because of that, the exact value of that `float` is much much farther away from the "true" value that `big_int + 0.5` really has than `big_int` itself.
However, the function `try_int_add` does realize this.
It returns the integer value shown above, which is only `0.5` away from the "true" value.
Sometimes, if we just discard the fractional part of a `float` and instead only work with the (rounded) integer values, we can be more accurate than trying to do all computations in the `float` domain.
Well, such approaches might be frowned upon by real mathematicians.
But I use it as foundation for some of my other maths-related tools.


### 3.4. Data Structures: `pycommons.ds`
Some very simple datastructures are provided in the package [`pycommons.ds`](/pycommons/pycommons.ds.html), but nothing special.
The function `is_new` creates a new function which returns `True` if it sees its argument for the first time, and `False` otherwise. 
The code below prints `True`, `True`, `False`, `True`, and `False`.

```python
from typing import Callable
from pycommons.ds.cache import is_new

cache: Callable[[str], bool] = is_new()
print(cache("1"))
print(cache("2"))
print(cache("1"))
print(cache("3"))
print(cache("2"))
```

The function `repr_cache` uses the `repr`-string representation of objects as keys to store the objects.
When an object is passed to it for the first time, it returns the object.
If an object with the same string `repr`-representation is passed to it, it returns the object originally stored under that string representation.
The code below prints `{1: '1', 3: '3', 7: '7'}`, `True`, `True`, and `False`.

```python
from typing import Callable
from pycommons.ds.cache import repr_cache

cache: Callable[[dict[int, str]], dict[int, str]] = repr_cache()
a = {1: '1', 3: '3', 7: '7'}
b = {1: '1', 3: '3', 7: '7'}
print(cache(a))
print(cache(a) is a)
print(cache(b) is a)
print(cache(b) is b)
```

The function `immutable_mapping` creates and `Mapping` which wraps some other mapping, such as a dictionary, and provides an immutable view on it.
This can be used in cases where you want to create global variables that hold dictionaries or pass dictionaries to functions but want to prevent these dictionaries from being changed.
The code below prints `'mappingproxy' object does not support item assignment` and `2`.

```python
from typing import Mapping
from pycommons.ds.immutable_map import immutable_mapping

imap: Mapping[int, int] = immutable_mapping({1: 2, 3: 4})
try:
    imap[1] = 3
except TypeError as te:
    print(te)

print(imap[1])
```

The function `reiterable` takes an `Iterator`, i.e., a sequence that can be processed exactly once, and turns it into a sequence that can be processed multiple times, i.e., a fully-fledged `Iterable`.
It does so by caching the values returned by the original `Iterator` when we pass over it for the first time.
The `iter` function of Python turns a sequence into an `Iterator` which can be passed over exactly once.
However, by wrapping the result of `iter(range(4))` into a `reiterable` named `ri`, we can go over `ri` twice (and, actually, as many times as we want) in the code below.
It will therefore print the numbers from `0` to `4` multiple times.

```python
from pycommons.ds.sequences import reiterable

ri = reiterable(iter(range(4)))
for i in ri:
    print(i)
for i in ri:
    print(i)
```

## 4. License
[`pycommons`](https://thomasweise.github.io/pycommons) is a library with utilities for Python projects.

Copyright (C) 2024-2026 [Thomas Weise](https://thomasweise.github.io)&nbsp;(汤卫思教授)

Dr. [Thomas Weise](https://thomasweise.github.io)&nbsp;(see [Contact](#5-contact)) holds the copyright of this package.

`pycommons` is provided to the public as open source software under the [GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007](https://thomasweise.github.io/pycommons/LICENSE.html).
Terms for other licenses, e.g., for specific industrial applications, can be negotiated with Dr. Thomas Weise (who can be reached via the [contact information](#5-contact) below).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Please visit the [contributions guidelines](https://thomasweise.github.io/pycommons/CONTRIBUTING_md.html) for `pycommons` if you would like to contribute to our package.
If you have any concerns regarding security, please visit our [security policy](https://thomasweise.github.io/pycommons/SECURITY_md.html).


## 5. Contact
If you have any questions or suggestions, please contact
Prof. Dr. [Thomas Weise](https://thomasweise.github.io) (汤卫思教授) of the 
School of Artificial Intelligence and Big Data&nbsp;([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd)) at
[Hefei University](http://www.hfuu.edu.cn/english)&nbsp;([合肥大学](http://www.hfuu.edu.cn)) in
Hefei, Anhui, China&nbsp;(中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
