"""Create the documentation."""

from argparse import ArgumentParser
from typing import Callable, Final, cast

import minify_html

from pycommons.dev.building.build_info import (
    BuildInfo,
    parse_project_arguments,
)
from pycommons.dev.doc.doc_info import (
    DocInfo,
    extract_md_infos,
    load_doc_info_from_setup_cfg,
)
from pycommons.dev.url_replacer import make_url_replacer
from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.io.path import Path, delete_path
from pycommons.processes.python import PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_CAPTURE, STREAM_FORWARD, Command
from pycommons.types import type_error


def __get_source(
        source: Path, __dst: set[Path] | None = None) \
        -> Callable[[Path], bool]:
    """
    Get the existing files in a directory.

    :param source: the directory
    :param __dst: the destination
    :return: the set of files

    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     f1 = td.resolve_inside("a")
    ...     f1.ensure_file_exists()  # gives False
    ...     f2 = td.resolve_inside("b")
    ...     f2.ensure_file_exists()  # gives False
    ...     d = td.resolve_inside("x")
    ...     d.ensure_dir_exists()  # gives False
    ...     f3 = d.resolve_inside("a")
    ...     f3.ensure_file_exists()
    ...     g = __get_source(td)
    ...     g(f1)  # is True
    ...     g(f2)  # is True
    ...     g(f3)  # is True
    ...     g(d)  # is True
    ...     g("bla")  # is not True
    ...     f4 = d.resolve_inside("x")
    ...     f4.ensure_file_exists()  # gives False
    ...     g(f4)  # is also not True, because generated later
    False
    False
    False
    True
    True
    True
    True
    False
    False
    False
    """
    if __dst is None:
        __dst = {source}
    for k in source.list_dir():
        __dst.add(k)
        if k.is_dir():
            __get_source(k, __dst)
    return __dst.__contains__


def __keep_only_source(
        source: Path, keep: Callable[[Path], bool],
        __collect: Callable[[Path], None] | None = None) -> None:
    """
    Keep only the source items, delete the rest.

    :param source: the source path
    :param keep: the set of files and directories to keep
    :param __collect: the collector

    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     f1 = td.resolve_inside("a")
    ...     f1.ensure_file_exists()  # gives False
    ...     f2 = td.resolve_inside("b")
    ...     f2.ensure_file_exists()  # gives False
    ...     d = td.resolve_inside("x")
    ...     d.ensure_dir_exists()  # gives False
    ...     f3 = d.resolve_inside("a")
    ...     f3.ensure_file_exists()
    ...     g = __get_source(td)
    ...     f4 = d.resolve_inside("x")
    ...     f4.ensure_file_exists()  # gives False
    ...     e = td.resolve_inside("y")
    ...     e.ensure_dir_exists()  # gives False
    ...     f5 = e.resolve_inside("a")
    ...     f5.ensure_file_exists()
    ...     f3.is_file()  # gives True - should be preserved
    ...     f4.is_file()  # gives True - will be deleted
    ...     f5.is_file()  # gives True - will be deleted
    ...     d.is_dir()  # True - will be preserved
    ...     e.is_dir()  # True - will be deleted
    ...     __keep_only_source(td, g)
    ...     f3.is_file()  # gives True - was preserved
    ...     f4.is_file()  # gives False
    ...     f5.is_file()  # gives False
    ...     d.is_dir()  # True - was preserved
    ...     e.is_dir()  # False
    False
    False
    False
    False
    False
    True
    True
    True
    True
    True
    True
    False
    False
    True
    False
    """
    lst: list[Path] | None = None
    if __collect is None:
        lst = []
        __collect = lst.append
    for f in source.list_dir():
        if not keep(f):
            __collect(f)
        if f.is_dir():
            __keep_only_source(f, keep, __collect)
    if lst:
        lst.sort(key=cast(Callable[[Path], int], str.__len__), reverse=True)
        for k in lst:
            delete_path(k)


