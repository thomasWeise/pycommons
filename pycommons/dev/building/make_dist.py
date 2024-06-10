"""Make the distribution."""

from argparse import ArgumentParser
from configparser import ConfigParser
from itertools import chain
from typing import Final

from pycommons.dev.building.build_info import (
    BuildInfo,
    parse_project_arguments,
)
from pycommons.dev.doc.doc_info import DocInfo, load_doc_info_from_setup_cfg
from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.io.path import UTF8, Path, delete_path, write_lines
from pycommons.io.temp import temp_dir, temp_file
from pycommons.processes.python import PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_FORWARD, Command
from pycommons.types import type_error

#: the prefix commands
__PRE_PREFIX: Final[tuple[str, ...]] = (
    "#!/bin/bash", "set -o pipefail", "set -o errtrace", "set -o nounset",
    "set -o errexit")

#: the prefix commands
__PREFIX: Final[tuple[str, ...]] = (
    'echo "Creating virtual environment."',
    'python3 -m venv "{VENV}"', 'echo "Activating virtual environment."',
    'source "{VENV}/bin/activate"',
)

#: the suffix commands
__SUFFIX: Final[tuple[str, ...]] = (
    'echo "Deactivating virtual environment."',
    "deactivate",
    'echo "Done."',
)


#: the virtual environment commands
__VENV_CMD: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("gz distribution with extras", (
        'echo "Installing {GZ_DIST}{EXTRAS} and capturing {REQUIREMENTS}."',
        'python3 -m pip --local --no-input --timeout {TIMEOUT} --retries 100 '
        '--require-virtualenv install "{GZ_DIST}{EXTRAS}"',
        'echo "Freezing requirements to {REQUIREMENTS}."',
        'pip freeze --all --require-virtualenv '
        '--no-input > "{REQUIREMENTS}"')),
    ("wheel distribution with extras", (
        'echo "Installing {WHEEL_DIST}{EXTRAS}."',
        'python3 -m pip --local --no-input --timeout {TIMEOUT} --retries 100 '
        '--require-virtualenv install "{WHEEL_DIST}{EXTRAS}"')),
    ("gz distribution without extras", (
        'echo "Installing {GZ_DIST} without extras."',
        'python3 -m pip --local --no-input --timeout {TIMEOUT} --retries 100 '
        '--require-virtualenv install "{GZ_DIST}"')),
    ("wheel distribution without extras", (
        'echo "Installing {WHEEL_DIST} without extras."',
        'python3 -m pip --local --no-input --timeout {TIMEOUT} --retries 100 '
        '--require-virtualenv install "{WHEEL_DIST}{EXTRAS}"')))

#: the prefix commands
__XZ: Final[tuple[str, ...]] = (
    'tar --dereference --exclude=".nojekyll" -c --transform '
    '"s,^,{BASE}/," * | xz -v -9e -c > "{DEST}"',
)


def __get_extras(setup_cfg: Path) -> list[str]:
    """
    Get all package extras.

    :param setup_cfg: the `setup.cfg` file
    :return: the set of extras

    >>> root = Path(__file__).up(4)
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     ex = __get_extras(root.resolve_inside("setup.cfg"))
    >>> print(ex)
    ['dev']
    """
    logger(f"Loading extras from {setup_cfg!r}.")
    cfg: Final[ConfigParser] = ConfigParser()
    cfg.read(setup_cfg, UTF8)
    if not cfg.has_section("options.extras_require"):
        logger(f"No extras from {setup_cfg!r}.")
        return []
    res = sorted(set(map(str.strip, cfg.options("options.extras_require"))))
    logger(f"Found extras {res} from {setup_cfg!r}.")
    return res


