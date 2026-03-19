"""
Parse a single quiz and output the results of the parse.
"""

import argparse
import os
import random
import sys

import quizcomp.cli.parser
import quizcomp.converter.convert
import quizcomp.constants
import quizcomp.quiz

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    seed = args.seed
    if (seed is None):
        seed = random.randint(0, 2**64)

    quiz = quizcomp.quiz.Quiz.from_path(args.path, flatten_groups = args.flatten_groups)
    variant = quiz.create_variant(all_questions = args.flatten_groups, seed = seed)  # pylint: disable=no-member
    content = quizcomp.converter.convert.convert_variant(variant, format = args.format,
            constructor_args = {'answer_key': args.answer_key})

    print(content)

    return 0

def main() -> int:
    """ Get a parser, parse the args, and call run. """

    return run_cli(_get_parser().parse_args())

def _get_parser() -> argparse.ArgumentParser:
    """ Get the parser. """

    parser = quizcomp.cli.parser.get_parser(__doc__.strip(),
        include_katex = True,
    )

    parser.add_argument('path', metavar = 'PATH',
        type = str,
        help = 'The path to a quiz json file.')

    parser.add_argument('--format',
        action = 'store', type = str, default = quizcomp.constants.FORMAT_JSON,
        choices = quizcomp.converter.convert.SUPPORTED_FORMATS,
        help = 'Output the parsed document in this format (default: %(default)s).')

    parser.add_argument('--key', dest = 'answer_key',
        action = 'store_true', default = False,
        help = 'Generate an answer key instead of a blank quiz (default: %(default)s).')

    parser.add_argument('--flatten-groups', dest = 'flatten_groups',
        action = 'store_true', default = False,
        help = 'Flatten question groups with multiple questions to multiple groups with a single question (default: %(default)s).')

    parser.add_argument('--seed', dest = 'seed',
        action = 'store', type = int, default = None,
        help = 'The random seed to use (defaults to a random seed).')

    return parser

if (__name__ == '__main__'):
    sys.exit(main())