def __pygmentize(source: Path, info: BuildInfo,
                 dest: Path | None = None) -> None:
    """
    Pygmentize a source file to a destination.

    :param source: the source file
    :param info: the information
    :param dest: the destination folder

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))

    >>> from contextlib import redirect_stdout
    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     with redirect_stdout(None):
    ...         __pygmentize(root.resolve_inside("README.md"), bf, td)
    ...         readme = td.resolve_inside("README_md.html").is_file()
    ...         __pygmentize(root.resolve_inside("setup.py"), bf, td)
    ...         setuppy = td.resolve_inside("setup_py.html").is_file()
    ...         __pygmentize(root.resolve_inside("setup.cfg"), bf, td)
    ...         setup_cfg = td.resolve_inside("setup_cfg.html").is_file()
    ...         __pygmentize(root.resolve_inside("Makefile"), bf, td)
    ...         makefile = td.resolve_inside("Makefile.html").is_file()
    ...         __pygmentize(root.resolve_inside("LICENSE"), bf, td)
    ...         xlicense = td.resolve_inside("LICENSE.html").is_file()
    ...         __pygmentize(root.resolve_inside("requirements.txt"), bf, td)
    ...         req = td.resolve_inside("requirements_txt.html").is_file()
    ...         try:
    ...             __pygmentize(root.resolve_inside("LICENSE"), bf, td)
    ...         except ValueError as ve:
    ...             ver = str(ve)
    >>> readme
    True
    >>> setuppy
    True
    >>> setup_cfg
    True
    >>> makefile
    True
    >>> xlicense
    True
    >>> req
    True
    >>> "already exists" in ver
    True
    """
    logger(f"Trying to pygmentize {source!r} to {dest!r}.")
    name: Final[str] = source.basename()
    language: str = "text"
    if name.endswith(".py"):
        language = "python3"
    elif name.endswith((".cfg", ".toml")):
        language = "INI"
    elif name.lower() == "makefile":
        language = "make"
    if dest is None:
        dest = info.doc_dest_dir
    dest_file: Final[Path] = dest.resolve_inside(
        f"{name.replace('.', '_')}.html")
    if dest_file.exists():
        raise ValueError(f"File {dest_file!r} already exists, "
                         f"cannot pygmentize {source!r}.")
    info.command(("pygmentize", "-f", "html", "-l", language, "-O", "full",
                  "-O", "style=default", "-o", dest_file, source)).execute()
    logger(f"Done pygmentizing {source!r} to {dest_file!r}.")


#: the default files to pygmentize
__PYGMENTIZE_DEFAULT: Final[tuple[str, ...]] = (
    "conftest.py", "LICENSE", "Makefile", "pyproject.toml",
    "requirements.txt", "requirements-dev.txt", "setup.cfg", "setup.py",
)

#: the possible styles
__STYLES: Final[tuple[str, ...]] = ("bizstyle.css", )

#: the html header
__HTML_HEADER: Final[str] = "<!DOCTYPE html><html><title>"
#: the top of the html body if styles are present
__HTML_BODY_STYLE_1: Final[str] =\
    ('</title><link href={STYLE} rel="stylesheet">'
     '<body style="background-image:none"><div class="document">'
     '<div class="documentwrapper"><div class="bodywrapper">'
     '<div class="body" role="main"><section>')
#: the bottom of the html body if styles are present
__HTML_BODY_STYLE_2: Final[str] = \
    "</section></div></div></div></div></body></html>"
#: the top of the html body if not styles are present
__HTML_BODY_NO_STYLE_1: Final[str] = "</title><body><section>"
#: the bottom of the html body if styles are present
__HTML_BODY_NO_STYLE_2: Final[str] = "</section></body></html>"


