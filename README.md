[![make build](https://github.com/thomasWeise/pycommons/actions/workflows/build.yml/badge.svg)](https://github.com/thomasWeise/pycommons/actions/workflows/build.yml)
[![pypi version](https://img.shields.io/pypi/v/pycommons)](https://pypi.org/project/pycommons)
[![pypi downloads](https://img.shields.io/pypi/dw/pycommons.svg)](https://pypistats.org/packages/pycommons)
[![coverage report](https://thomasweise.github.io/pycommons/tc/badge.svg)](https://thomasweise.github.io/pycommons/tc/index.html)
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

In order to use this package, you need to first install it using [`pip`](https://pypi.org/project/pip/) or some other tool that can install packages from [PyPi](https://pypi.org).
You can install the newest version of this library from [PyPi](https://pypi.org/project/pycommons/) using [`pip`](https://pypi.org/project/pip/) by doing

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

### 3.1. Data Structures

Some very simple datastructures are provided, but nothing special.
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

Copyright (C) 2024  Thomas Weise (汤卫思教授)

Dr. Thomas Weise (see [Contact](#5-contact)) holds the copyright of this package.

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
Prof. Dr. Thomas Weise (汤卫思教授) of the 
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd/)) at
[Hefei University](http://www.hfuu.edu.cn/english/) ([合肥大学](http://www.hfuu.edu.cn/)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
