"""
Make an `index.rst` file.

In all of my projects, the `index.rst` files have the same contents,
basically. So here we generate them on the fly based on the documentation
information data. Since this data contains the index of the last section
in the `README.md` files, this allows me to properly number the code section.
"""
from typing import Any, Callable

from pycommons.dev.doc.doc_info import DocInfo
from pycommons.io.console import logger
from pycommons.types import type_error


def make_index_rst(info: DocInfo, collector: Callable[[str], Any]) -> None:
    """
    Create the `index.rst` file contents.

    :param info: The documentation information
    :param collector: the collector to receive the information.

    >>> di = DocInfo(__file__, "a", "b", "bla", "1.2", 12,
    ...              "https://example.com")
    >>> from contextlib import redirect_stdout
    >>> l = []
    >>> with redirect_stdout(None):
    ...     make_index_rst(di, l.append)
    >>> for s in l:
    ...     print(s)
    bla
    ===
    <BLANKLINE>
    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`
    <BLANKLINE>
    .. include:: README.md
       :parser: myst_parser.sphinx_
    <BLANKLINE>
    13. Modules and Code
    --------------------
    <BLANKLINE>
    .. toctree::
       :maxdepth: 4
    <BLANKLINE>
       modules

    >>> try:
    ...     make_index_rst(None, print)
    ... except TypeError as te:
    ...     print(str(te)[:70])
    info should be an instance of pycommons.dev.doc.doc_info.DocInfo but i

    >>> try:
    ...     make_index_rst(1, print)
    ... except TypeError as te:
    ...     print(str(te)[:70])
    info should be an instance of pycommons.dev.doc.doc_info.DocInfo but i

    >>> try:
    ...     make_index_rst(di, None)
    ... except TypeError as te:
    ...     print(str(te))
    collector should be a callable but is None.

    >>> try:
    ...     make_index_rst(di, 1)
    ... except TypeError as te:
    ...     print(str(te))
    collector should be a callable but is int, namely '1'.
    """
    if not isinstance(info, DocInfo):
        raise type_error(info, "info", DocInfo)
    if not callable(collector):
        raise type_error(collector, "collector", call=True)
    logger(f"Now creating index.rst contents for project {info.project!r}.")

    collector(info.title)
    collector("=" * str.__len__(info.title))
    collector("")
    collector("* :ref:`genindex`")
    collector("* :ref:`modindex`")
    collector("* :ref:`search`")
    collector("")
    collector(".. include:: README.md")
    collector("   :parser: myst_parser.sphinx_")
    collector("")
    mac: str = "Modules and Code"
    if info.last_major_section_index is not None:
        mac = f"{info.last_major_section_index + 1}. {mac}"
    collector(mac)
    collector("-" * str.__len__(mac))
    collector("")
    collector(".. toctree::")
    collector("   :maxdepth: 4")
    collector("")
    collector("   modules")
    logger("Finished creating index.rst contents for "
           f"project {info.project!r}.")
