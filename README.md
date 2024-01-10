[![make build](https://github.com/thomasWeise/pycommons/actions/workflows/build.yaml/badge.svg)](https://github.com/thomasWeise/pycommons/actions/workflows/build.yaml)
[![pypi version](https://img.shields.io/pypi/v/pycommons)](https://pypi.org/project/pycommons)
[![pypi downloads](https://img.shields.io/pypi/dw/pycommons.svg)](https://pypistats.org/packages/pycommons)
[![coverage report](https://thomasweise.github.io/pycommons/tc/badge.svg)](https://thomasweise.github.io/pycommons/tc/index.html)

# pycommons: Common Utility Functions for Python Projects.

Some common utility functionality for Python projects.


## 1. Introduction

In this project, we combine several utilities and functions that are used in our other projects.


## 2. Installation

In order to use this package, you need to first install it using [`pip`](https://pypi.org/project/pip/) or some other tool that can install packages from [PyPi](https://pypi.org).
You can install the newest version of this library from [PyPi](https://pypi.org/project/pycommons/) using [`pip`](https://pypi.org/project/pip/) by doing

```shell
pip install pycommons
```

This will install the latest official release of our package as well as [all dependencies](https://thomasweise.github.io/pycommons/requirements.html).
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

You can also clone the repository and then run a [`make` build](https://thomasweise.github.io/pycommons/Makefile.html), which will automatically install all dependencies, run all the tests, and then install the package on your system, too.
This will work only on Linux, though.
It also installs the [dependencies for building](https://thomasweise.github.io/pycommons/requirements-dev.html), which include, e.g., those for [unit testing and static analysis](#81-unit-tests-and-static-analysis).
If this build completes successful, you can be sure that [`pycommons`](https://thomasweise.github.io/pycommons) will work properly on your machine.

All dependencies for using and running `pycommons` are listed at [here](https://thomasweise.github.io/pycommons/requirements.html).
The additional dependencies for a [full `make` build](https://thomasweise.github.io/pycommons/Makefile.html), including unit tests, static analysis, and the generation of documentation are listed [here](https://thomasweise.github.io/pycommons/requirements-dev.html).


## 3. License

[`pycommons`](https://thomasweise.github.io/pycommons) is a library with utilities for Python projects.

Copyright (C) 2024  [Thomas Weise](http://iao.hfuu.edu.cn/5) (汤卫思教授)

Dr. Thomas Weise (see [Contact](#4-contact)) holds the copyright of this package.

`pycommons` is provided to the public as open source software under the [GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007](https://thomasweise.github.io/pycommons/LICENSE.html).
Terms for other licenses, e.g., for specific industrial applications, can be negotiated with Dr. Thomas Weise (who can be reached via the [contact information](#12-contact) below).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Please visit the [contributions guidelines](https://thomasweise.github.io/pycommons/CONTRIBUTING.html) for `pycommons` if you would like to contribute to our package.
If you have any concerns regarding security, please visit our [security policy](https://thomasweise.github.io/pycommons/SECURITY.html).


## 4. Contact

If you have any questions or suggestions, please contact
Prof. Dr. [Thomas Weise](http://iao.hfuu.edu.cn/5) (汤卫思教授) of the 
Institute of Applied Optimization (应用优化研究所, [IAO](http://iao.hfuu.edu.cn)) of the
School of Artificial Intelligence and Big Data ([人工智能与大数据学院](http://www.hfuu.edu.cn/aibd/)) at
[Hefei University](http://www.hfuu.edu.cn/english/) ([合肥大学](http://www.hfuu.edu.cn/)) in
Hefei, Anhui, China (中国安徽省合肥市) via
email to [tweise@hfuu.edu.cn](mailto:tweise@hfuu.edu.cn) with CC to [tweise@ustc.edu.cn](mailto:tweise@ustc.edu.cn).
