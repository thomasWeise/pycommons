"""
The documentation information.

The :class:`~pycommons.dev.doc.doc_info.DocInfo` holds the basic data needed
to generate documentation in a unified way. For now, this data is loaded
from the `setup.cfg` file, in which the process expects to find references
to a `version.py` and `README.md` file. Then, it loads the information from
these files as well. This spares us the trouble of defining the information
in several places and keeping it synchronized.
"""
from configparser import ConfigParser
from dataclasses import dataclass
from typing import Final

from pycommons.io.console import logger
from pycommons.io.path import UTF8, Path, file_path
from pycommons.net.url import URL
from pycommons.types import check_int_range, check_to_int_range


@dataclass(frozen=True, init=False, order=False, eq=False)
class DocInfo:
    """
    A class that represents information about documentation.

    >>> di = DocInfo(__file__, "a", "b", "c", "1", 12, "https://example.com")
    >>> di.doc_url
    'https://example.com'
    >>> di.last_major_section_index
    12
    >>> di.project
    'a'
    >>> di.author
    'b'
    >>> di.title
    'c'
    >>> di.readme_md_file[-11:]
    'doc_info.py'

    >>> di = DocInfo(__file__, "a", "b", "c", "1", None,
    ...             "https://example.com")
    >>> di.doc_url
    'https://example.com'
    >>> print(di.last_major_section_index)
    None
    >>> di.title
    'c'
    >>> di.readme_md_file[-11:]
    'doc_info.py'

    >>> try:
    ...     DocInfo(None, "a", "b", "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     DocInfo(1, "a", "b", "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     DocInfo(__file__, None, "b", "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     DocInfo(__file__, 1, "b", "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     DocInfo(__file__, " ", "b", "c", "1", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid project name ' '.

    >>> try:
    ...     DocInfo(__file__, "a", None, "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     DocInfo(__file__, "a", 1, "c", "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     DocInfo(__file__, "a", " ", "c", "1", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid author name ' '.

    >>> try:
    ...     DocInfo(__file__, "a", "b", None, "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     DocInfo(__file__, "a", "b", 1, "1", 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     DocInfo(__file__, "b", "c", " ", "1", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid title ' '.

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", None, 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", 1, 12, "https://example.com")
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "x", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:64])
    Invalid version 'x': Cannot convert version='x' to int, let alon

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", " ", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:64])
    Invalid version ' ': empty or only white space.


    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.x", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:64])
    Invalid version '1.x': Cannot convert version='x' to int, let al

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "-1", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:64])
    Invalid version '-1': version=-1 is invalid, must be in 0..10000

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "0.-1", 12, "https://example.com")
    ... except ValueError as ve:
    ...     print(str(ve)[:64])
    Invalid version '0.-1': version=-1 is invalid, must be in 0..100

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.2", "x",
    ...             "https://example.com")
    ... except TypeError as te:
    ...     print(str(te)[:60])
    last_major_section_index should be an instance of int but is

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.2", 0, "https://example.com")
    ... except ValueError as ve:
    ...     print(ve)
    last_major_section_index=0 is invalid, must be in 1..1000000.

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.2", 12, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.2", 12, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     DocInfo(__file__, "a", "b", "c", "1.2", 12, "dfg")
    ... except ValueError as ve:
    ...     print(ve)
    URL part '' has invalid length 0.
    """

    #: The readme.md file.
    readme_md_file: Path
    #: The project name.
    project: str
    #: The author name.
    author: str
    #: The documentation title.
    title: str
    #: The version string.
    version: str
    #: The index of the last major section
    last_major_section_index: int | None
    #: the base URL of the documentation
    doc_url: URL

    def __init__(self, readme_md: Path, project: str, author: str,
                 title: str, version: str,
                 last_major_section_index: int, doc_url: str) -> None:
        """
        Create the documentation information class.

        :param readme_md: the path to the `README.md` file
        :param project: the project name
        :param author: the author name
        :param title: the title string
        :param version: the version string
        :param last_major_section_index: the index of the last major section,
            or `None`
        :param doc_url: the base URL of the documentation
        """
        object.__setattr__(self, "readme_md_file", file_path(readme_md))

        uproject = str.strip(project)
        if str.__len__(uproject) <= 0:
            raise ValueError(f"Invalid project name {project!r}.")
        object.__setattr__(self, "project", uproject)

        uauthor = str.strip(author)
        if str.__len__(uauthor) <= 0:
            raise ValueError(f"Invalid author name {author!r}.")
        object.__setattr__(self, "author", uauthor)

        utitle = str.strip(title)
        if str.__len__(utitle) <= 0:
            raise ValueError(f"Invalid title {title!r}.")
        object.__setattr__(self, "title", utitle)

        uversion = str.strip(version)
        if str.__len__(uversion) <= 0:
            raise ValueError(
                f"Invalid version {version!r}: empty or only white space.")
        for v in uversion.split("."):
            try:
                check_to_int_range(v, "version", 0, 1_000_000_000)
            except ValueError as ve:
                raise ValueError(
                    f"Invalid version {version!r}: "
                    f"{str(ve).removesuffix('.')}.") from ve
        object.__setattr__(self, "version", uversion)

        object.__setattr__(
            self, "last_major_section_index", None
            if last_major_section_index is None else check_int_range(
                last_major_section_index, "last_major_section_index", 1,
                1_000_000))
        object.__setattr__(self, "doc_url", URL(doc_url))

    def __str__(self) -> str:
        """
        Convert this object to a string.

        :return: the string version of this object.

        >>> print(str(DocInfo(__file__, "a", "b", "c", "1",
        ...                   12, "https://example.com"))[:40])
        'c' project 'a' by 'b', version '1', wit
        """
        return (f"{self.title!r} project {self.project!r} by "
                f"{self.author!r}, version {self.version!r}, "
                f"with readme file {self.readme_md_file!r} having the last "
                f"section {self.last_major_section_index} and documentation "
                f"url {self.doc_url}.")


