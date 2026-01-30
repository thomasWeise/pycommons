"""Test running the tests from the command line."""

from os import environ, remove, rename

from pycommons.io.path import Path
from pycommons.io.temp import temp_file
from pycommons.processes.python import PYTHON_ENV, PYTHON_INTERPRETER
from pycommons.processes.shell import STREAM_FORWARD, Command


def test_tests_from_command_line() -> None:
    """Test running the tests."""
    nrt: str = "PYCOMMONS_NO_RECURSIVE_TESTS"
    if nrt in environ:
        return
    root_dir = Path(__file__).up(5)
    nrt_test_file = root_dir.resolve_inside(nrt)
    if nrt_test_file.exists():
        return
    if nrt_test_file.ensure_file_exists():
        return
    try:
        env: dict[str, str] = dict(PYTHON_ENV)
        env[nrt] = nrt
        cmd = Command([PYTHON_INTERPRETER, "-m",
                       "pycommons.dev.building.run_tests",
                       "--root", root_dir, "--package", "pycommons"],
                      env=env, stderr=STREAM_FORWARD, stdout=STREAM_FORWARD,
                      working_dir=root_dir)
        coverage = root_dir.resolve_inside(".coverage")
        has_coverage = coverage.is_file()
        if has_coverage:
            with temp_file() as ctn:
                rename(coverage, ctn)
                cmd.execute()
                if coverage.is_file():
                    Command(["coverage", "combine", "-a", ctn],
                            env=PYTHON_ENV, stderr=STREAM_FORWARD,
                            stdout=STREAM_FORWARD, working_dir=root_dir)
                else:
                    rename(ctn, coverage)
        else:
            cmd.execute()
    finally:
        remove(nrt_test_file)
