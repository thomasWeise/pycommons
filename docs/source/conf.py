"""The configuration for sphinx to generate the documentation."""
import datetime
import os
import sys
from typing import Final
from pycommons.io.path import file_path, Path, line_writer
from pycommons.dev.process_md import make_url_replacer, process_markdown

# the path of the documentation configuration
doc_path: Final[Path] = file_path(__file__).up(1)

# get the path to the root directory of this project
root_path: Final[Path] = doc_path.up(2)
sys.path.insert(0, root_path)

# set the base url
html_baseurl = "https://thomasweise.github.io/pycommons/"

with (root_path.resolve_inside("README.md").open_for_read() as rd,
      doc_path.resolve_inside("README.md").open_for_write() as wd):
    process_markdown(rd, line_writer(wd), make_url_replacer(
        {"https://thomasweise.github.io/pycommons/": "./"},
        {"https://github.com/thomasWeise/pycommons/blob/main/LICENSE":
         "./LICENSE.html"}
    ))

# enable myst header anchors
myst_heading_anchors = 6

# project information
project = 'pycommons'
author = 'Thomas Weise'
# noinspection PyShadowingBuiltins
copyright = f"2021-{datetime.datetime.now ().year}, {author}"

# tell sphinx to go kaboom on errors
nitpicky = True
myst_all_links_external = True

# The full version, including alpha/beta/rc tags.
release = {}
with open(os.path.abspath(os.path.sep.join([
        root_path, "pycommons", "version.py"]))) as fp:
    exec(fp.read(), release)  # nosec # nosemgrep # noqa: DUO105
release = release["__version__"]

# The Sphinx extension modules that we use.
extensions = ['myst_parser',  # for processing README.md
              'sphinx.ext.autodoc',  # to convert docstrings to documentation
              'sphinx.ext.doctest',  # do the doc tests again
              'sphinx.ext.intersphinx',  # to link to numpy et al.
              'sphinx_autodoc_typehints',  # to infer types from hints
              'sphinx.ext.viewcode',  # add rendered source code
              ]

# Location of dependency documentation for cross-referencing.
intersphinx_mapping = {
    'numpy': ('https://numpy.org/doc/stable/', None),
    'python': ("https://docs.python.org/3/", None),
}

# inherit docstrings in autodoc
autodoc_inherit_docstrings = True

# add default values after comma
typehints_defaults = "comma"

# the sources to be processed
source_suffix = ['.rst', '.md']

# The theme to use for HTML and HTML Help pages.
html_theme = 'bizstyle'

# Code syntax highlighting style:
pygments_style = 'default'