def __render_markdown(markdown: Path, info: BuildInfo, dest: Path | None,
                      css: str | None,
                      url_fixer: Callable[[str], str]) -> None:
    """
    Render a markdown file.

    :param markdown: the markdown file
    :param dest: the destination path
    :param info: the build info
    :param css: the relative path to the style sheet
    :param url_fixer: the URL fixer

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     with redirect_stdout(None):
    ...         __render_markdown(root.resolve_inside("README.md"), bf,
    ...             td, None, lambda s: s)
    ...         readme = td.resolve_inside("README_md.html").is_file()
    ...         try:
    ...             __render_markdown(root.resolve_inside("README.md"), bf,
    ...                 td, None, lambda s: s)
    ...         except ValueError as ve:
    ...             vstr = str(ve)
    ...         __render_markdown(root.resolve_inside("CONTRIBUTING.md"), bf,
    ...             td, "dummy.css", lambda s: s)
    ...         cb = td.resolve_inside("CONTRIBUTING_md.html").is_file()
    >>> readme
    True
    >>> vstr.endswith("already exists.")
    True
    >>> cb
    True
    """
    logger(f"Trying to render {markdown!r}.")

    # find the destination file
    basename: Final[str] = markdown.basename()
    if dest is None:
        dest = info.doc_dest_dir
    dest_path: Final[Path] = dest.resolve_inside(
        f"{basename.replace('.', '_')}.html")
    if dest_path.exists():
        raise ValueError(f"Destination path {dest_path!r} already exists.")

    # get the title
    title, _ = extract_md_infos(markdown)
    title = str.strip(title).replace("`", "").replace("*", "")

    # set up the body
    body_1: str = __HTML_BODY_NO_STYLE_1
    body_2: str = __HTML_BODY_NO_STYLE_2
    if css is not None:
        body_1 = __HTML_BODY_STYLE_1.replace("{STYLE}", css)
        body_2 = __HTML_BODY_STYLE_2

    text: Final[str] = url_fixer(str.strip(Command((
        PYTHON_INTERPRETER, "-m", "markdown", "-o", "html", markdown),
        stderr=STREAM_FORWARD, stdout=STREAM_CAPTURE, timeout=info.timeout,
        working_dir=info.base_dir).execute()[0]))
    dest_path.write_all_str(f"{__HTML_HEADER}{title}{body_1}{text}{body_2}")
    logger(f"Finished rendering {markdown!r} to {dest_path!r}.")


def __minify(file: Path) -> None:
    """
    Minify the given HTML file.

    :param file: the file

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     with redirect_stdout(None):
    ...         __render_markdown(root.resolve_inside("README.md"), bf,
    ...             td, None, lambda s: s)
    ...         readme = td.resolve_inside("README_md.html")
    ...         long = str.__len__(readme.read_all_str())
    ...         __minify(readme)
    ...         short = str.__len__(readme.read_all_str())
    >>> 0 < short < long
    True
    """
    logger(f"Minifying HTML in {file!r}.")
    text: str = str.strip(file.read_all_str())
    text = str.strip(minify_html.minify(  # pylint: disable=E1101
        text, do_not_minify_doctype=True,
        ensure_spec_compliant_unquoted_attribute_values=True,
        keep_html_and_head_opening_tags=False, minify_css=True,
        minify_js=True, remove_bangs=True,
        remove_processing_instructions=True))
    if "<pre" not in text:
        text = " ".join(map(str.strip, text.splitlines()))
    file.write_all_str(str.strip(text))


def __minify_all(dest: Path, skip: Callable[[str], bool]) -> None:
    """
    Minify all files in the given destination folder.

    :param dest: the destination
    :param skip: the files to skip

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))

    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     with redirect_stdout(None):
    ...         __render_markdown(root.resolve_inside("README.md"), bf,
    ...             td, None, lambda s: s)
    ...         readme = td.resolve_inside("README_md.html")
    ...         __render_markdown(root.resolve_inside("CONTRIBUTING.md"), bf,
    ...             td, None, lambda s: s)
    ...         cb = td.resolve_inside("CONTRIBUTING_md.html")
    ...         longr = str.__len__(readme.read_all_str())
    ...         longc = str.__len__(cb.read_all_str())
    ...         __minify_all(td, lambda x: False)
    ...         shortr = str.__len__(readme.read_all_str())
    ...         shortc = str.__len__(cb.read_all_str())
    >>> 0 < shortr < longr
    True
    >>> 0 < shortc < longc
    True
    """
    if skip(dest):
        return
    if dest.is_file():
        if dest.endswith(".html"):
            __minify(dest)
    elif dest.is_dir():
        for f in dest.list_dir():
            __minify_all(f, skip)


def __put_nojekyll(dest: Path) -> None:
    """
    Put a `.nojekyll` file into each directory.

    :param dest: the destination path.

    >>> from pycommons.io.temp import temp_dir
    >>> with temp_dir() as td:
    ...     x = td.resolve_inside("x")
    ...     x.ensure_dir_exists()
    ...     y = x.resolve_inside("y")
    ...     y.ensure_dir_exists()
    ...     __put_nojekyll(td)
    ...     td.resolve_inside(".nojekyll").is_file()
    ...     x.resolve_inside(".nojekyll").is_file()
    ...     y.resolve_inside(".nojekyll").is_file()
    True
    True
    True
    """
    if not dest.is_dir():
        return
    dest.resolve_inside(".nojekyll").ensure_file_exists()
    for f in dest.list_dir(files=False):
        __put_nojekyll(f)


