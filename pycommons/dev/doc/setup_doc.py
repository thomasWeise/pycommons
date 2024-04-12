"""Set up the documentation builder in a unified way."""

import sys
from datetime import datetime, timezone
from inspect import stack
from typing import Any, Final, Iterable, Mapping

from pycommons.dev.doc.doc_info import DocInfo, load_doc_info_from_setup_cfg
from pycommons.dev.doc.index_rst import make_index_rst
from pycommons.dev.doc.process_md import (
    process_markdown_for_sphinx,
)
from pycommons.io.console import logger
from pycommons.io.path import Path, directory_path, line_writer
from pycommons.types import check_int_range, type_error

#: the default intersphinx mappings
__DEFAULT_INTERSPHINX: Final[dict[str, tuple[str, None]]] = {
    "latexgit": ("https://thomasweise.github.io/latexgit_py/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "moptipy": ("https://thomasweise.github.io/moptipy/", None),
    "moptipyapps": ("https://thomasweise.github.io/moptipyapps/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "psutil": ("https://psutil.readthedocs.io/en/stable/", None),
    "pycommons": ("https://thomasweise.github.io/pycommons/", None),
    "python": ("https://docs.python.org/3/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "sklearn": ("https://scikit-learn.org/stable/", None),
    "urllib3": ("https://urllib3.readthedocs.io/en/stable/", None),
}


def setup_doc(doc_dir: str, root_dir: str,
              copyright_start_year: int | None = None,
              dependencies: Iterable[str | tuple[str, str]] | None = None,
              base_urls: Mapping[str, str] | None = None,
              full_urls: Mapping[str, str] | None = None,
              static_paths: Iterable[str] | None = None) -> None:
    """
    Set up the documentation building process in a unified way.

    This function must be called directly from the `conf.py` script. It will
    configure the sphinx documentation generation engine using my default
    settings. It can automatically link to several standard dependencies,
    render the `README.md` file of the project to a format that the myst
    parser used by sphinx can understand, fix absolute URLs in the
    `README.md` file that point to the documentation URL to relative links,
    get the documentation URL, the project title, author, and version from the
    root `setup.cfg` file from which it traces to the `README.md` and the
    `version.py` file of the project, and also construct an `index.rst` file.
    All in all, you will end up with a very unified setup for the
    documentation generation. Nothing fancy, but it will work and work the
    same in all of my projects without the need to copy and maintain
    boilerplate code.

    :param doc_dir: the folder where the documentation is to be built.
    :param root_dir: the root path of the project.
    :param copyright_start_year: the copyright start year
    :param dependencies: the external libraries to use
    :param base_urls: a mapping of basic urls to shortcuts
    :param full_urls: a mapping of full urls to abbreviations
    :param static_paths: a list of static paths, if there are any
    """
    doc_path: Final[Path] = directory_path(doc_dir)
    root_path: Final[Path] = directory_path(root_dir)
    logger(f"Beginning to set up sphinx for document folder {doc_path!r} "
           f"and root folder {root_path!r}.")

    doc_info: Final[DocInfo] = load_doc_info_from_setup_cfg(
        root_path.resolve_inside("setup.cfg"))

    # the global variables
    global_vars: Final[dict[str, Any]] = stack()[1].frame.f_globals

    # create the copyright information
    current_year: Final[int] = datetime.now(timezone.utc).year
    thecopyright: str = str(current_year) \
        if (copyright_start_year is None) or (check_int_range(
            copyright_start_year, "copyright_start_year", 1980,
            current_year) == current_year) \
        else f"{copyright_start_year}-{current_year}"
    thecopyright = f"{thecopyright}, {doc_info.author}"
    logger(f"Printing copyright information {thecopyright!r}.")
    global_vars["copyright"] = thecopyright

    use_deps: dict[str, tuple[str, None]] = {
        "python": __DEFAULT_INTERSPHINX["python"]}
    if dependencies is not None:
        if not isinstance(dependencies, Iterable):
            raise type_error(dependencies, "dependencies", Iterable)

        # Location of dependency documentation for cross-referencing.
        for x in dependencies:
            if isinstance(x, tuple):
                use_deps[str.strip(x[0])] = (str.strip(x[1]), None)
            else:
                xx = str.strip(x)
                if xx in __DEFAULT_INTERSPHINX:
                    use_deps[xx] = __DEFAULT_INTERSPHINX[xx]
                else:
                    raise ValueError(
                        f"{x!r} is not among the known dependencies"
                        f" {sorted(__DEFAULT_INTERSPHINX.keys())}.")

    global_vars["intersphinx_mapping"] = use_deps
    logger(f"Setting dependency mappings to {use_deps}.")

    # set the base url
    use_url: Final[str] = f"{doc_info.doc_url}"
    logger(f"Using base url {use_url!r}.")
    global_vars["html_baseurl"] = use_url

    # set up the default urls
    if base_urls is None:
        base_urls = {doc_info.doc_url: "./"}
    elif doc_info.doc_url not in base_urls:
        base_urls = dict(base_urls)
        base_urls[doc_info.doc_url] = "./"

    readme_out: Final[Path] = doc_path.resolve_inside("README.md")
    logger(f"Now processing {doc_info.readme_md_file!r} to {readme_out!r} "
           f"with replacers {base_urls} and {full_urls}.")
    with (doc_info.readme_md_file.open_for_read() as rd,
          readme_out.open_for_write() as wd):
        process_markdown_for_sphinx(rd, line_writer(wd), base_urls, full_urls)

    index_rst_file: Final[Path] = doc_path.resolve_inside("index.rst")
    logger(f"Now writing index.rst file {index_rst_file!r}.")
    with index_rst_file.open_for_write() as wd:
        make_index_rst(doc_info, line_writer(wd))

    # enable myst header anchors
    global_vars["myst_heading_anchors"] = 6

    # project information
    global_vars["project"] = doc_info.project
    global_vars["author"] = doc_info.author

    # tell sphinx to go kaboom on errors
    global_vars["nitpicky"] = True
    global_vars["myst_all_links_external"] = True

    # The full version, including alpha/beta/rc tags.
    global_vars["release"] = doc_info.version
    global_vars["version"] = doc_info.version

    # The Sphinx extension modules that we use.
    extensions: Final[list[str]] = [
        "myst_parser",  # for processing README.md
        "sphinx.ext.autodoc",  # to convert docstrings to documentation
        "sphinx.ext.doctest",  # do the doc tests again
        "sphinx.ext.intersphinx",  # to link to numpy et al.
        "sphinx_autodoc_typehints",  # to infer types from hints
        "sphinx.ext.viewcode",  # add rendered source code
    ]
    logger(f"Using extensions {extensions}.")
    global_vars["extensions"] = extensions

    # inherit docstrings in autodoc
    global_vars["autodoc_inherit_docstrings"] = True

    # add default values after comma
    global_vars["typehints_defaults"] = "comma"

    # the sources to be processed
    global_vars["source_suffix"] = [".rst", ".md"]

    # Code syntax highlighting style:
    global_vars["pygments_style"] = "default"

    # The language is English.
    global_vars["language"] = "en"

    # The theme to use for HTML and HTML Help pages.
    global_vars["html_theme"] = "bizstyle"
    # The potential static paths
    if static_paths is not None:
        global_vars["html_static_path"] = sorted(map(str.strip, static_paths))
    global_vars["html_show_sphinx"] = False

    # Some python options
    global_vars["python_display_short_literal_types"] = True
    global_vars["python_use_unqualified_type_names"] = True

    # get the path to the root directory of this project
    if (list.__len__(sys.path) <= 0) or (sys.path[0] != root_path):
        sys.path.insert(0, root_path)

    logger(f"Finished setting up sphinx for document folder {doc_path!r} "
           f"and root folder {root_path!r}.")
