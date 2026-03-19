import argparse
import logging
import os
import shutil
import subprocess
import typing

_nodejs_bin_dir: typing.Union[str, None] = None  # pylint: disable=invalid-name

def set_nodejs_bin_dir(path: str) -> None:
    """ Set the binary path to use for NodeJS (node). """

    global _nodejs_bin_dir  # pylint: disable=global-statement
    _nodejs_bin_dir = path

def _has_command(command: str, cwd: str = '.') -> bool:
    """ Check if the given command is found on the current shell. """

    result = subprocess.run(["which", command], cwd = cwd, capture_output = True, check = False)
    return (result.returncode == 0)

def _has_package(package: str, cwd: str = '.') -> bool:
    """ Check if the given NodeJS package exists. """

    bin_path = 'npm'
    if (_nodejs_bin_dir is not None):
        bin_path = os.path.join(_nodejs_bin_dir, bin_path)

    result = subprocess.run([bin_path, "list", package], cwd = cwd, capture_output = True, check = False)
    return (result.returncode == 0)

def is_available(cwd: str = '.') -> bool:
    """ Check if KaTeX is available on this system. """

    if ((_nodejs_bin_dir is None) and (shutil.which('npx') is None)):
        logging.warning("Could not find `npx` (usually installed with `npm`), cannot use katex equations.")
        return False

    if (not _has_package('katex', cwd = cwd)):
        logging.warning("Could not find the `katex` NodeJS package, cannot use katex equations.")
        return False

    return True

def to_html(text: str, cwd: str = '.') -> str:
    """ Convert the given text (math/equation) to HTML using KaTeX. """

    bin_path = 'npx'
    if (_nodejs_bin_dir is not None):
        bin_path = os.path.join(_nodejs_bin_dir, bin_path)

    result = subprocess.run([bin_path, "katex", "--format", "mathml"], cwd = cwd,
        input = text, text = True, capture_output = True,
        check = False)

    if (result.returncode != 0):
        raise ValueError(f"KaTeX did not exit cleanly. Stdout: '{result.stdout}', Stderr: '{result.stderr}'")

    return result.stdout

def set_cli_args(parser: argparse.ArgumentParser, extra_state: typing.Dict[str, typing.Any]) -> argparse.ArgumentParser:
    """ Set KaTeX-related CLI options. """

    parser.add_argument('--nodejs-bin-dir', dest = 'node_bin_dir',
        action = 'store', type = str, default = None,
        help = ('A NodeJS binary directory that includes `npm` and `npx`.'
                + ' If not specified, $PATH will be searched.'
                + ' Used for HTML equations.'))

    return parser

def init_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace, extra_state: typing.Dict[str, typing.Any]) -> argparse.Namespace:
    """ Initialize this module from the CLI options set in set_cli_args(). """

    if (args.node_bin_dir is not None):
        set_nodejs_bin_dir(args.node_bin_dir)

    return args
