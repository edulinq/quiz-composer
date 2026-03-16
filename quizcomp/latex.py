import argparse
import logging
import os
import shutil
import subprocess
import typing

_pdflatex_bin_path: typing.Union[str, None] = None
_pdflatex_use_docker: bool = False

DOCKER_IMAGE: str = "ghcr.io/edulinq/pdflatex-docker:1.0.0"

def set_pdflatex_bin_path(path: str) -> None:
    """ Set the binary path to use for NodeJS (node). """

    global _pdflatex_bin_path
    _pdflatex_bin_path = path

def set_pdflatex_use_docker(pdflatex_use_docker: bool) -> None:
    """ Set whether or not to use the pdflatex Docker container. """

    global _pdflatex_use_docker
    _pdflatex_use_docker = pdflatex_use_docker

def is_available() -> bool:
    """ Check if LaTeX is available on this system. """

    if (_pdflatex_use_docker):
        if (not _is_docker_available()):
            logging.warning("Docker is not available, cannot compile PDFs.")
            return False

        return True

    if (_pdflatex_bin_path is not None):
        return True

    if (shutil.which('pdflatex') is None):
        logging.warning("Could not find `pdflatex`, cannot compile PDFs.")
        return False

    return True

def _is_docker_available() -> bool:
    """ Check if Docker is available on this system. """

    if (shutil.which('docker') is None):
        return False

    result = subprocess.run(["docker", "info"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    return (result.returncode == 0)

def compile(path: str) -> None:
    """
    Compile a LaTeX file to PDF in its containing directory.

    The caller must provide a path to a TeX file within a prepared output directory.
    This directory should contain all necessary resources (e.g., images) and no non-relevant files.
    Compilation may generate additional files (e.g., .aux, .log) in this directory,
    and permissions may be modified as needed.
    """

    if (_pdflatex_use_docker is True):
        _compile_docker(path)
    else:
        _compile_local(path)

def _compile_local(path: str) -> None:
    """ Compile without using Docker. """

    bin_path = "pdflatex"
    if (_pdflatex_bin_path is not None):
        bin_path = _pdflatex_bin_path

    tex_filename = os.path.basename(path)
    out_dir = os.path.dirname(path)

    # Need to compile twice to get positioning information.
    for _ in range(2):
        result = subprocess.run([bin_path, '-interaction=nonstopmode', tex_filename],
                                cwd = out_dir, text = True, capture_output = True)
        if (result.returncode != 0):
            raise ValueError(f"pdflatex did not exit cleanly. Stdout: '{result.stdout}', Stderr: '{result.stderr}'")

def _compile_docker(path: str) -> None:
    """ Compile using Docker. """

    tex_filename = os.path.basename(path)
    out_dir_path = os.path.abspath(os.path.dirname(path))

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{out_dir_path}:/work",
        DOCKER_IMAGE,
        tex_filename
    ]

    result = subprocess.run(docker_cmd, capture_output = True, text = True)
    if (result.returncode != 0):
        raise ValueError(f"Docker compilation failed with exit code '{result.returncode}'. Stdout: '{result.stdout}', Stderr: '{result.stderr}'")

def set_cli_args(parser: argparse.ArgumentParser, extra_state: typing.Dict[str, typing.Any]) -> argparse.ArgumentParser:
    """ Set LaTeX-related CLI options. """

    parser.add_argument('--pdflatex-bin-path', dest = 'pdflatex_bin_path',
        action = 'store', type = str, default = None,
        help = ('The path to the pdflatex binary to use.'
                + ' If not specified, $PATH will be searched.'
                + ' Used to compile PDFs.'))

    parser.add_argument('--pdflatex-use-docker', dest = 'pdflatex_use_docker',
        action = 'store_true', default = False,
        help = ('Use Docker to compile PDFs with pdflatex.'
                + f" The Docker image '{DOCKER_IMAGE}' will be used."))

    return parser

def init_from_args(parser: argparse.ArgumentParser, args: argparse.Namespace, extra_state: typing.Dict[str, typing.Any]) -> argparse.Namespace:
    """ Initialize this module from the CLI options set in set_cli_args(). """

    if (args.pdflatex_use_docker):
        set_pdflatex_use_docker(args.pdflatex_use_docker)

    if (args.pdflatex_bin_path is not None):
        set_pdflatex_bin_path(args.pdflatex_bin_path)

    return args
