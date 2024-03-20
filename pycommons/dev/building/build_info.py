"""The project build information."""
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Final, Iterable

from pycommons.io.path import Path, directory_path
from pycommons.processes.shell import STREAM_FORWARD, Command
from pycommons.types import check_int_range, type_error


@dataclass(frozen=True, init=False, order=False, eq=False)
class BuildInfo:
    """
    A class that represents information about building a project.

    >>> b = BuildInfo(Path(__file__).up(4), "pycommons", "tests", "examples",
    ...         "docs/source", "docs/build", "dist")
    >>> b.base_dir == Path(__file__).up(4)
    True
    >>> b.package_name
    'pycommons'
    >>> b.sources_dir.endswith('pycommons')
    True
    >>> b.examples_dir.endswith('examples')
    True
    >>> b.tests_dir.endswith('tests')
    True
    >>> b.doc_source_dir.endswith('source')
    True
    >>> b.doc_dest_dir.endswith('build')
    True
    >>> b.dist_dir.endswith('dist')
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
    ...     print(str(ve)[:27])
    Inconsistent directories ['

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
    ...     print(str(ve)[:27])
    Inconsistent directories ['

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", doc_source_dir=1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", doc_dest_dir=1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons", dist_dir=1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     BuildInfo(Path(__file__).up(4), "pycommons",
    ...          doc_source_dir="docs", doc_dest_dir="docs/build")
    ... except ValueError as ve:
    ...     print(str(ve)[:20])
    Nested directories '
    """

    #: the path to the project base directory
    base_dir: Path
    #: the name of the project / package
    package_name: str
    #: the path to the directory with the package sources
    sources_dir: Path
    #: the path to the tests directory, if any
    tests_dir: Path | None
    #: the path to the examples directory, if any
    examples_dir: Path | None
    #: the source directory for documentation
    doc_source_dir: Path | None
    #: the destination directory for documentation
    doc_dest_dir: Path | None
    #: the directory where the distribution files should be located
    dist_dir: Path | None
    #: the standard timeout
    timeout: int

    def __init__(self, base_dir: str,
                 package_name: str,
                 tests_dir: str | None = None,
                 examples_dir: str | None = None,
                 doc_source_dir: str | None = None,
                 doc_dest_dir: str | None = None,
                 dist_dir: str | None = None,
                 timeout: int = 3600) -> None:
        """
        Create the build information class.

        :param base_dir: the base directory of the project
        :param package_name: the package name
        :param tests_dir: the tests folder, if any
        :param examples_dir: the examples folder, if any
        :param doc_source_dir: the documentation source directory, if any
        :param doc_dest_dir: the documentation destination directory, if any
        :param dist_dir: the distribution directory, if any
        :param timeout: the standard timeout
        """
        object.__setattr__(self, "base_dir", directory_path(base_dir))
        object.__setattr__(self, "package_name", str.strip(package_name))
        object.__setattr__(self, "sources_dir", directory_path(
            self.base_dir.resolve_inside(self.package_name)))
        object.__setattr__(
            self, "tests_dir",
            None if tests_dir is None else directory_path(
                self.base_dir.resolve_inside(str.strip(tests_dir))))
        object.__setattr__(
            self, "examples_dir",
            None if examples_dir is None else directory_path(
                self.base_dir.resolve_inside(str.strip(examples_dir))))
        object.__setattr__(
            self, "doc_source_dir", None if doc_source_dir is None
            else directory_path(self.base_dir.resolve_inside(
                str.strip(doc_source_dir))))
        object.__setattr__(
            self, "doc_dest_dir", None if doc_dest_dir is None
            else self.base_dir.resolve_inside(str.strip(doc_dest_dir)))
        object.__setattr__(
            self, "dist_dir", None if dist_dir is None
            else self.base_dir.resolve_inside(str.strip(dist_dir)))
        n: int = 3
        dirs: set[str] = {self.base_dir, self.sources_dir, self.package_name}
        if self.examples_dir is not None:
            dirs.add(self.examples_dir)
            n += 1
        if self.tests_dir is not None:
            dirs.add(self.tests_dir)
            n += 1
        if self.doc_source_dir is not None:
            dirs.add(self.doc_source_dir)
            n += 1
        if self.doc_dest_dir is not None:
            dirs.add(self.doc_dest_dir)
            n += 1
        if self.dist_dir is not None:
            dirs.add(self.dist_dir)
            n += 1
        if set.__len__(dirs) != n:
            raise ValueError(f"Inconsistent directories {sorted(dirs)!r}.")

        dirs.remove(self.base_dir)
        sel: list[Path] = [p for p in dirs if isinstance(p, Path)]
        for i, p1 in enumerate(sel):
            for j in range(i + 1, list.__len__(sel)):
                p2 = sel[j]
                if p1.contains(p2) or p2.contains(p1):
                    raise ValueError(
                        f"Nested directories {p1!r} and {p2!r}.")

        object.__setattr__(
            self, "timeout", check_int_range(
                timeout, "timeout", 1, 1_000_000_000))

    def __str__(self) -> str:
        r"""
        Convert this object to a string.

        :return: the string version of this object.

        >>> str(BuildInfo(Path(__file__).up(4), "pycommons"))[:15]
        "'pycommons' in "
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", "tests"))[-31:]
        ', and per-step timeout is 3600s'
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", "tests",
        ...         "examples"))[-51:]
        "amples in 'examples', and per-step timeout is 3600s"
        >>> str(BuildInfo(Path(__file__).up(4), "pycommons", None,
        ...         "examples"))[-35:]
        "les', and per-step timeout is 3600s"
        >>> for f in str(BuildInfo(Path(__file__).up(4), "pycommons", None,
        ...     doc_dest_dir="docs/build", doc_source_dir="docs/source",
        ...     dist_dir="dist")).split("'")[2::2]:
        ...     print(str.strip(f))
        in
        , documentation sources in
        , documentation destination in
        , distribution destination is
        , and per-step timeout is 3600s
        """
        text: str = f"{self.package_name!r} in {self.base_dir!r}"
        dirs: list[str] = []
        if self.tests_dir is not None:
            dirs.append(
                f"tests in {self.tests_dir.relative_to(self.base_dir)!r}")
        if self.examples_dir is not None:
            dirs.append(f"examples in "
                        f"{self.examples_dir.relative_to(self.base_dir)!r}")
        if self.doc_source_dir is not None:
            dirs.append(f"documentation sources in "
                        f"{self.doc_source_dir.relative_to(self.base_dir)!r}")
        if self.doc_dest_dir is not None:
            dirs.append(f"documentation destination in "
                        f"{self.doc_dest_dir.relative_to(self.base_dir)!r}")
        if self.dist_dir is not None:
            dirs.append(f"distribution destination is "
                        f"{self.dist_dir.relative_to(self.base_dir)!r}")
        dirs.append(f"per-step timeout is {self.timeout}s")
        n: Final[int] = list.__len__(dirs)
        if n == 1:
            return f"{text} and {dirs[0]}"
        dirs[-1] = f"and {dirs[-1]}"
        dirs.insert(0, text)
        return ", ".join(dirs)

    def command(self, args: Iterable[str]) -> Command:
        """
        Create a typical build step command.

        :param args: the arguments of the command

        >>> b = BuildInfo(Path(__file__).up(4), "pycommons")
        >>> cmd = b.command(("cat", "README.txt"))
        >>> cmd.working_dir == b.base_dir
        True
        >>> cmd.command
        ('cat', 'README.txt')
        >>> cmd.timeout
        3600
        >>> cmd.stderr == STREAM_FORWARD
        True
        >>> cmd.stdout == STREAM_FORWARD
        True
        >>> cmd.timeout
        3600
        """
        return Command(args, working_dir=self.base_dir, timeout=self.timeout,
                       stderr=STREAM_FORWARD, stdout=STREAM_FORWARD)


