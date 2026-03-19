"""
Customize an argument parser for the Quiz Composer.
"""

import argparse
import os
import typing

import edq.core.argparser

import quizcomp
import quizcomp.katex
import quizcomp.latex

CONFIG_FILENAME: str = 'edq-quiz-composer.json'

def get_parser(description: str,
        include_net: bool = False,
        include_katex: bool = False,
        include_latex: bool = False,
        ) -> argparse.ArgumentParser:
    """
    Get an argument parser specialized for the Quiz Composer.
    """

    config_options = {
        'config_filename': CONFIG_FILENAME,
    }

    parser = edq.core.argparser.get_default_parser(
            description,
            version = f"v{quizcomp.__version__}",
            include_net = include_net,
            config_options = config_options,
    )

    if (include_katex):
        parser.register_callbacks('katex', quizcomp.katex.set_cli_args, quizcomp.katex.init_from_args)

    if (include_latex):
        parser.register_callbacks('latex', quizcomp.latex.set_cli_args, quizcomp.latex.init_from_args)

    return typing.cast(argparse.ArgumentParser, parser)

def add_out_arg(
        parser: argparse.ArgumentParser,
        default_filename: str,
        name: str = 'out',
        dest: str = 'out',
        default: str = '.',
        ) -> None:
    """
    Add a standard output path argument to an argparse parser.
    Sibling to resolve_out_arg().
    """

    parser.add_argument(f'--{name}', dest = dest,
        action = 'store', type = str, default = default,
        help = ('The path specifying where to put the output.'
                + f' If the path points to an existing dir, the result will be written to `<{name}>/{default_filename}`.'
                + ' If the path point to an existing file, the file will be overwritten with the result.'
                + ' If the path points to a non-existing dir (denoted with a trailing path separator (e.g., slash)),'
                + ' the dir will be created and the output will be written as it is to an existing dir.'
                + ' Finally if the path does not exist, the result will be written to the full path (creating any parent directories along the way).'
                + ' (default: %(default)s).'))

def resolve_out_arg(raw_path: str, default_filename: str) -> str:
    """
    Resolve the out argument with the semantics of add_out_arg(),
    and return a resolved normalized path.
    """

    path = os.path.abspath(raw_path)

    if (os.path.isfile(path)):
        return path
    elif (os.path.isdir(path)):
        return os.path.join(path, default_filename)
    elif (raw_path.endswith(os.sep)):
        os.makedirs(path, exist_ok = True)
        return os.path.join(path, default_filename)
    else:
        os.makedirs(os.path.dirname(path), exist_ok = True)
        return path
