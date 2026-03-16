import logging
import os
import shutil
import subprocess

_pdflatex_bin_path = None
_pdflatex_use_docker = False

DOCKER_IMAGE = "ghcr.io/edulinq/pdflatex-docker:1.0.0"

def set_pdflatex_bin_path(path):
    global _pdflatex_bin_path
    _pdflatex_bin_path = path

def set_pdflatex_use_docker(pdflatex_use_docker):
    global _pdflatex_use_docker
    _pdflatex_use_docker = pdflatex_use_docker

def is_available():
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

def _is_docker_available():
    if (shutil.which('docker') is None):
        return False

    result = subprocess.run(["docker", "info"], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    return (result.returncode == 0)

def compile(path):
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

def _compile_local(path):
    bin_path = "pdflatex"
    if (_pdflatex_bin_path is not None):
        bin_path = _pdflatex_bin_path

    tex_filename = os.path.basename(path)
    out_dir = os.path.dirname(path)

    # Need to compile twice to get positioning information.
    for _ in range(2):
        result = subprocess.run([bin_path, '-interaction=nonstopmode', tex_filename],
                                cwd = out_dir, capture_output = True)
        if (result.returncode != 0):
            raise ValueError("pdflatex did not exit cleanly. Stdout: '%s', Stderr: '%s'" % (result.stdout, result.stderr))

def _compile_docker(path):
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
        raise ValueError("Docker compilation failed with exit code '%s'. Stdout: '%s', Stderr: '%s'" % (result.returncode, result.stdout, result.stderr))

def set_cli_args(parser):
    parser.add_argument('--pdflatex-bin-path', dest = 'pdflatex_bin_path',
        action = 'store', type = str, default = None,
        help = ('The path to the pdflatex binary to use.'
                + ' If not specified, $PATH will be searched.'
                + ' Used to compile PDFs.'))

    parser.add_argument('--pdflatex-use-docker', dest = 'pdflatex_use_docker',
        action = 'store_true', default = False,
        help = ('Use Docker to compile PDFs with pdflatex.'
                + " The Docker image '%s' will be used." % (DOCKER_IMAGE)))

    return parser

def init_from_args(args):
    if (args.pdflatex_use_docker):
        set_pdflatex_use_docker(args.pdflatex_use_docker)

    if (args.pdflatex_bin_path is not None):
        set_pdflatex_bin_path(args.pdflatex_bin_path)

    return args