def make_dist(info: BuildInfo) -> None:
    """
    Create the distribution files.

    This code cannot really be unit tested, as it would run the itself
    recursively.

    :param info: the build information

    >>> root = Path(__file__).up(4)
    >>> bf = BuildInfo(root, "pycommons",
    ...     examples_dir=root.resolve_inside("examples"),
    ...     tests_dir=root.resolve_inside("tests"),
    ...     dist_dir=root.resolve_inside("dist"),
    ...     doc_source_dir=root.resolve_inside("docs/source"),
    ...     doc_dest_dir=root.resolve_inside("docs/build"))
    >>> from contextlib import redirect_stdout
    >>> with redirect_stdout(None):
    ...     make_dist(bf)

    >>> try:
    ...     make_dist(None)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi

    >>> try:
    ...     make_dist(1)
    ... except TypeError as te:
    ...     print(str(te)[:50])
    info should be an instance of pycommons.dev.buildi
    """
    if not isinstance(info, BuildInfo):
        raise type_error(info, "info", BuildInfo)

    dest: Final[Path] = info.dist_dir
    if dest is None:
        raise ValueError(f"Require distribution directory to build {info}.")
    logger(f"Now building distribution for {info} to {dest!r}.")
    if dest.is_dir():
        delete_path(dest)
    dest.ensure_dir_exists()
    dest.enforce_dir()

    setup_py: Final[Path] = info.base_dir.resolve_inside("setup.py")
    if setup_py.is_file():
        logger(f"Checking setup.py file {setup_py!r}.")
        info.command((PYTHON_INTERPRETER, setup_py, "check")).execute()
    else:
        logger("No setup.py file found.")

    logger("Building distribution.")
    info.command((PYTHON_INTERPRETER, "-m", "build", "-o", dest)).execute()

    logger("Now checking distribution.")
    info.command((PYTHON_INTERPRETER, "-m", "twine", "check",
                  f"{dest}/*")).execute()

    logger("Loading version information from setup.cfg.")
    setup_cfg: Final[Path] = info.base_dir.resolve_inside("setup.cfg")
    setup_cfg.enforce_file()
    doc_info: Final[DocInfo] = load_doc_info_from_setup_cfg(setup_cfg)
    dist_base: Final[str] = f"{info.package_name}-{doc_info.version}"
    logger(f"Base file name is {dist_base!r}.")
    gz_dist: Final[Path] = dest.resolve_inside(f"{dist_base}.tar.gz")
    gz_dist.enforce_file()
    logger(f"gz distribution is {gz_dist!r}.")
    wheel_dist: Final[Path] = dest.resolve_inside(
        f"{dist_base}-py3-none-any.whl")
    wheel_dist.enforce_file()
    logger(f"wheel distribution is {wheel_dist!r}.")
    requirements: Final[Path] = dest.resolve_inside(
        f"{dist_base}-requirements_frozen.txt")
    logger(f"Will store requirements in {requirements!r}.")
    to: Final[str] = str(info.timeout)

    extras: Final[list[str]] = __get_extras(setup_cfg)
    extras_str: Final[str] = "" if list.__len__(extras) <= 0 \
        else f"[{','.join(extras)}]"

    count: int = 0
    for what, steps in __VENV_CMD:
        count += 1  # noqa: SIM113
        if (count > 2) and (str.__len__(extras_str) <= 0):
            break
        logger(f"Now testing {what}.")
        with temp_dir() as venv:
            venv_build: Path = temp_file(directory=venv, suffix=".sh")
            with venv_build.open_for_write() as wd:
                write_lines((s.replace(
                    "{VENV}", venv).replace("{GZ_DIST}", gz_dist).replace(
                    "{WHEEL_DIST}", wheel_dist).replace(
                    "{REQUIREMENTS}", requirements).replace(
                    "{TIMEOUT}", to).replace("{EXTRAS}", extras_str)
                    for s in chain(__PRE_PREFIX, __PREFIX,
                                   steps, __SUFFIX)), wd)
            Command(("bash", "--noprofile", "-e", "-E",
                     venv_build), working_dir=venv,
                    timeout=info.timeout, stdout=STREAM_FORWARD,
                    stderr=STREAM_FORWARD).execute()

    logger("Fixing exact package requirements.")
    pack: Final[str] = info.package_name
    pack_replace: Final[str] = f"{pack}{extras_str} @"
    requirements_txt: Final[str] = requirements.read_all_str()
    with requirements.open_for_write() as wd:
        write_lines((
            f"{pack}{extras_str}=={doc_info.version}" if s.startswith(
                pack_replace) else s for s in str.splitlines(
                requirements_txt)), wd)

    docs: Final[Path | None] = info.doc_dest_dir
    if (docs is not None) and docs.is_dir():
        logger(f"Now compressing documentation {docs!r}.")
        doc_name: Final[str] = f"{dist_base}-documentation"
        doc_dest: Final[Path] = dest.resolve_inside(f"{doc_name}.tar.xz")
        with temp_file(suffix=".sh") as tf:
            with tf.open_for_write() as wd:
                write_lines((s.replace("{DEST}", doc_dest).replace(
                    "{BASE}", doc_name) for s in chain(
                    __PRE_PREFIX, __XZ)), wd)
            Command(("bash", "--noprofile", "-e", "-E", tf),
                    working_dir=docs, timeout=info.timeout,
                    stdout=STREAM_FORWARD, stderr=STREAM_FORWARD).execute()
        doc_dest.enforce_file()

    logger("Finished building distribution.")


# Run conversion if executed as script
if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__,
        "Build the Distribution Files.",
        "This utility builds a distribution for python projects "
        "in a unified way.")
    make_dist(parse_project_arguments(parser))