def make_documentation(info: BuildInfo) -> None:
    """
    Make the documentation of the project.

    :param info: the build information

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))
    >>> from io import StringIO
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     make_documentation(bf)
    """
    if not isinstance(info, BuildInfo):
        raise type_error(info, "info", BuildInfo)

    source: Final[Path | None] = info.doc_source_dir
    dest: Final[Path | None] = info.doc_dest_dir
    if (source is None) or (dest is None):
        raise ValueError("Need both documentation source and "
                         f"destination, but got {info}.")
    logger(f"Building documentation with setup {info}.")

    logger(f"First clearing {dest!r}.")
    if dest.exists():
        if not dest.is_dir():
            raise ValueError(f"{dest!r} exists but is no directory?")
        delete_path(dest)
    dest.ensure_dir_exists()

    logger("Collecting all documentation source files.")
    retain: Final[Callable[[Path], bool]] = __get_source(source)
    try:
        logger("Building the documentation files via Sphinx.")
        info.command(("sphinx-apidoc", "-M", "--ext-autodoc",
                      "-o", source, info.sources_dir)).execute()
        info.command(("sphinx-build", "-W", "-a", "-E", "-b", "html",
                      source, dest)).execute()
        logger("Finished the Sphinx executions.")
    finally:
        logger("Clearing all auto-generated files.")
        __keep_only_source(source, retain)

    logger("Now building the additional files.")

    if info.examples_dir is not None:
        examples_dest: Final[Path] = dest.resolve_inside("examples")
        examples_dest.ensure_dir_exists()
        logger(f"Now pygmentizing example files to {examples_dest!r}.")
        for f in info.examples_dir.list_dir(directories=False):
            if f.endswith(".py"):
                __pygmentize(f, info, examples_dest)

    logger("Now pygmentizing default files.")
    for fn in __PYGMENTIZE_DEFAULT:
        f = info.base_dir.resolve_inside(fn)
        if f.is_file():
            __pygmentize(f, info)

    # now printing coverage information
    coverage_file: Final[Path] = info.base_dir.resolve_inside(".coverage")
    coverage_dest: Path | None = None
    if coverage_file.is_file():
        logger(f"Generating coverage from file {coverage_file!r}.")
        coverage_dest = dest.resolve_inside("tc")
        coverage_dest.ensure_dir_exists()
        delete_path(coverage_dest)
        try:
            info.command(("coverage", "html", "-d", coverage_dest,
                          f"--data-file={coverage_file}",
                          f"--include={info.package_name}/*")).execute()
        except ValueError as ve:
            if coverage_dest.is_dir():
                raise
            logger(f"No coverage to report: {ve}.")
        else:
            info.command((
                "coverage-badge", "-o", coverage_dest.resolve_inside(
                    "badge.svg"))).execute()
    else:
        logger("No coverage data found.")

    # find potential style sheet
    static: Final[Path] = dest.resolve_inside("_static")
    css: str | None = None
    if static.is_dir():
        for sst in __STYLES:
            css_path: Path = static.resolve_inside(sst)
            if css_path.is_file():
                css = css_path.relative_to(dest)
                break
    if css is None:
        logger("Found no static css style.")
    else:
        logger(f"Using style sheet {css!r}.")

    setup_cfg: Final[Path] = info.base_dir.resolve_inside("setup.cfg")
    url_fixer: Callable[[str], str] = str.strip
    if setup_cfg.is_file():
        logger("Loading documentation information.")
        doc_info: Final[DocInfo] = load_doc_info_from_setup_cfg(setup_cfg)
        url_fixer = make_url_replacer(
            {doc_info.doc_url: "./"}, for_markdown=False)

    logger("Now rendering all markdown files in the root directory.")
    for f in info.base_dir.list_dir(directories=False):
        if f.is_file() and f.endswith(".md") and (
                not f.basename().startswith("README")):
            __render_markdown(f, info, dest, css, url_fixer)

    logger("Now minifying all generated html files.")
    __minify_all(dest, {coverage_dest}.__contains__)

    logger("Now putting a .nojekyll file into each directory.")
    __put_nojekyll(dest)

    logger(f"Finished building documentation with setup {info}.")


# Run documentation generation process if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Build the Documentation",
        "This utility uses sphinx to build the documentation.")
    make_documentation(parse_project_arguments(parser))
