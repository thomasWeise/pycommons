"""The project build information."""
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Final

from pycommons.io.path import Path, directory_path
from pycommons.types import type_error


@dataclass(frozen=True, init=False, order=False, eq=False)
class BuildInfo:
    """
    A class that represents information about building a project.

    >>> b = BuildInfo(Path(__file__).up(4), "pycommons", "tests", "examples")
    >>> b.base_dir == Path(__file__).up(4)
    True
    >>> b.package_name
    'pycommons'
    >>> b.examples_dir_name
    'examples'
    >>> b.tests_dir_name
    'tests'
    >>> b.sources_dir.endswith('pycommons')
    True
    >>> b.examples_dir.endswith('examples')
    True
    >>> b.tests_dir.endswith('tests')
    True

    >>> try:
    ...     BuildInfo(None, "pycommons")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     BuildInfo(1, "pycommons")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "")
    ... except ValueError as ve:
    ...     print(ve)
    Relative path must not be empty.

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), ".")
    ... except ValueError as ve:
    ...     print(str(ve)[:32])
    Inconsistent directories ['.', '

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "..")
    ... except ValueError as ve:
    ...     print("does not contain" in str(ve))
    True

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", "..")
    ... except ValueError as ve:
    ...     print("does not contain" in str(ve))
    True

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", ".")
    ... except ValueError as ve:
    ...     print(str(ve)[:32])
    Inconsistent directories ['.', '

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", None, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", None, "..")
    ... except ValueError as ve:
    ...     print("does not contain" in str(ve))
    True

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", None, ".")
    ... except ValueError as ve:
    ...     print(str(ve)[:32])
    Inconsistent directories ['.', '
    """

    #: the path to the project base directory
    base_dir: Path
    #: the name of the project / package
    package_name: str
    #: the path to the directory with the package sources
    sources_dir: Path
    #: the name of the tests directory, if any
    tests_dir_name: str | None
    #: the path to the tests directory, if any
    tests_dir: Path | None
    #: the name of the examples directory, if any
    examples_dir_name: str | None
    #: the path to the examples directory, if any
    examples_dir: Path | None

    def __init__(self, base_dir: str,
                 package_name: str,
                 tests_name: str | None = None,
                 examples_name: str | None = None) -> None:
        """
        Create the build information class.

        :param base_dir: the base directory of the project
        :param package_name: the package name
        :param tests_name: the name of the tests folder, if any
        :param examples_name: the name of the examples folder, if any
        """
        object.__setattr__(self, "base_dir", directory_path(base_dir))
        object.__setattr__(self, "package_name", str.strip(package_name))
        object.__setattr__(self, "sources_dir", directory_path(
            self.base_dir.resolve_inside(self.package_name)))
        object.__setattr__(
            self, "tests_dir_name",
            None if tests_name is None else str.strip(tests_name))
        object.__setattr__(
            self, "tests_dir",
            None if self.tests_dir_name is None else directory_path(
                self.base_dir.resolve_inside(self.tests_dir_name)))
        object.__setattr__(
            self, "examples_dir_name",
            None if examples_name is None else str.strip(examples_name))
        object.__setattr__(
            self, "examples_dir",
            None if self.examples_dir_name is None else directory_path(
                self.base_dir.resolve_inside(self.examples_dir_name)))
        n: int = 3
        dirs: set[str] = {self.base_dir, self.sources_dir, self.package_name}
        if self.examples_dir is not None:
            dirs.add(self.examples_dir)
            dirs.add(self.examples_dir_name)  # type: ignore
            n += 2
        if self.tests_dir is not None:
            dirs.add(self.tests_dir)
            dirs.add(self.tests_dir_name)  # type: ignore
            n += 2
        if set.__len__(dirs) != n:
            raise ValueError(f"Inconsistent directories {sorted(dirs)!r}.")

    def __str__(self) -> str:
        """
        Convert this object to a string.

        :return: the string version of this object.

        >>> str(BuildInfo(Path(__file__).up(4), "pycommons"))[:16]
        "'pycommons' in '"
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", "tests"))[-30:]
        "' with tests in folder 'tests'"
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", "tests",
        ...         "examples"))[-51:]
        "in folder 'tests' and examples in folder 'examples'"
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", None,
        ...         "examples"))[-45:]
        "pycommons' with examples in folder 'examples'"
        """
        text: str = f"{self.package_name!r} in {self.base_dir!r}"
        concat: str = " with "
        if self.tests_dir_name is not None:
            text = f"{text}{concat}tests in folder {self.tests_dir_name!r}"
            concat = " and "
        if self.examples_dir_name is not None:
            text = (f"{text}{concat}examples in "
                    f"folder {self.examples_dir_name!r}")
        return text


def parse_project_arguments(parser: ArgumentParser) -> BuildInfo:
    """
    Load project information arguments from the command line.

    :param parser: the argument parser

    >>> try:
    ...     parse_project_arguments(None)
    ... except TypeError as te:
    ...     print(te)
    parser should be an instance of argparse.ArgumentParser but is None.

    >>> try:
    ...     parse_project_arguments(1)
    ... except TypeError as te:
    ...     print(str(te)[:40])
    parser should be an instance of argparse
    """
    if not isinstance(parser, ArgumentParser):
        raise type_error(parser, "parser", ArgumentParser)
    parser.add_argument(
        "--root", help="the project root directory", type=Path, nargs="?",
        default=".")
    parser.add_argument(
        "--package", help="the name of the package folder", type=str)
    parser.add_argument(
        "--tests", help="the name of the tests folder, if any",
        nargs="?", default=None)
    parser.add_argument(
        "--examples", help="the name of the examples folder, if any ",
        nargs="?", default=None)
    args: Final[Namespace] = parser.parse_args()
    return BuildInfo(args.root, args.package, args.tests, args.examples)