def parse_project_arguments(parser: ArgumentParser,
                            args: list[str] | None = None) -> BuildInfo:
    """
    Load project information arguments from the command line.

    :param parser: the argument parser
    :param args: the command line arguments

    >>> from pycommons.io.arguments import pycommons_argparser
    >>> ap = pycommons_argparser(__file__, "a test program",
    ...     "An argument parser for testing this function.")
    >>> ee = parse_project_arguments(ap, ["--root", Path(__file__).up(4),
    ...                              "--package", "pycommons"])
    >>> ee.package_name
    'pycommons'
    >>> ee.sources_dir.endswith("pycommons")
    True
    >>> ee.dist_dir.endswith("dist")
    True
    >>> ee.doc_source_dir.endswith("docs/source")
    True
    >>> ee.doc_dest_dir.endswith("docs/build")
    True
    >>> ee.examples_dir.endswith("examples")
    True
    >>> ee.tests_dir.endswith("tests")
    True

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
        "--tests",
        help="the relative path to the tests folder, if any",
        nargs="?", default=None)
    parser.add_argument(
        "--examples",
        help="the relative path to the examples folder, if any ",
        nargs="?", default=None)
    parser.add_argument(
        "--doc-src", help="the relative path to the documentation"
                          " source, if any ",
        nargs="?", default=None)
    parser.add_argument(
        "--doc-dst", help="the relative path to the documentation"
                          " destination, if any ",
        nargs="?", default=None)
    parser.add_argument(
        "--dist", help="the relative path to the distribution, if any ",
        nargs="?", default=None)
    parser.add_argument(
        "--timeout", help="the per-step timeout", type=int,
        nargs="?", default=3600)
    res: Final[Namespace] = parser.parse_args(args)

    root: Final[Path] = directory_path(res.root)
    pack: Final[str] = str.strip(str.strip(res.package))
    done: Final[set[str | None]] = {root, pack}

    tests: str | None = res.tests
    if (tests is None) and ("tests" not in done) and (
            root.resolve_inside("tests").is_dir()):
        tests = "tests"
    done.add(tests)

    examples: str | None = res.examples
    if (examples is None) and ("examples" not in done) and (
            root.resolve_inside("examples").is_dir()):
        examples = "examples"
    done.add(examples)

    doc_src: str | None = res.doc_src
    doc_dir: Path | None = None
    if (doc_src is None) and ("docs/source" not in done):
        doc_dir = root.resolve_inside("docs")
        if doc_dir.is_dir() and (doc_dir.resolve_inside("source").is_dir()):
            doc_src = "docs/source"
    done.add(doc_src)

    doc_dst: str | None = res.doc_dst
    if (doc_dst is None) and ("docs/build" not in done):
        if doc_dir is None:
            doc_dir = root.resolve_inside("docs")
        if doc_dir.is_dir() and (doc_dir.resolve_inside(
                "build").is_dir() or (doc_src == "docs/source")):
            doc_dst = "docs/build"
    done.add(doc_dst)

    dist: str | None = res.dist
    if (dist is None) and ("dist" not in done):
        ddd = root.resolve_inside("dist")
        if (not ddd.exists()) or ddd.is_dir():
            dist = "dist"

    return BuildInfo(root, pack, tests, examples, doc_src, doc_dst, dist,
                     res.timeout)


def replace_in_cmd(orig: Iterable[str], replace_with: str,
                   replace_what: str = ".") -> Iterable[str]:
    """
    Replace the occurrences of `replace_what` with `replace_with`.

    :param orig: the original sequence
    :param replace_with: the string it is to be replace with
    :param replace_what: the string to be replaced
    :return: the replaced sequence

    >>> replace_in_cmd(('x', '.', 'y'), 'a', '.')
    ['x', 'a', 'y']
    >>> replace_in_cmd(('x', '.', 'y'), 'a')
    ['x', 'a', 'y']

    >>> try:
    ...     replace_in_cmd(None, 'a', '.')
    ... except TypeError as te:
    ...     print(te)
    orig should be an instance of typing.Iterable but is None.

    >>> try:
    ...     replace_in_cmd(1, 'a', '.')
    ... except TypeError as te:
    ...     print(te)
    orig should be an instance of typing.Iterable but is int, namely '1'.

    >>> try:
    ...     replace_in_cmd([], 'a', '.')
    ... except ValueError as ve:
    ...     print(ve)
    Did not find '.'.

    >>> try:
    ...     replace_in_cmd(['x'], 'a', '.')
    ... except ValueError as ve:
    ...     print(ve)
    Did not find '.'.

    >>> try:
    ...     replace_in_cmd(['x'], 'a')
    ... except ValueError as ve:
    ...     print(ve)
    Did not find '.'.

    >>> try:
    ...     replace_in_cmd(['x'], None, '.')
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     replace_in_cmd(['x'], 1, '.')
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     replace_in_cmd(['x'], '', '.')
    ... except ValueError as ve:
    ...     print(ve)
    Invalid replace_with ''.

    >>> try:
    ...     replace_in_cmd(['x'], 'y', None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     replace_in_cmd(['x'], 'y', 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     replace_in_cmd(['x'], 'x', '')
    ... except ValueError as ve:
    ...     print(ve)
    Invalid replace_what ''.
    """
    if not isinstance(orig, Iterable):
        raise type_error(orig, "orig", Iterable)
    if str.__len__(replace_with) <= 0:
        raise ValueError(f"Invalid replace_with {replace_with!r}.")
    if str.__len__(replace_what) <= 0:
        raise ValueError(f"Invalid replace_what {replace_what!r}.")
    result: list[str] = []
    found: bool = False
    for k in orig:
        if k == replace_what:
            found = True
            result.append(replace_with)
        else:
            result.append(k)
    if not found:
        raise ValueError(f"Did not find {replace_what!r}.")
    return result
