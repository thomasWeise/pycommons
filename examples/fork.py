"""
An example for forking a process.

Depending on the command line arguments you use to invoke this process with,
it can fork multiple times this very process.

If you provide the argument `"--fork N"`, then the process will be launched
`N` times. Each of the copies of the process will have a different `fork_id`
parameter.
If you additionally provide the argument `"--fork-log-dir YYY"`, then `YYY`
will be used as a log directory.
Each of the forked processes will get one log file where it writes its
standard output and one log file where it writes its standard error stream
inside this log directory.

If you do not provide such arguments, the process is just executed normally.
It will then write a random number of times with random delays the text that
was provided via argument `"--text ..."`.
"""

from argparse import ArgumentParser
from random import randint
from time import sleep
from typing import Final

from pycommons.io.arguments import pycommons_argparser
from pycommons.io.console import logger
from pycommons.processes.fork import fork

if __name__ == "__main__":
    parser: Final[ArgumentParser] = pycommons_argparser(
        __file__, "This is an example for forking.",
        "Run this program with argument --fork XXX to create XXX processes.\n"
        "Run it with argument --fork-log-dir YYY to create log files in"
        "directory YYY.\n"
        "Use argument --text 'ZZZ' to also write some text.")
    parser.add_argument(
        "--text", help="Some text to be written.",
        type=str, nargs="?", default="No text given.")
    args = fork(parser)

    if args is not None:
        fork_id: int | None = args.fork_id
        if fork_id is None:
            logger("The process was not forked.")
            text = f"Original process with text={args.text!r}."
        else:
            logger("The process was forked.")
            text = f"Fork {args.fork_id} with text={args.text!r}."
        for _ in range(randint(1, 5)):
            logger(text)
            sleep(randint(1, 3))