def extract_md_infos(readme_md_file: str) -> tuple[str, int | None]:
    """
    Parse a `README.md` file and find the title and last section index.

    :param readme_md_file: the path to the `README.md`
    :return: a tuple of the title (headline starting with `"# "` (but without
        the `"# "`), and the last section index, if any)

    >>> from os.path import join, dirname
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     t = extract_md_infos(join(dirname(dirname(dirname(dirname(
    ...                          __file__)))), "README.md"))
    >>> print(t)
    ('*pycommons:* Common Utility Functions for Python Projects.', 5)
    """
    readme_md: Final[Path] = file_path(readme_md_file)
    logger(f"Now parsing markdown file {readme_md!r}.")

    # load both the title and the last index
    title: str | None = None
    last_idx: int | None = None
    in_code: bool = False
    with (readme_md.open_for_read() as rd):
        for orig_line in rd:
            line: str = str.strip(orig_line)  # force string
            # skip all code snippets in the file
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            # ok, we are not in code
            if line.startswith("# "):  # top-level headline
                if title is not None:  # only 1 top-level headline permitted
                    raise ValueError(
                        f"Already have title {title!r} but now found "
                        f"{line[2:]!r} in {readme_md!r}.")
                title = str.strip(line[2:])
            elif line.startswith("## "):  # second-level headline
                doti: int = line.find(".")  # gather numeric index, if any
                if doti <= 3:
                    if last_idx is not None:
                        raise ValueError(f"Got {line!r} after having index.")
                else:
                    idx_str = str.strip(line[3:doti])
                    try:
                        index = check_to_int_range(idx_str, "s", 1, 1000)
                    except ValueError as ve:
                        index = None
                        if last_idx is not None:
                            raise ValueError(
                                f"Got {line!r} and finding index "
                                f"{last_idx} in {readme_md!r} causing "
                                f"{str(ve).removesuffix('.')}.") from ve
                    if index is not None:
                        if (last_idx is not None) and (last_idx >= index):
                            raise ValueError(
                                f"Found index {index} in line {line!r} "
                                f"after index {last_idx} in "
                                f"{readme_md!r}.")
                        last_idx = index

    if title is None:
        raise ValueError(f"No title in {readme_md!r}.")

    logger(f"Finished parsing markdown file {readme_md!r}, got "
           f"title {title!r} and last section index {last_idx}.")
    return title, last_idx


