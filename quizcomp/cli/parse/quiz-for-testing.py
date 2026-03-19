# pylint: disable=invalid-name

"""
Parse a quiz for the purposes of testing.
The quiz will be parsed one and content will be generated for (but not output)
for each of the specified format (or none if none are specified).
"""

import argparse
import os
import random
import sys

import quizcomp.cli.parser
import quizcomp.converter.convert
import quizcomp.quiz

def run_cli(args: argparse.Namespace) -> int:
    """ Run the CLI. """

    if (not os.path.exists(args.path)):
        raise ValueError(f"Provided path '{args.path}' does not exist.")

    if (not os.path.isfile(args.path)):
        raise ValueError(f"Provided path '{args.path}' is not a file.")

    for quiz_format in args.formats:
        if (quiz_format not in quizcomp.converter.convert.SUPPORTED_FORMATS):
            raise ValueError("Unknown quiz format '%s', must be one of: [%s]." % (quiz_format, ', '.join(quizcomp.converter.convert.SUPPORTED_FORMATS)))

    seed = args.seed
    if (seed is None):
        seed = random.randint(0, 2**64)

    print("Parsing quiz: '%s'." % (args.path))

    quiz = quizcomp.quiz.Quiz.from_path(args.path, flatten_groups = args.flatten_groups)
    variant = quiz.create_variant(all_questions = args.flatten_groups, seed = seed)

    for quiz_format in args.formats:
        print("Generating quiz content for '%s'." % (quiz_format))
        quizcomp.converter.convert.convert_variant(variant, format = quiz_format,
                constructor_args = {'answer_key': args.answer_key})

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

    parser.add_argument('formats', metavar = 'FORMAT',
        type = str, nargs = '*',
        help = 'Generate (but do not output) content in this format.')

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
