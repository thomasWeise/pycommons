"""Test running the static analysis from the command line."""

from os import environ

from pycommons.io.path import Path
from pycommons.processes.python import PYTHON_ENV, PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_FORWARD, Command


def test_static_analysis_from_command_line() -> None:
    """Test running the static analysis."""
    nrt: str = "PYCOMMONS_NO_RECURSIVE_TESTS"
    if nrt in environ:
        return
    root_dir = Path(__file__).up(5)
    nrt_test_file = root_dir.resolve_inside(nrt)
    if nrt_test_file.exists():
        return
    Command([PYTHON_INTERPRETER, "-m",
             "pycommons.dev.building.static_analysis",
             "--root", root_dir, "--package", "pycommons"],
            env=PYTHON_ENV, stderr=STREAM_FORWARD, stdout=STREAM_FORWARD,
            working_dir=root_dir).execute()
