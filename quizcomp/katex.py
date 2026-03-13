import argparse
import logging
import os
import shutil
import subprocess
import typing

import quizcomp.util.encoding

_nodejs_bin_dir = None

def set_nodejs_bin_dir(path):
    global _nodejs_bin_dir
    _nodejs_bin_dir = path

def _has_command(command, cwd = '.'):
    result = subprocess.run(["which", command], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def _has_package(package, cwd = '.'):
    bin_path = 'npm'
    if (_nodejs_bin_dir is not None):
        bin_path = os.path.join(_nodejs_bin_dir, bin_path)

    result = subprocess.run([bin_path, "list", package], cwd = cwd, capture_output = True)
    return (result.returncode == 0)

def is_available(cwd = '.'):
    if ((_nodejs_bin_dir is None) and (shutil.which('npx') is None)):
        logging.warning("Could not find `npx` (usually installed with `npm`), cannot use katex equations.")
        return False

    if (not _has_package('katex', cwd = cwd)):
        logging.warning("Could not find the `katex` NodeJS package, cannot use katex equations.")
        return False

    return True

def to_html(text, cwd = '.'):
    bin_path = 'npx'
    if (_nodejs_bin_dir is not None):
        bin_path = os.path.join(_nodejs_bin_dir, bin_path)

    result = subprocess.run([bin_path, "katex", "--format", "mathml"], cwd = cwd,
        input = text, encoding = quizcomp.util.encoding.DEFAULT_ENCODING,
        capture_output = True)

    if (result.returncode != 0):
        raise ValueError("KaTeX did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))

    return result.stdout

def set_cli_args(parser: argparse.ArgumentParser, extra_state: typing.Dict[str, typing.Any]) -> None:
    parser.add_argument('--nodejs-bin-dir', dest = 'node_bin_dir',
        action = 'store', type = str, default = None,
        help = ('A NodeJS binary directory that includes `npm` and `npx`.'
                + ' If not specified, $PATH will be searched.'
                + ' Used for HTML equations.'))

    return parser

def init_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace, extra_state: typing.Dict[str, typing.Any]) -> None:
    if (args.node_bin_dir is not None):
        set_nodejs_bin_dir(args.node_bin_dir)

    return args
