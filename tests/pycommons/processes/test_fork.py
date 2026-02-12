"""Test the forking of processes."""

from typing import Final

from pycommons.io.path import Path
from pycommons.io.temp import temp_dir
from pycommons.processes.python import PYTHON_INTERPRETER as PI
from pycommons.processes.shell import Command

#: The forking example program
SCRIPT: Final[Path] = Path(__file__).up(4).resolve_inside(
    "examples").resolve_inside("fork.py")


def test_normal_exec() -> None:
    """Test the normal execution of the example."""
    Command((PI, SCRIPT)).execute(True)


def test_1_fork_normal() -> None:
    """Test doing 1 fork."""
    Command((PI, SCRIPT, "--fork", "1")).execute(True)


def test_2_forks_normal() -> None:
    """Test doing 2 forks."""
    Command((PI, SCRIPT, "--fork", "2")).execute(True)


def test_3_forks_normal() -> None:
    """Test doing 3 forks."""
    Command((PI, SCRIPT, "--fork", "3")).execute(True)


def test_4_forks_normal() -> None:
    """Test doing 4 forks."""
    Command((PI, SCRIPT, "--fork", "3")).execute(True)


def test_1_fork_log_dir() -> None:
    """Test doing 1 fork with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "1",
                 "--fork-log-dir", td)).execute(True)


def test_2_forks_log_dir() -> None:
    """Test doing 2 forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "2",
                 "--fork-log-dir", td)).execute(True)


def test_3_fork_log_dir() -> None:
    """Test doing 3 forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "3",
                 "--fork-log-dir", td)).execute(True)


def test_4_fork_log_dir() -> None:
    """Test doing 4 forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "4",
                 "--fork-log-dir", td)).execute(True)


def test_rel_0d5_fork_normal() -> None:
    """Test doing relative forks."""
    Command((PI, SCRIPT, "--fork", "0.5")).execute(True)


def test_rel_0d5_fork_log_dir() -> None:
    """Test doing relative forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "0.5",
                 "--fork-log-dir", td)).execute(True)


def test_rel_0d75_fork_normal() -> None:
    """Test doing relative forks."""
    Command((PI, SCRIPT, "--fork", "0.75")).execute(True)


def test_rel_0d75_fork_log_dir() -> None:
    """Test doing relative forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "0.75",
                 "--fork-log-dir", td)).execute(True)


def test_rel_0d3_fork_normal() -> None:
    """Test doing relative forks."""
    Command((PI, SCRIPT, "--fork", "0.3")).execute(True)


def test_rel_0d3_fork_log_dir() -> None:
    """Test doing relative forks with logging directory."""
    with temp_dir() as td:
        Command((PI, SCRIPT, "--fork", "0.3",
                 "--fork-log-dir", td)).execute(True)