def parse_version_py(version_file: str,
                     version_attr: str = "__version__") -> str:
    """
    Parse a `version.py` file and return the version string.

    :param version_file: the path to the version file
    :param version_attr: the version attribute
    :return: the version string

    >>> from os.path import join, dirname
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     s = parse_version_py(join(dirname(dirname(dirname(__file__))),
    ...         "version.py"))
    >>> print(s[:s.rindex(".")])
    0.8

    >>> try:
    ...     parse_version_py(None, "v")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'NoneType'

    >>> try:
    ...     parse_version_py(1, "v")
    ... except TypeError as te:
    ...     print(te)
    descriptor '__len__' requires a 'str' object but received a 'int'

    >>> try:
    ...     parse_version_py(__file__, None)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'NoneType' object

    >>> try:
    ...     parse_version_py(__file__, 1)
    ... except TypeError as te:
    ...     print(te)
    descriptor 'strip' for 'str' objects doesn't apply to a 'int' object

    >>> try:
    ...     parse_version_py(__file__, "")
    ... except ValueError as ve:
    ...     print(ve)
    Invalid version attr ''.

    >>> from contextlib import redirect_stdout
    >>> from io import StringIO
    >>> try:
    ...     with redirect_stdout(None):
    ...         parse_version_py(__file__, "xyz")
    ... except ValueError as ve:
    ...     print(str(ve)[:36])
    Did not find version attr 'xyz' in '
    """
    version_path: Final[Path] = file_path(version_file)
    uversion_attr = str.strip(version_attr)
    if str.__len__(uversion_attr) <= 0:
        raise ValueError(f"Invalid version attr {version_attr!r}.")
    logger(f"Now parsing version file {version_path!r}, looking for "
           f"attribute {uversion_attr!r}.")

    version_str: str | None = None
    # load the version string
    with version_path.open_for_read() as rd:
        for orig_line in rd:
            line = str.strip(orig_line)
            lst: list[str] = [str.strip(item) for sublist in
                              line.split("=") for item in sublist.split(":")]
            if lst[0] == uversion_attr:
                if version_str is not None:
                    raise ValueError(
                        f"Version defined as {version_str!r} in "
                        f"{version_path!r} but encountered {orig_line!r}?")
                if list.__len__(lst) <= 1:
                    raise ValueError(f"Strange version string {orig_line!r} "
                                     f"in {version_path!r}.")
                version_tst: str = lst[-1]
                for se in ("'", '"'):
                    if version_tst.startswith(se):
                        if not version_tst.endswith(se):
                            raise ValueError(
                                f"Incorrect string limits for {orig_line!r}"
                                f" in version file {version_path!r}.")
                        version_str = str.strip(version_tst[1:-1])
                        break
                if version_str is None:
                    raise ValueError(f"Undelimited string in {orig_line!r} in"
                                     f" version file {version_path!r}?")
    if version_str is None:
        raise ValueError(f"Did not find version attr {uversion_attr!r} in "
                         f"{version_path!r}.")

    logger(f"Found version string {version_str!r} in file {version_path!r}.")
    return version_str


def load_doc_info_from_setup_cfg(setup_cfg_file: str) -> DocInfo:
    """
    Load the documentation information from the `setup.cfg` file.

    :param setup_cfg_file: the path to the `setup.cfg` file.
    :return: the documentation information

    >>> from os.path import dirname, join
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     r = load_doc_info_from_setup_cfg(join(dirname(dirname(dirname(
    ...         dirname(__file__)))), "setup.cfg"))
    >>> r.title
    '*pycommons:* Common Utility Functions for Python Projects.'
    >>> r.doc_url
    'https://thomasweise.github.io/pycommons'
    >>> r.project
    'pycommons'
    >>> r.author
    'Thomas Weise'
    """
    setup_cfg: Final[Path] = file_path(setup_cfg_file)
    logger(f"Now loading documentation info from {setup_cfg!r}.")
    cfg: Final[ConfigParser] = ConfigParser()
    cfg.read(setup_cfg, UTF8)
    root_path: Final[Path] = setup_cfg.up(1)

    # first get version string
    version_attr: Final[str] = str.strip(cfg.get("metadata", "version"))
    if str.__len__(version_attr) <= 0:
        raise ValueError(f"Invalid version attribute {version_attr!r}.")
    version_str: str | None = None
    if version_attr.startswith("attr: "):
        version_splt: list[str] = str.split(str.strip(version_attr[6:]), ".")
        version_file = root_path
        for f in version_splt[:-2]:  # find file
            version_file = version_file.resolve_inside(f)
        version_str = parse_version_py(
            version_file.resolve_inside(version_splt[-2] + ".py"),
            version_splt[-1])
    else:
        version_str = version_attr

    # now load data from readme md
    long_desc_attr: Final[str] = str.strip(cfg.get(
        "metadata", "long_description"))
    if str.__len__(long_desc_attr) <= 0:
        raise ValueError(
            f"Invalid long_description attribute {long_desc_attr!r}.")
    if not long_desc_attr.startswith("file:"):
        raise ValueError(f"long_description {long_desc_attr!r} does "
                         f"not point to file.")
    readme_md_file: Final[Path] = root_path.resolve_inside(
        str.strip(long_desc_attr[6:]))
    title, last_sec = extract_md_infos(readme_md_file)

    # get the documentation URL
    docu_url: str | None = None
    for url in str.splitlines(str.strip(cfg.get(
            "metadata", "project_urls"))):
        splt: list[str] = url.split("=")
        if list.__len__(splt) != 2:
            raise ValueError(f"Strange URL line {url!r}.")
        if str.strip(splt[0]).lower() == "documentation":
            if docu_url is not None:
                raise ValueError("Two docu URLs found?")
            docu_url = str.strip(splt[1])
    if docu_url is None:
        docu_url = cfg.get("metadata", "url")

    res: Final[DocInfo] = DocInfo(
        readme_md_file, str.strip(cfg.get("metadata", "name")),
        str.strip(cfg.get("metadata", "author")), title, version_str,
        last_sec, docu_url)

    logger("Finished loading documentation info "
           f"from {setup_cfg!r}, found {res}")
    return res
